"""Deep stress testing script to uncover flaws, hallucinations, and failure modes

in the raw NLLB-200 neural translation model across Ethiopian languages.
"""

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline, LANGUAGES

def test_flaws():
    p = TranslatorPipeline()
    p.translator.load()

    categories = {
        "1. NEGATION & POLARITY INVERSION (High Clinical Risk)": [
            ("eng", "amh", "Do NOT take this medicine with alcohol.", "ይህንን መድሃኒት ከአልኮል ጋር በፍጹም አይውሰዱ።"),
            ("eng", "orm", "Do NOT drink unboiled water.", "Bishaan hin danfine hin dhuginaa."),
            ("eng", "tir", "Do NOT stop taking the antibiotics early.", "ነቲ አንቲባዮቲክስ ቀዲምኩም ደው ኣይተብልዎ።"),
            ("amh", "eng", "ምንም አይነት ህመም አይሰማኝም።", "I do not feel any pain at all."),
            ("orm", "eng", "Dawaa kana nyaata malee hin fudhatin.", "Do not take this medicine without food."),
            ("tir", "eng", "ናብ ሆስፒታል ምኻድ ኣይደልን እየ።", "I do not want to go to the hospital."),
        ],
        "2. CULTURAL IDIOMS & FIGURATIVE EXPRESSIONS": [
            ("amh", "eng", "ዜናውን ስሰማ ሆዴ ባባ።", "When I heard the news, I was deeply moved to tears."),
            ("amh", "eng", "ፖሊሶቹን ሳያቸው እግር አውጣ ብዬ ሮጥኩ።", "When I saw the police, I ran as fast as my legs could carry me."),
            ("amh", "eng", "በቁም ነገር ነው የማናግርህ፣ አትቀልድ።", "I am speaking to you seriously, do not joke."),
            ("amh", "eng", "ስራ ፈትቼ ቤት ነው የተቀመጥኩት።", "I am unemployed and sitting at home."),
            ("orm", "eng", "Lafti natti maraa jira, dhaabachuu hin dandeenye.", "The room is spinning / I feel dizzy, I cannot stand."),
            ("orm", "eng", "Waan hundumaa harka lafa jalaan hojjatan.", "They did everything under the table / corruptly."),
            ("tir", "eng", "ነገሩ ምስ ሰማዕኩ ልበይ ዓሪፉ።", "When I heard the matter, my heart found peace / I was relieved."),
            ("som", "eng", "Hadalkaagu calooshayda buu galay.", "Your words touched my heart deeply."),
        ],
        "3. COMPLEX CLINICAL & EMERGENCY TRIAGE": [
            ("eng", "amh", "The patient has acute shortness of breath when lying flat.", "በሽተኛው ጋደም ሲል ከፍተኛ የትንፋሽ ማጠር አለበት።"),
            ("eng", "amh", "Are you experiencing any vaginal bleeding or contractions?", "የደም መፍሰስ ወይም የምጥ ስሜት ይሰማዎታል?"),
            ("eng", "orm", "He had an epileptic seizure, bit his tongue, and lost consciousness.", "Inni dhibee gaggabdoo qabaatee, arraba isaa ciniinee, of wallaale."),
            ("eng", "tir", "Are you allergic to penicillin or any other antibiotics?", "ንፔኒሲሊን ወይስ ንኻልእ ፀረ-ተህዋስያን ኣለርጂ ኣለኩም ዶ?"),
            ("amh", "eng", "የስኳር ህመም እና ከፍተኛ የደም ግፊት አለብኝ።", "I have diabetes and high blood pressure."),
            ("orm", "eng", "Harmi koo na dhiita'ee dhukkubbii cimaa qaba.", "My breast is swollen and has severe pain."),
        ],
        "4. ETHIOPIAN GEOGRAPHY & PROPER NOUN PRESERVATION": [
            ("eng", "amh", "The historic churches of Lalibela were carved from solid rock.", "ታሪካዊዎቹ የላሊበላ አብያተ ክርስቲያናት ከተሰነጠቀ አለት ተፈልፍለው የተሰሩ ናቸው።"),
            ("eng", "orm", "We took a boat ride on Lake Tana near Bahir Dar.", "Haroo Xaanaa cinaa Baahir Daaritti doonii yaabbannee turre."),
            ("eng", "tir", "The ancient obelisks of Axum are over two thousand years old.", "ጥንታውያን ሓወልትታት ኣኽሱም ልዕሊ ክልተ ሽሕ ዓመት ዝዕድሚኦም እዮም።"),
            ("amh", "orm", "ወደ ጎንደር እና ደብረ ታቦር የሚወስደው አውራ ጎዳና ተዘግቷል።", "Daandiin gara Gondarii fi Dabra Taabor geessu cufameera."),
            ("amh", "eng", "አቶ አበበ እና ወይዘሮ አልማዝ አዲስ አበባ ውስጥ ነው የሚኖሩት።", "Ato Abebe and Woizero Almaz live in Addis Ababa."),
        ],
        "5. NUMBERS, DOSAGES & CURRENCY PRECISION": [
            ("eng", "amh", "Inject 15 units of insulin subcutaneous before dinner.", "ከእራት በፊት 15 ዩኒት ኢንሱሊን በቆዳ ስር ውጉ።"),
            ("eng", "orm", "The price is 4,500 Birr per quintal.", "Gatiin kun kintaala tokkotti Birrii 4,500 dha."),
            ("amh", "eng", "በቀን ሶስት ጊዜ ሁለት ሁለት ኪኒን ለሰባት ቀናት ውሰዱ።", "Take two pills three times a day for seven days."),
            ("tir", "eng", "ናይዚ መድሃኒት ዋጋ 750 ቅርሺ እዩ።", "The price of this medicine is 750 Birr."),
        ],
        "6. SHORT ONE-WORD DIRECTIVES & AMBIGUOUS TERMS": [
            ("eng", "amh", "Breathe!", "ተንፍስ!"),
            ("eng", "amh", "Push!", "ግፋ! / አምጥ!"),
            ("eng", "orm", "Stop!", "Dhaabadhu!"),
            ("eng", "tir", "Wait!", "ተጸበ!"),
            ("amh", "eng", "በቃ!", "Enough! / That's all!"),
            ("orm", "eng", "Tole!", "Okay! / Agreed!"),
        ],
        "7. CODE-SWITCHING & MIXED BORROWED PHRASING": [
            ("amh", "eng", "ዶክተሩ በካርድ ፋይል ውስጥ ሪፈራል ጽፎልኛል።", "The doctor wrote me a referral in the card file."),
            ("orm", "eng", "Kilaasii keessatti kompiitara dhabnee qormaata online hin qoranne.", "We lacked computers in class and did not take the online exam."),
            ("eng", "amh", "Check the ICU monitor and call the lab for blood results.", "የአይ ሲ ዩ ሞኒተሩን ይመልከቱ እና የደም ምርመራ ውጤቱን ከላብራቶሪ ይጠይቁ።"),
        ]
    }

    print("\n" + "=" * 90)
    print("LISAN NMT FLAW-DETECTION & STRESS TEST BENCHMARK")
    print("Model: facebook/nllb-200-distilled-600M (CTranslate2 INT8, No Fallback/Glossary)")
    print("=" * 90 + "\n")

    total_tests = 0
    flaws_found = []

    for category, test_cases in categories.items():
        print(f"\n>>> CATEGORY: {category}")
        print("-" * 90)
        for src, tgt, text, ref in test_cases:
            total_tests += 1
            src_nllb = LANGUAGES[src]["nllb_code"]
            tgt_nllb = LANGUAGES[tgt]["nllb_code"]
            
            t0 = time.perf_counter()
            out = p.translator.translate(text, src_nllb, tgt_nllb)
            lat_ms = (time.perf_counter() - t0) * 1000

            print(f"[{src.upper()} -> {tgt.upper()}] ({lat_ms:.0f}ms)")
            print(f"  Input:     {text}")
            print(f"  NLLB Raw:  {out}")
            print(f"  Reference: {ref}")
            print()

    print("=" * 90)
    print(f"Completed deep flaw scan across {total_tests} adversarial test cases.")
    print("=" * 90)

if __name__ == "__main__":
    test_flaws()
