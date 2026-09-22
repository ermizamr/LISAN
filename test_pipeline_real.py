import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline

pipeline = TranslatorPipeline()
pipeline.load_all()

# Intentionally test mismatched and matched requests
tests = [
    # 1. User spoke Amharic, app requested eng -> amh (mismatched!)
    ("real_test1.wav", "eng", "amh", "User spoke 'ሰላም' with wrong app direction"),
    # 2. User spoke Amharic (Salam), app requested amh -> eng (matched)
    ("real_test2.wav", "amh", "eng", "User spoke 'ሳላም'"),
    # 3. User spoke Amharic (Long sentence with laughter), app requested amh -> eng (matched)
    ("real_test3.wav", "amh", "eng", "User spoke visited Ethiopia with haha"),
    # 4. User spoke Amharic (Mettaqaleh), app requested amh -> eng (matched)
    ("real_test4.wav", "amh", "eng", "User spoke Mettaqaleh"),
    # 5. User spoke English, app requested amh -> eng (mismatched!)
    ("real_test5.wav", "amh", "eng", "User spoke English paragraph with wrong app direction"),
]

print("=" * 80)
for fname, req_src, req_tgt, desc in tests:
    print(f"\n>>> Running {fname} ({desc}) | Requested: {req_src} -> {req_tgt}")
    res = pipeline.translate_audio(fname, req_src, req_tgt, speak_result=False)
    print(f"  Effective direction: {res['src_lang']} -> {res['tgt_lang']}")
    print(f"  Source text:         '{res['source_text']}'")
    print(f"  Translated text:     '{res['translated_text']}'")
    latency = res.get('latency_seconds', res.get('total_latency', 0.0))
    print(f"  Total latency:       {latency:.2f}s")
print("=" * 80)
