"""Local HTTP bridge for the Ethiopian translator pipeline.

Run from the repository root with:
    $env:PYTHONUTF8=1; uvicorn server:app --host 127.0.0.1 --port 8000
"""

import os
os.environ["MKL_DISABLE_FAST_MM"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
from contextlib import asynccontextmanager
from pathlib import Path
import sys
import tempfile
import time

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

# Rich emits status symbols during model loading; keep Windows subprocesses UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import LANGUAGES, TranslatorPipeline


class TextTranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)
    src: str
    tgt: str
    session_id: str | None = None
    formality: str = "auto"


class QuickReply(BaseModel):
    text: str
    translation: str


class TranslationResponse(BaseModel):
    source_text: str
    translated_text: str
    src_lang: str
    tgt_lang: str
    latency_seconds: float
    intent: str = "general_conversation"
    formality: str = "auto"
    suggested_replies: list[QuickReply] = []


def _validate_language_pair(src: str, tgt: str) -> None:
    if src not in LANGUAGES or tgt not in LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported language code",
                "supported": sorted(LANGUAGES),
            },
        )
    if src == tgt:
        raise HTTPException(status_code=400, detail="Source and target languages must differ")


@asynccontextmanager
async def lifespan(application: FastAPI):
    whisper_size = os.getenv("WHISPER_SIZE", "tiny")
    pipeline = TranslatorPipeline(whisper_size=whisper_size)
    application.state.pipeline = pipeline
    pipeline.load_all()
    yield
    application.state.pipeline = None


app = FastAPI(
    title="Ethiopian Translator API",
    version="0.1.0",
    description="Offline translation bridge for the Flutter client.",
    lifespan=lifespan,
)


def get_pipeline() -> TranslatorPipeline:
    pipeline = getattr(app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Translation models are still loading")
    return pipeline


@app.get("/health")
async def health() -> dict[str, str | bool]:
    ready = getattr(app.state, "pipeline", None) is not None
    return {"status": "ok" if ready else "loading", "ready": ready}


@app.get("/languages")
async def languages() -> dict[str, dict[str, str | None]]:
    return {
        key: {
            "name": value["name"],
            "native": value["native"],
            "flag": value["flag"],
        }
        for key, value in LANGUAGES.items()
    }




@app.post("/translate/text", response_model=TranslationResponse)
async def translate_text(request: TextTranslationRequest) -> TranslationResponse:
    _validate_language_pair(request.src, request.tgt)
    started = time.perf_counter()
    smart_res = get_pipeline().translate_text_smart(
        request.text.strip(),
        request.src,
        request.tgt,
        session_id=request.session_id,
        formality=request.formality,
    )
    dt = round(time.perf_counter() - started, 3)
    print(f"[TEXT] {request.src} -> {request.tgt} ({dt}s) [{smart_res['intent']}]: '{request.text}' => '{smart_res['translated_text']}'")
    return TranslationResponse(
        source_text=smart_res["source_text"],
        translated_text=smart_res["translated_text"],
        src_lang=request.src,
        tgt_lang=request.tgt,
        latency_seconds=dt,
        intent=smart_res["intent"],
        formality=smart_res["formality"],
        suggested_replies=[QuickReply(**r) for r in smart_res.get("suggested_replies", [])],
    )


@app.post("/translate/audio", response_model=TranslationResponse)
async def translate_audio(
    file: UploadFile = File(...),
    src: str = Query(...),
    tgt: str = Query(...),
    session_id: str | None = Query(default=None),
    formality: str = Query(default="auto"),
) -> TranslationResponse:
    _validate_language_pair(src, tgt)
    if file.content_type and file.content_type not in {
        "application/octet-stream",
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
    } and not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="Upload a WAV or other audio file")

    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            temporary_path = temporary_file.name
            while chunk := await file.read(1024 * 1024):
                temporary_file.write(chunk)

        started = time.perf_counter()
        result = get_pipeline().translate_audio(
            temporary_path,
            src,
            tgt,
            speak_result=False,
            session_id=session_id,
            formality=formality,
        )
        dt = round(time.perf_counter() - started, 3)
        effective_src = result.get("src_lang", src)
        effective_tgt = result.get("tgt_lang", tgt)
        print(f"[AUDIO] {effective_src} -> {effective_tgt} ({dt}s) [{result.get('intent')}]: '{result['source_text']}' => '{result['translated_text']}'")
        return TranslationResponse(
            source_text=result["source_text"],
            translated_text=result["translated_text"],
            src_lang=effective_src,
            tgt_lang=effective_tgt,
            latency_seconds=dt,
            intent=result.get("intent", "general_conversation"),
            formality=result.get("formality", "auto"),
            suggested_replies=[QuickReply(**r) for r in result.get("suggested_replies", [])],
        )
    finally:
        await file.close()
        if temporary_path:
            os.unlink(temporary_path)
