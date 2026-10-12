"""
Seed Demo Scenarios into LISAN Translation Memory & Audio Cache
==============================================================
Scenarios:
1. Rural Clinic Triage (Amharic <-> Afaan Oromoo)
2. Tourist in Ancient Axum (English <-> Tigrinya & Amharic)
"""

import sys
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai_pipeline.translation_memory import TranslationMemory, normalize_for_indexing
from ai_pipeline.pipeline import MMSTTSEngine

RURAL_CLINIC_DIALOGUE = [
    # Turn 1: Doctor welcomes patient
    {
        "domain": "rural_clinic",
        "amh": "እንደምን ዋልክ አባቴ፣ ዛሬ ምንህን ነው የሚያምህ?",
        "orm": "Akkam oolte abbaa koo, har'a maaltu si dhibe?",
        "eng": "Good day father, where are you feeling pain today?",
        "tir": "ደሓንዶ ውዒልካ ኣቦይ፡ ሎሚ እንታይ እዩ ዘሕምመካ ዘሎ?",
    },
    # Turn 2: Patient describes fever and head pain
    {
        "domain": "rural_clinic",
        "amh": "ጤና ይስጥልኝ ዶክተር። ለሦስት ቀናት ራሴን ያመኛል፣ እንዲሁም ከፍተኛ ትኩሳት ይዞኛል።",
        "orm": "Baga nagaan jirtu doktoor. Guyyaa sadiif mataan na dhukkuba, akkasumas ho'i guddaan na qabeera.",
        "eng": "Hello doctor. I have had a severe headache and high fever for three days.",
        "tir": "ሰላም ዶክተር። ንሰለስተ መዓልታት ርእሰይ የሕምመኒ ኣሎ፡ ከምኡ'ውን ሓያል ረስኒ ሒዙኒ ኣሎ።",
    },
    # Turn 3: Doctor probes chills and nausea
    {
        "domain": "rural_clinic",
        "amh": "ብርድ ብርድ ማለት፣ ማቅለሽለሽ ወይም ሳል አለብህ?",
        "orm": "Dhaamochi, balaqqamsi ykn qufaan sitti jiraa?",
        "eng": "Do you have chills, nausea, or a cough?",
        "tir": "ቁሪ ቁሪ ምባል፡ ተምላስ ወይ ሰዓል ኣለካ ድዩ?",
    },
    # Turn 4: Patient describes evening chills
    {
        "domain": "rural_clinic",
        "amh": "ሳል የለም፣ ነገር ግን ማታ ማታ ብርቱ ብርድ ይይዘኛል፣ ሰውነቴም ይንቀጠቀጣል።",
        "orm": "Qufaan hin jiru, garuu galgala galgala qorri guddaan na qaba, qaamni koos ni hollata.",
        "eng": "No cough, but at night I get intense chills and my body shivers.",
        "tir": "ሰዓል የለን፡ ግና ምሸት ምሸት ሓያል ቁሪ ይሕዘኒ፡ ሰብነተይ'ውን ይንቀጥቀጥ።",
    },
    # Turn 5: Doctor orders rapid malaria test
    {
        "domain": "rural_clinic",
        "amh": "የወባ በሽታ መኖሩን ለማረጋገጥ አሁን ፈጣን የጣት ደም ምርመራ እናደርጋለን።",
        "orm": "Busaadhaa fi dhibee biraa mirkaneeffachuuf amma qorannoo dhiigaa ariifachiisaa siif goona.",
        "eng": "We will now do a rapid finger-prick blood test to check for malaria.",
        "tir": "ናይ ዓሶ ሕማም ምህላዉ ንምርግጋጽ ሕጂ ቅልጡፍ ናይ ኣጻብዕቲ ደም መርመራ ክንገብረልካ ኢና።",
    },
    # Turn 6: Doctor explains diagnosis
    {
        "domain": "rural_clinic",
        "amh": "የምርመራው ውጤት መጥቷል፤ ሳንባህ ጤነኛ ነው፣ ነገር ግን ደምህ ውስጥ ወባ ተገኝቷል።",
        "orm": "Firiin qorannoo dhufeera; sombi kee nagaadha, garuu dhiiga kee keessatti busaan argameera.",
        "eng": "The test results are here; your lungs are healthy, but malaria was found in your blood.",
        "tir": "ውጽኢት መርመራ መጺኡ ኣሎ፤ ሳንቡእካ ጥዑይ እዩ፡ ግና ኣብ ደምካ ዓሶ ተረኺቡ ኣሎ።",
    },
    # Turn 7: Doctor prescribes medication
    {
        "domain": "rural_clinic",
        "amh": "ይህንን የወባ መድሃኒት ለሦስት ቀናት ከምግብ በኋላ በቀን ሁለት ጊዜ ውሰድ።",
        "orm": "Qoricha busaa kana guyyoota sadiif nyaata booda guyyaatti yeroo lama fudhadhu.",
        "eng": "Take this malaria medication twice daily after meals for three days.",
        "tir": "ነዚ ናይ ዓሶ መድሃኒት ንሰለስተ መዓልታት ድሕሪ ምግቢ ኣብ መዓልቲ ክልተ ግዜ ውሰዶ።",
    },
    # Turn 8: Patient asks about rest and water
    {
        "domain": "rural_clinic",
        "amh": "አመሰግናለሁ ዶክተር። የእርሻ ስራ ትቼ የፈላ ውሃ ብቻ መጠጣት አለብኝ?",
        "orm": "Galatoomi doktoor. Hojii maasii dhiisee bishaan danfe qofa dhuguun qabaa?",
        "eng": "Thank you doctor. Should I rest from farm work and only drink boiled water?",
        "tir": "የቐንየለይ ዶክተር። ስራሕ ሕርሻ ኣቋሪጸ ዝፈልሐ ማይ ጥራይ ድየ ክሰቲ ዘለኒ?",
    },
    # Turn 9: Doctor confirms fluids and rest
    {
        "domain": "rural_clinic",
        "amh": "አዎ፣ በደንብ እረፍት አድርግ፣ ብዙ ውሃ ጠጣ፣ ትኩሳቱ ካልቀነሰም ተመልሰህ ና።",
        "orm": "Eeyyee, sirriitti boqodhu, bishaan baay'ee dhugi, yoo ho'i hin hir'anne immoo deebi'ii kottu.",
        "eng": "Yes, rest well, drink plenty of water, and come back if the fever does not subside.",
        "tir": "እወ፡ ጽቡቕ ጌርካ ዕረፍቲ ግበር፡ ብዙሕ ማይ ስተ፡ ረስኒ እንተዘይጎዲሉ ድማ ተመሊስካ ንዓ።",
    },
    # Turn 10: Patient farewell blessing
    {
        "domain": "rural_clinic",
        "amh": "ጤና ይስጥልኝ ዶክተር፣ እግዚአብሔር ይህንን መድሃኒት ፈውስ ያድርገው።",
        "orm": "Fayyaa ta'aa doktoor, waaqayyo qoricha kana eebba haa godhu.",
        "eng": "Goodbye doctor, may God make this medicine a true healing.",
        "tir": "ደሓን ኩኑ ዶክተር፡ እግዚኣብሔር ነዚ መድሃኒት ፈውሲ ይግበሮ።",
    },
]

AXUM_TOURIST_DIALOGUE = [
    # Turn 1: Tourist marvels at obelisk
    {
        "domain": "axum_tourist",
        "eng": "Hello! This ancient granite obelisk is breathtaking. How old is it?",
        "tir": "ሰላም! እዚ ጥንታዊ ናይ ሓወልቲ ግራናይት ኣዝዩ ዘደንቕ እዩ። ዕድሚኡ ክንደይ ዓመት እዩ?",
        "amh": "ሰላም! ይህ ጥንታዊ የግራናይት ሀውልት እጅግ አስደናቂ ነው። ዕድሜው ስንት ዓመት ነው?",
        "orm": "Akkam! Siidaan giraanaayitii durii kun baay'ee nama dinqisiisa. Umuriin isaa waggaa meeqa?",
    },
    # Turn 2: Guide explains King Ezana
    {
        "domain": "axum_tourist",
        "eng": "Welcome to the ancient city of Axum. This obelisk was erected in the fourth century by King Ezana.",
        "tir": "እንቋዕ ብደሓን መጻእኪ ናብ ጥንታዊት ከተማ ኣክሱም። እዚ ሓወልቲ ኣብ ራብዓይ ክፍለ ዘመን ብንጉሥ ኢዛና እዩ ተሃኒጹ።",
        "amh": "እንኳን ወደ ጥንታዊቷ የአክሱም ከተማ በደህና መጣህ። ይህ ሀውልት በአራተኛው ክፍለ ዘመን በንጉሥ ኢዛና ነው የተተከለው።",
        "orm": "Baga nagaan gara magaalaa durii Aksum dhuftan. Siidaan kun jaarraa afraffaatti Mootii Eezaanaatiin dhaabame.",
    },
    # Turn 3: Tourist asks about transport
    {
        "domain": "axum_tourist",
        "eng": "It is carved from a single piece of stone! How did ancient engineers transport something so massive?",
        "tir": "ካብ ሓደ ዓቢ እምኒ ጥራይ ዝተቐርጸ እዩ! ጥንታውያን መሃንድሳት ከመይ ገይሮም እዮም ከምዚ ዝኣመሰለ ከቢድ እምኒ ኣጓዒዞምዎ?",
        "amh": "ከአንድ ድንጋይ ብቻ የተቀረጸ ነው! ጥንታዊያን መሐንዲሶች ይህን የመሰለ ግዙፍ ድንጋይ እንዴት አጓጓዙት?",
        "orm": "Dhagaa tokko qofa irraa bocame! Ogeeyyiin durii wanta ulfaataa akkanaa akkamitti geejjiban?",
    },
    # Turn 4: Guide explains engineering ramps
    {
        "domain": "axum_tourist",
        "eng": "They transported it from four kilometers away using elephants and massive wooden rollers along prepared ramps.",
        "tir": "ካብ ኣርባዕተ ኪሎ ሜትር ርሕቀት ብዝነበሩ ሓርማዛትን ገዘፍቲ ዕንጨይትን ተጠቒሞም ብዝተዳለወ ጐደና ኣንከራፊፎም እዮም ኣምጺኦምዎ።",
        "amh": "ከአራት ኪሎ ሜትር ርቀት በዝሆኖችና በትላልቅ የእንጨት ማንከባለያዎች በመጠቀም በተዘጋጁ መንገዶች ነው ያመጡት።",
        "orm": "Arbaa fi mukkeen gurguddoo maramanitti fayyadamuun kiilomeetira afur irraa daandii qophaa'e irraan fidan.",
    },
    # Turn 5: Tourist asks about trilingual tablet
    {
        "domain": "axum_tourist",
        "eng": "I also noticed the inscriptions nearby in Ge'ez, Sabaean, and Greek. Why three languages?",
        "tir": "ኣብ ጥቓኡ ዘለዉ ጽሑፋት ብግእዝ፡ ሳባውያንን ግሪኽን ተጻሒፎም ርእየዮም። ንምንታይ እዩ ብሰለስተ ቋንቋታት ተጻሒፉ?",
        "amh": "በአቅራቢያው ያሉትን ጽሁፎች በግዕዝ፣ በሳባውያን እና በግሪክ ተጽፈው አይቻለሁ። ለምን በሦስት ቋንቋዎች ተጻፈ?",
        "orm": "Barreeffamoota dhiyoo jiran Gi'iizii, Saabaa fi Giriikiin barreeffaman argeera. Maaliif afaanota sadiin barreeffame?",
    },
    # Turn 6: Guide explains international trade
    {
        "domain": "axum_tourist",
        "eng": "King Ezana wrote it in three languages so international trade partners from Rome and South Arabia could understand his royal decrees.",
        "tir": "ንጉሥ ኢዛና ብዓለም ደረጃ ዝነበሩ ናይ ንግዲ መሻርኽቱ ካብ ሮማን ደቡብ ዓረብን ንክርድእዎ ኢሉ እዩ ብሰለስተ ቋንቋታት ጽሒፍዎ።",
        "amh": "ንጉሥ ኢዛና ከሮምና ከደቡብ አረቢያ የመጡ ዓለም አቀፍ የንግድ አጋሮች የንጉሱን አዋጅ እንዲረዱ ብሎ ነው በሦስት ቋንቋዎች የጻፈው።",
        "orm": "Mootichi Eezaanaa daldaltoonni Roomaa fi Kibba Arabaa labata isaa akka hubataniif afaanota sadiin barreesse.",
    },
    # Turn 7: Tourist asks about Mary of Zion & Ark
    {
        "domain": "axum_tourist",
        "eng": "Is the Church of Our Lady Mary of Zion nearby? Can visitors see the Ark of the Covenant?",
        "tir": "ቤተክርስትያን ቅድስት ማርያም ጽዮን ኣብዚ ጥቓ ድዩ ዘሎ? በጻሕቲ ነቲ ታቦተ ጽዮን ክርእይዎ ይፍቀድ ድዩ?",
        "amh": "የቅድስት ማርያም ጽዮን ቤተክርስቲያን እዚ አቅራቢያ ነው ያለው? ጎብኚዎች ታቦተ ጽዮንን ማየት ይችላሉ?",
        "orm": "Mana sagadaa Qulqulluu Maariyaam Xiyoon as dhiyootti argamaa? Daawwattoonni Taabota Xiyoon argu danda'uu?",
    },
    # Turn 8: Guide explains sacred protocol & museum
    {
        "domain": "axum_tourist",
        "eng": "Yes, it is right nearby. The Ark is guarded solely by one consecrated monk, but we can visit the historical museum to see the ancient crowns and manuscripts.",
        "tir": "እወ ኣብዚ ጥቓ እዩ። እቲ ታቦት ብሓደ ውፉይ መነኮስ ጥራይ እዩ ዝሕሎ፡ ንሕና ግን ነቲ ታሪኻዊ ቤተ መዘክርን ጥንታውያን ዘውድታትን ክንርኢ ንኽእል ኢና።",
        "amh": "አዎ እዚ ቅርብ ነው ያለው። ታቦቱ በአንድ የተመረጠ መነኩሴ ብቻ ነው የሚጠበቀው፣ እኛ ግን ታሪካዊውን ቤተ መዘክርና የጥንት ዘውዶችን ማየት እንችላለን።",
        "orm": "Eeyyee, asuma dhiyoo jira. Taabotichi qeesii eebbifamaa tokkoon qofa eegama, garuu baallee fi barreeffamoota durii muuziyeemii seenaa keessatti ilaaluu dandeenya.",
    },
    # Turn 9: Guide invites to traditional coffee
    {
        "domain": "axum_tourist",
        "eng": "Now, let us sit in the shade and enjoy traditional Axumite coffee with fragrant frankincense.",
        "tir": "ሕጂ ድማ ንዑ ኣብዚ ጽላል ኮፍ ኢልና ባህላዊ ቡን ኣክሱም ምስ ጥዑም ዕጣን ንስተ።",
        "amh": "አሁን በዚህ ጥላ ስር ተቀምጠን ባህላዊውን የአክሱም ቡና ከጥሩ እጣን ጋር እንጠጣ።",
        "orm": "Amma gaaddisa jala teenyee buna aadaa Aksum urgooftuu ixaana waliin haa dhugnu.",
    },
    # Turn 10: Tourist thanks warmly
    {
        "domain": "axum_tourist",
        "eng": "That sounds wonderful! Thank you so much for your generous hospitality.",
        "tir": "ኣዝዩ ባህ ዘብል እዩ! ስለቲ ለጋስ ኣቀባብላኻ ኣዚየ እየ ዘመስግነካ።",
        "amh": "በጣም ደስ ይላል! ስላደረክልኝ ሞቅ ያለ አቀባበል እጅግ አድርጌ አመሰግናለሁ።",
        "orm": "Baay'ee namatti tola! Keessummeessaa keessan arjoomina qabuuf baay'ee galatoomaa.",
    },
]

def text_hash(lang: str, text: str) -> str:
    cleaned = text.strip()
    return f"{lang}_{hashlib.md5(cleaned.encode('utf-8')).hexdigest()[:10]}"

def main():
    print("=" * 70)
    print("Seeding Demo Scenarios into Translation Memory & TTS Cache")
    print("=" * 70)

    tm = TranslationMemory()
    cache_dir = ROOT_DIR / "output_tts" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    tts_engine = MMSTTSEngine()

    # 1. Seed Rural Clinic across all 4 languages
    print("\n[1/2] Seeding Rural Clinic Dialogue (Amharic, Oromo, Tigrinya, English)...")
    for i, item in enumerate(RURAL_CLINIC_DIALOGUE, 1):
        for s_l in ['amh', 'orm', 'tir', 'eng']:
            for t_l in ['amh', 'orm', 'tir', 'eng']:
                if s_l != t_l:
                    tm.insert(s_l, t_l, item[s_l], item[t_l], domain=item["domain"], dataset="demo_scenario", bidirectional=False)
        print(f"  Turn {i:02d}: All 4 languages seeded in TM")

        # Synthesize audio for all 4 languages
        for lang in ['amh', 'orm', 'tir', 'eng']:
            text = item[lang]
            h = text_hash(lang, text)
            wav_path = cache_dir / f"{h}.wav"
            if not wav_path.exists() or wav_path.stat().st_size < 500:
                wav_bytes = tts_engine.synthesize_to_bytes(text, lang=lang)
                with open(wav_path, "wb") as f:
                    f.write(wav_bytes)
                print(f"    ✓ Cached TTS audio: {h}.wav ({len(wav_bytes)//1024} KB)")

    # 2. Seed Axum Tourist across all 4 languages
    print("\n[2/2] Seeding Axum Tourist Dialogue (English, Tigrinya, Amharic, Oromo)...")
    for i, item in enumerate(AXUM_TOURIST_DIALOGUE, 1):
        for s_l in ['amh', 'orm', 'tir', 'eng']:
            for t_l in ['amh', 'orm', 'tir', 'eng']:
                if s_l != t_l:
                    tm.insert(s_l, t_l, item[s_l], item[t_l], domain=item["domain"], dataset="demo_scenario", bidirectional=False)
        print(f"  Turn {i:02d}: All 4 languages seeded in TM")

        # Synthesize audio for all 4 languages
        for lang in ['eng', 'tir', 'amh', 'orm']:
            text = item[lang]
            h = text_hash(lang, text)
            wav_path = cache_dir / f"{h}.wav"
            if not wav_path.exists() or wav_path.stat().st_size < 500:
                wav_bytes = tts_engine.synthesize_to_bytes(text, lang=lang)
                with open(wav_path, "wb") as f:
                    f.write(wav_bytes)
                print(f"    ✓ Cached TTS audio: {h}.wav ({len(wav_bytes)//1024} KB)")

    print("\n" + "=" * 70)
    print("✓ Successfully seeded all dialogue turns into Translation Memory!")
    print("✓ All neural audio files synthesized and cached in output_tts/cache/")
    print("=" * 70)

if __name__ == "__main__":
    main()
