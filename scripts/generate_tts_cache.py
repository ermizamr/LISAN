import os
import sys
import hashlib
import json
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Import corpora from generate_dart_tm
from scripts.generate_dart_tm import CLINIC_CORPUS, ROAD_CORPUS, CAFE_CORPUS, MARKET_CORPUS
from ai_pipeline.pipeline import MMSTTSEngine

def text_hash(lang: str, text: str) -> str:
    cleaned = text.strip()
    return f"{lang}_{hashlib.md5(cleaned.encode('utf-8')).hexdigest()[:10]}"

def main():
    out_dir = ROOT_DIR / "output_tts" / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_corpora = CLINIC_CORPUS + ROAD_CORPUS + CAFE_CORPUS + MARKET_CORPUS
    
    unique_items = {}
    for item in all_corpora:
        for lang in ['amh', 'orm', 'tir', 'som', 'eng']:
            if lang in item:
                text = item[lang].strip()
                h = text_hash(lang, text)
                unique_items[h] = (lang, text)

    # Core user greetings and medical conversational phrases
    additional_phrases = [
        ('amh', 'ሰላም፣ እንዴት ነህ? ደህና ነህ?'),
        ('amh', 'ሰላም እንዴት ነህ ደህና ነህ?'),
        ('amh', 'ደህና ነኝ፣ አንተስ?'),
        ('amh', 'እኔ ደህና ነኝ አንተ ደህና ነህ?'),
        ('amh', 'ምንህን ነው የሚያምህ?'),
        ('amh', 'መድሃኒት አዝልሃለው'),
        ('amh', 'እንደምን አደርክ?'),
        ('amh', 'እንደምን ዋልክ?'),
        ('amh', 'እንኳን ደህና መጣህ'),
        ('amh', 'አመሰግናለሁ'),
        ('amh', 'ይቅርታ'),
        ('amh', 'ስምህ ማን ይባላል?'),
        ('amh', 'እባክዎ ይድገሙልኝ'),
        ('amh', 'አዎ'),
        ('amh', 'አይደለም'),
        
        ('orm', 'Akkam, akkam jirta? Nagaa qabdaa?'),
        ('orm', 'Akkam jirta, nagaa qabdaa?'),
        ('orm', 'Ani nagaadha, ati hoo nagaadhaa?'),
        ('orm', 'Maaltu si dhibe?'),
        ('orm', 'Qoricha siif barreessa'),
        ('orm', 'Akkam bulte?'),
        ('orm', 'Akkam oolte?'),
        ('orm', 'Baga nagaan dhufte'),
        ('orm', 'Galatoomi'),
        ('orm', 'Dhiifama'),
        ('orm', 'Maqaan kee eenyu?'),
        ('orm', 'Maaloo naaf irra deebi\'i'),
        ('orm', 'Eeyyee'),
        ('orm', 'Miti'),
        
        ('tir', 'ሰላም፡ ከመይ ኣለኻ? ድሓን ዲኻ?'),
        ('tir', 'ሰላም ከመይ ኣለኻ፡ ድሓን ዲኻ?'),
        ('tir', 'ኣነ ድሓን እየ፡ ንስኻኸ ድሓን ዲኻ?'),
        ('tir', 'ምንኻ እዩ ዝሕምመካ?'),
        ('tir', 'መድሃኒት ክጽሕፈልካ እየ'),
        ('tir', 'ከመይ ሓዲርካ?'),
        ('tir', 'ከመይ ውዒልካ?'),
        ('tir', 'እንቋዕ ብደሓን መጻእካ'),
        ('tir', 'የቐንየለይ'),
        ('tir', 'ይቕሬታ'),
        ('tir', 'ስምካ መን ይበሃል?'),
        ('tir', 'ብኽብረትካ ድገመለይ'),
        ('tir', 'እወ'),
        ('tir', 'ኣይኮነን'),
        
        ('som', 'Nabad, sidee tahay? Ma fiican tahay?'),
        ('som', 'Sidee tahay, ma fiican tahay?'),
        ('som', 'Anigu waan fiicanahay, adiguna ma fiican tahay?'),
        ('som', 'Maxaa ku xanuunaya?'),
        ('som', 'Dawo ayaan kuu qorayaa'),
        ('som', 'Subax wanaagsan'),
        ('som', 'Galab wanaagsan'),
        ('som', 'Soo dhowow'),
        ('som', 'Mahadsanid'),
        ('som', 'Waan ka xumahay'),
        ('som', 'Magacaa?'),
        ('som', 'Fadlan ii soo celi'),
        ('som', 'Haa'),
        ('som', 'Maya'),
        
        ('eng', 'Hello, how are you? Are you doing well?'),
        ('eng', 'I am fine, and you?'),
        ('eng', 'I am doing well, thank you.'),
        ('eng', 'Where does it hurt?'),
        ('eng', 'I will prescribe medicine for you.'),
        ('eng', 'Good morning'),
        ('eng', 'Good afternoon'),
        ('eng', 'Welcome'),
        ('eng', 'Thank you very much'),
        ('eng', 'Excuse me'),
        ('eng', 'What is your name?'),
        ('eng', 'Please repeat that for me'),
        ('eng', 'Yes'),
        ('eng', 'No'),
    ]

    for lang, text in additional_phrases:
        h = text_hash(lang, text)
        unique_items[h] = (lang, text)

    print(f"Total unique utterances to synthesize: {len(unique_items)}")

    # Group by language to load models sequentially
    by_lang = {}
    for h, (lang, text) in unique_items.items():
        by_lang.setdefault(lang, []).append((h, text))

    engine = MMSTTSEngine()
    index_manifest = {}

    total_synthesized = 0
    total_cached = 0

    for lang in ['amh', 'orm', 'tir', 'som', 'eng']:
        items = by_lang.get(lang, [])
        print(f"\nProcessing {len(items)} items for language '{lang}'...")
        
        # Load model for this language
        engine._get_model_and_tokenizer(lang)

        for i, (h, text) in enumerate(items):
            target_path = out_dir / f"{h}.wav"
            index_manifest[h] = {
                "lang": lang,
                "text": text,
                "file": f"{h}.wav"
            }
            if target_path.exists() and target_path.stat().st_size > 1000:
                total_cached += 1
                continue

            try:
                t0 = time.time()
                wav_bytes = engine.synthesize_to_bytes(text, lang)
                if len(wav_bytes) > 500:
                    with open(target_path, "wb") as f:
                        f.write(wav_bytes)
                    total_synthesized += 1
                    dt = time.time() - t0
                    print(f"  [{lang} {i+1}/{len(items)}] Synthesized '{text[:30]}' ({len(wav_bytes)//1024} KB, {dt:.2f}s)")
                else:
                    print(f"  [{lang} {i+1}/{len(items)}] WARNING: Empty audio for '{text}'")
            except Exception as e:
                print(f"  [{lang} {i+1}/{len(items)}] Error synthesizing '{text}': {e}")

    # Save manifest
    manifest_path = out_dir / "index.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(index_manifest, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Complete! Synthesized: {total_synthesized}, Already Cached: {total_cached}")
    print(f"✓ Manifest saved to {manifest_path}")

if __name__ == '__main__':
    main()
