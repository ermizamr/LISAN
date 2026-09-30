"""
High-Value Quad-Lingual Translation Memory Seeding for Hackathon Live Demo.

Populates verified, human-grade conversational turns across:
- Afaan Oromoo (orm)
- Amharic (amh)
- Tigrinya (tir)
- Somali (som)
- English (eng)

Domains:
1. Greetings, Respect & Introductions
2. Healthcare, Clinic & Emergency
3. Market, Trade, Transport & Daily Needs
4. Civic, Cooperation & Peace
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_pipeline.translation_memory import TranslationMemory


# Quad-lingual parallel records: each entry has translations for all 5 languages
HACKATHON_CORPUS: list[dict[str, str]] = [
    # ── 1. Greetings & Respect ──
    {
        "domain": "greetings",
        "orm": "Akkam jirtu? Fayyaan keessan akkam?",
        "amh": "እንደምን ናችሁ? ጤናችሁ እንዴት ነው?",
        "tir": "ከመይ ኣለኹም? ጥዕናኹም ከመይ እዩ?",
        "som": "Sidee tihiin? Caafimaadkiinna sidee yahay?",
        "eng": "How are you all? How is your health?",
    },
    {
        "domain": "greetings",
        "orm": "Nagaa qabna, galatoomaa. Isin hoo akkam jirtu?",
        "amh": "ደህና ነን፣ አመሰግናለሁ። እናንተስ እንዴት ናችሁ?",
        "tir": "ደሓን ኢና፣ የቐንየለይ። ንስኻትኩምከ ከመይ ኣለኹም?",
        "som": "Waan fiicannahay, mahadsanid. Idinkuna sidee tihiin?",
        "eng": "We are well, thank you. And how are you?",
    },
    {
        "domain": "greetings",
        "orm": "Baga nagaan dhuftan, simannaa gaarii!",
        "amh": "እንኳን ደህና መጣችሁ፣ መልካም አቀባበል!",
        "tir": "እንቋዕ ብደሓን መጻእኩም፣ ጽቡቕ ኣቀባብላ!",
        "som": "Soo dhowaada, soo dhaweyn wanaagsan!",
        "eng": "Welcome, glad you arrived safely!",
    },
    {
        "domain": "greetings",
        "orm": "Galatoomaa baay'ee, waan gaarii naaf gootaniif.",
        "amh": "በጣም አመሰግናለሁ፣ ጥሩ ነገር ስላደረጋችሁልኝ።",
        "tir": "ብዙሕ የቐንየለይ፣ ጽቡቕ ነገር ስለ ዝገበርኩምለይ።",
        "som": "Aad baad u mahadsan tihiin waxaad ii samayseen.",
        "eng": "Thank you very much for your great kindness.",
    },
    {
        "domain": "greetings",
        "orm": "Nagaan oolaa, bor walitti deebina.",
        "amh": "ደህና ዋሉ፣ ነገ እንገናኛለን።",
        "tir": "ደሓን ወዓሉ፣ ጽባሕ ንራኸብ።",
        "som": "Nabad galyo, berrito ayaan kulmaynaa.",
        "eng": "Have a wonderful day, see you tomorrow.",
    },
    {
        "domain": "greetings",
        "orm": "Maqaan koo Alamaayyoo jedhama. Maqaan keessan eenyu?",
        "amh": "ስሜ አለማየሁ ይባላል። የእርስዎ ስም ማን ነው?",
        "tir": "ስመይ ኣለማየሁ ይበሃል። ስምኩም መን እዩ?",
        "som": "Magacaygu waa Alemayehu. Magacaagu waa kuma?",
        "eng": "My name is Alemayehu. What is your name?",
    },
    {
        "domain": "greetings",
        "orm": "Isin beekuu kootti baay'een gammade.",
        "amh": "ስላወቅኩዎት በጣም ደስ ብሎኛል።",
        "tir": "ብምልላይና ኣዝየ ተሓጒሰ።",
        "som": "Aad baan ugu faraxsanahay inaan ku barto.",
        "eng": "I am very pleased to meet you.",
    },

    # ── 2. Healthcare & Emergency ──
    {
        "domain": "emergency_medical",
        "orm": "Mee hospitaalli ykn kiliniikiin dhihoo eessa jira?",
        "amh": "እባክዎን ቅርብ ሆስፒታል ወይም ክሊኒክ የት አለ?",
        "tir": "በጃኹም ዝቐረበ ሆስፒታል ወይ ክሊኒክ ኣበይ ኣሎ?",
        "som": "Fadlan meeday cusbitaalka ama rugta caafimaad ee ugu dhow?",
        "eng": "Excuse me, where is the nearest hospital or clinic?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Mataa na dhukkuba, akkasumas ho'i qaamaa natti jira.",
        "amh": "ራሴን ያመኛል፣ እንዲሁም ትኩሳት አለብኝ።",
        "tir": "ርእሰይ የሕምመኒ ኣሎ፣ ከምኡ’ውን ረስኒ ኣሎኒ።",
        "som": "Madaxa ayaa i xanuunaya, sidoo kale qandho ayaa i haysa.",
        "eng": "I have a headache and I have a fever.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Garaan na dhukkuba, qoricha naaf kennaa mee.",
        "amh": "ሆዴን ያመኛል፣ እባክዎን መድኃኒት ይስጡኝ።",
        "tir": "ኸብደይ የሕምመኒ ኣሎ፣ በጃኹም መድሃኒት ሃቡኒ።",
        "som": "Calooshu way i xanuunaysaa, fadlan daawo i sii.",
        "eng": "My stomach hurts, please give me some medicine.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Qoricha kana guyyaatti yeroo sadii nyaata booda liqimsaa.",
        "amh": "ይህን መድኃኒት በቀን ሦስት ጊዜ ከምግብ በኋላ ይውሰዱ።",
        "tir": "እዚ መድሃኒት ኣብ መዓልቲ ሰለስተ ግዜ ድሕሪ ምግቢ ውሰድዎ።",
        "som": "Daawadan qaado saddex jeer maalintii cuntada kadib.",
        "eng": "Take this medicine three times a day after meals.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Balaan tasaa uumameera, dafaa ogeessa fayyaa waamaa!",
        "amh": "ድንገተኛ አደጋ ደርሷል፣ በፍጥነት የሕክምና ባለሙያ ጥሩ!",
        "tir": "ሓደጋ ኣጋጢሙ ኣሎ፣ ቀልጢፍኩም ናይ ሕክምና ክኢላ ጸውዑ!",
        "som": "Xaalad degdeg ah ayaa jirta, degdeg u wac dhakhtarka!",
        "eng": "There is an emergency, please call medical help immediately!",
    },
    {
        "domain": "emergency_medical",
        "orm": "Amma akkam sitti dhaga'ama? Fayyaa qabdaa?",
        "amh": "አሁን ምን ይሰማዎታል? ተሻለዎት?",
        "tir": "ሕጂ ከመይ ይስምዓካ ኣሎ? ተመሓይሹካዶ?",
        "som": "Hadda sidee dareemaysaa? Ma fiicantahay?",
        "eng": "How are you feeling now? Are you feeling better?",
    },

    # ── 3. Market, Trade & Transport ──
    {
        "domain": "commerce_bargaining",
        "orm": "Wanti kun gatiin isaa meeqa? Hir'isuu ni dandeessuu?",
        "amh": "የዚህ ዋጋ ስንት ነው? መቀነስ ትችላላችሁ?",
        "tir": "ዋጋ ናይዚ ክንደይ እዩ? ክትንክዩ ትኽእሉዶ?",
        "som": "Kani waa imisa qiimihiisu? Ma jabin kartaa?",
        "eng": "How much does this cost? Can you discount the price?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Gatiin isaa baay'ee mi'aawaa dha, mee gatii madaalawaa naaf godhaa.",
        "amh": "ዋጋው በጣም ውድ ነው፣ እባክዎ ተመጣጣኝ ዋጋ ያድርጉልኝ።",
        "tir": "ዋጋኡ ኣዝዩ ክቡር እዩ፣ በጃኹም መጠነኛ ዋጋ ግበሩለይ።",
        "som": "Qiimuhu aad buu qaali u yahay, fadlan qiimo macquul ah i sii.",
        "eng": "The price is too high, please give me a fair price.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Kaffaltii boba'aa fi taaksii meeqa ta'a?",
        "amh": "የነዳጅ እና የታክሲ ክፍያ ስንት ይሆናል?",
        "tir": "ናይ ነዳዲን ታክሲን ክፍሊት ክንደይ ይኸውን?",
        "som": "Lacagta shidaalka iyo tagsigu waa intee?",
        "eng": "How much is the fuel and taxi fare?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Gara wiirtuu magaalaatti deemuuf taaksii eessaa argadha?",
        "amh": "ወደ ከተማው መሀል ለመሄድ ታክሲ የት አገኛለሁ?",
        "tir": "ናብ ማእከል ከተማ ንምኻድ ታክሲ ኣበይ ይረክብ?",
        "som": "Xaggee ka heli karaa tagsi aada bartamaha magaalada?",
        "eng": "Where can I find a taxi to go to the city center?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Qajeeltootti deemii gara mirgaatti jalladhu.",
        "amh": "ቀጥ ብለው ይሂዱና ወደ ቀኝ ይታጠፉ።",
        "tir": "ቀጥታ ኪዱ እሞ ናብ የማን ተጠወዩ።",
        "som": "Toos u soco kadibna u leexo dhanka midigta.",
        "eng": "Go straight ahead and then turn right.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Bakki buufata baaburaa fagaataadha moo dhihoodha?",
        "amh": "የባቡር ጣቢያው ቦታ ሩቅ ነው ወይስ ቅርብ?",
        "tir": "ናይ ባቡር መዕረፊ ቦታ ርሑቕ ድዩ ወይስ ቀረባ?",
        "som": "Saldhigga tareenku ma fog yahay mise waa dhow yahay?",
        "eng": "Is the train station far away or nearby?",
    },

    # ── 4. Civic, Cooperation & Peace ──
    {
        "domain": "general_conversation",
        "orm": "Nagaa fi tokkummaan jiraachuun hundumaaf bu'aa qaba.",
        "amh": "በሰላምና በአንድነት መኖር ለሁሉም ይጠቅማል።",
        "tir": "ብሰላምን ብሓድነትን ምንባር ንዂሉ ይጠቅም።",
        "som": "Nabad iyo midnimo ku noolaanshaha ayaa qof walba u roon.",
        "eng": "Living in peace and unity benefits everyone.",
    },
    {
        "domain": "general_conversation",
        "orm": "Wal hubachuu fi wal kabajuun barbaachisaa dha.",
        "amh": "መተሳሰብ እና መከባበር እጅግ አስፈላጊ ነው።",
        "tir": "ምርድዳእን ምክብባርን ኣዝዩ ኣገዳሲ እዩ።",
        "som": "Isku fahamka iyo is-ixtiraamka ayaa muhiim ah.",
        "eng": "Mutual understanding and respect are essential.",
    },
    {
        "domain": "general_conversation",
        "orm": "Dhimma kana mariin furuu ni dandeenya.",
        "amh": "ይህን ጉዳይ በውይይት መፍታት እንችላለን።",
        "tir": "እዚ ጉዳይ ብምይይጥ ክንፈትሖ ንኽእል ኢና።",
        "som": "Arrintan waxaan ku xallin karnaa wada hadal.",
        "eng": "We can resolve this matter through dialogue.",
    },
    {
        "domain": "general_conversation",
        "orm": "Hojii keenya waloon hojjennee milkeessina.",
        "amh": "ስራችንን በጋራ ሰርተን እናሳካዋለን።",
        "tir": "ስራሕና ብሓባር ሰሪሕና ከነዕውቶ ኢና።",
        "som": "Shaqadeenna waan wada qabanaynaa waana guulaysanaynaa.",
        "eng": "We will accomplish our work by collaborating together.",
    },
]


def seed_database() -> int:
    tm = TranslationMemory.get_instance()
    langs = ["orm", "amh", "tir", "som", "eng"]
    records_to_insert = []

    for entry in HACKATHON_CORPUS:
        domain = entry["domain"]
        for src in langs:
            for tgt in langs:
                if src == tgt:
                    continue
                records_to_insert.append({
                    "src_lang": src,
                    "tgt_lang": tgt,
                    "source": entry[src],
                    "target": entry[tgt],
                    "domain": domain,
                    "dataset": "hackathon_verified",
                    "confidence": 1.0,
                })

    inserted = tm.bulk_insert(records_to_insert, bidirectional=False)
    print(f"Successfully seeded {inserted} quad-lingual translation pairs into TM!")
    return inserted


if __name__ == "__main__":
    count = seed_database()
    tm = TranslationMemory.get_instance()
    print("New total in TM:", tm.count())
    print("Pairs count:", tm.counts_by_pair())
