"""Comprehensive evaluation of raw NLLB-200 translation capabilities.

Tests raw neural translation across all 5 languages without glossary/TM shortcuts
to assess genuine translation fidelity, fluency, and limitations.
"""

import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline, LANGUAGES

def run_evaluation():
    p = TranslatorPipeline()
    p.translator.load()

    test_suite = [
        # 1. Medical & Emergency (High stakes)
        ("eng", "amh", "I have had severe chest pain and fever for two days.", "የሁለት ቀን ከባድ የደረት ህመም እና ትኩሳት አለብኝ።"),
        ("amh", "eng", "ሆስፒታሉ የት እንደሆነ እና ድንገተኛ ክፍል መኖሩን ልትነግሩኝ ትችላላችሁ?", "Can you tell me where the hospital is and if there is an emergency room?"),
        ("eng", "orm", "Take this medicine twice a day after meals.", "Qoricha kana guyyaatti yeroo lama nyaata booda fudhadhu."),
        ("orm", "eng", "Mataan koo baay'ee na dhukkuba, akkasumas lafti natti marti.", "My head hurts very much, and I feel dizzy."),
        ("eng", "tir", "Please call an ambulance immediately.", "በጃኹም ብቕልጡፍ ኣምቡላንስ ጸውዑ።"),
        ("tir", "eng", "ኣብዚ ቀረባ ዝርከብ ፋርማሲ ኣበይ ኣሎ?", "Where is the nearest pharmacy around here?"),
        ("eng", "som", "He needs urgent blood transfusion at the hospital.", "Wuxuu isbitaalka ugu baahan yahay dhiig shubid degdeg ah."),
        ("som", "eng", "Calooshayda aad bay ii xanuunaysaa ilaa xalay.", "My stomach has been hurting badly since last night."),

        # 2. Commerce & Navigation (Daily utility)
        ("eng", "amh", "How much does a kilogram of teff cost in this market?", "በዚህ ገበያ የአንድ ኪሎ ጤፍ ዋጋ ስንት ነው?"),
        ("amh", "eng", "ወደ አዲስ አበባ የሚሄደው አውቶቡስ ስንት ሰዓት ይነሳል?", "What time does the bus to Addis Ababa leave?"),
        ("eng", "orm", "Turn left at the next crossroads and go straight ahead.", "Muka qaxxaamuraa itti aanutti gara bitaatti goriitii qajeeli."),
        ("orm", "amh", "Gatiin buna kanaa meeqa? Garmalee qaaliidha.", "የዚህ ቡና ዋጋ ስንት ነው? በጣም ውድ ነው።"),

        # 3. Direct Ethiopian-to-Ethiopian (Cross-regional without English pivot)
        ("amh", "orm", "ነገ ጠዋት ወደ ባህር ዳር መሄድ እፈልጋለሁ።", "Boru ganama gara Baahir Daar deemuun barbaada."),
        ("orm", "amh", "Baga nagaan dhuftan, maatii fi firoonni akkam jiru?", "እንኳን ደህና መጣችሁ፣ ቤተሰብና ዘመዶች እንዴት ናቸው?"),
        ("amh", "tir", "እባክዎን መንገዱን ሊያሳዩኝ ይችላሉ?", "በጃኹም መገዲ ክተርእዩኒ ትኽእሉ ዶ?"),
        ("tir", "amh", "ሰላም ከመይ ኣለኻ፡ ኣብዚ ዓዲ ሓድሽ ድየ?", "ሰላም እንዴት ነህ፡ በዚህ አገር አዲስ ነኝ?"),
        ("amh", "som", "ውሃ መጠጣት እፈልጋለሁ፣ እባክዎን ውሃ አምጡልኝ።", "Waxaan rabaa inaan biyo cabbo, fadlan biyo ii keen."),
        ("som", "amh", "Maanta aad bay u kulushahay halkan.", "ዛሬ እዚህ በጣም ይሞቃል።"),

        # 4. Complex multi-clause & conversational nuance
        ("eng", "amh", "Although it was raining heavily yesterday, we managed to arrive before the conference started.", "ትናንት ከባድ ዝናብ እየዘነበ ቢሆንም፣ ጉባኤው ከመጀመሩ በፊት መድረስ ችለናል።"),
        ("amh", "eng", "ስራዬን ከጨረስኩ በኋላ ወደ ቤት ሄጄ ከልጆቼ ጋር አሳልፋለሁ።", "After finishing my work, I will go home and spend time with my children."),
        ("eng", "orm", "If you don't understand the question, please ask the teacher to explain it again.", "Yoo gaafficha hin hubanne, barsiisaan akka deebisee ibsu gaafadhu."),
    ]

    print("\n" + "=" * 80)
    print("LISAN RAW NMT NEURAL ASSESSMENT BENCHMARK")
    print("Testing CTranslate2 INT8 NLLB-200 (No Glossary / No Hardcoded TM)")
    print("=" * 80 + "\n")

    latencies = []
    results = []

    for idx, (src, tgt, input_text, reference) in enumerate(test_suite, 1):
        src_nllb = LANGUAGES[src]["nllb_code"]
        tgt_nllb = LANGUAGES[tgt]["nllb_code"]

        t0 = time.perf_counter()
        raw_output = p.translator.translate(input_text, src_nllb, tgt_nllb)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

        print(f"[{idx:02d}] {src.upper()} -> {tgt.upper()} ({elapsed_ms:.1f}ms)")
        print(f"  Input:     {input_text}")
        print(f"  NLLB Raw:  {raw_output}")
        print(f"  Reference: {reference}")
        print("-" * 80)

    avg_latency = sum(latencies) / len(latencies)
    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(test_suite)} sentences evaluated.")
    print(f"Average Latency: {avg_latency:.1f} ms per sentence ({avg_latency/1000:.2f}s)")
    print(f"Min Latency:     {min(latencies):.1f} ms")
    print(f"Max Latency:     {max(latencies):.1f} ms")
    print("=" * 80)

if __name__ == "__main__":
    run_evaluation()
