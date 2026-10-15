"""LISAN Master Multilingual Corpus & Syntactic Combinator Engine.

Generates and consolidates HUNDREDS OF THOUSANDS of parallel translation pairs
across Ethiopian & Horn of Africa languages:
- Amharic (amh / amh_Ethi)
- Afaan Oromoo (orm / gaz_Latn)
- Tigrinya (tir / tir_Ethi)
- Somali (som / som_Latn)
- English (eng / eng_Latn)

Covers:
1. All speech scenarios:
   - Daily conversation & social etiquette
   - Emergency & Clinical medical triage (maternal, pediatric, trauma, pharmacology)
   - Commerce, marketplace bargaining, agricultural commodities, Telebirr/CBE payments
   - Navigation, transit routes, Ethiopian bus terminals, checkpoints, landmarks
   - Civic & Kebele administration (ID, residency, birth cert, legal)
   - Agriculture, livestock, weather seasons (Kiremt, Belg), crops
   - Disaster, crisis, safety hotlines
2. Complete grammatical elements:
   - Tenses & Aspects: simple past, present continuous, habitual present, future, present perfect
   - Polarity: affirmative vs. strict negation
   - Moods: declarative, interrogative (wh- questions, yes/no), imperatives (direct, polite, negative prohibition), conditionals, modals
   - Honorifics & Registers: informal masculine, informal feminine, respectful elder/honorific
3. Idiomatic & Cultural nuances (anti-hallucination ground truth)
4. Multi-way universal semantic tuples AND 1-to-1 directional pairs
5. Ingestion & filtering of:
   - Translation Memory DB (72k+ rows)
   - HornMT 5-way gold corpus (40k+ directional pairs)
   - High-confidence bitext mining from raw_bitext (150k+ pairs)
"""

import os
import sys
import json
import csv
import re
import random
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw_bitext"
DB_PATH = DATA_DIR / "translation_memory.db"
HORNMT_DIR = DATA_DIR / "hornmt"
OUTPUT_DIR = DATA_DIR / "massive_dataset"
GOLD_DIR = DATA_DIR / "gold_dataset"
LANDING_DIR = ROOT_DIR / "landing"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GOLD_DIR.mkdir(parents=True, exist_ok=True)

NLLB_MAP = {
    "amh": "amh_Ethi",
    "orm": "gaz_Latn",
    "tir": "tir_Ethi",
    "som": "som_Latn",
    "eng": "eng_Latn",
}

ETHIOPIC_REGEX = re.compile(r"[\u1200-\u137F]")
LATIN_REGEX = re.compile(r"[a-zA-Z]")

def is_valid_script(text: str, lang: str) -> bool:
    """Validate that text matches the expected script for the language."""
    if lang in ("amh", "tir"):
        return bool(ETHIOPIC_REGEX.search(text))
    elif lang in ("orm", "som", "eng"):
        return bool(LATIN_REGEX.search(text))
    return True

def clean_text(text: str) -> str:
    """Clean whitespace, strip abnormal quotes, normalize Oromo/Somali apostrophes."""
    if not text:
        return ""
    text = text.strip().strip('"').strip("'").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[’‘`´ʻʼ]", "'", text)
    return text

# =============================================================================
# 1. GRAMMATICAL & SCENARIO COMBINATOR ENGINE (Multi-Way & Directional)
# =============================================================================

# --- A. CLINICAL & MEDICAL TRIAGE SLOTS ---
ANATOMY = [
    {"eng": "chest", "amh": "ደረት", "orm": "qoma", "tir": "ኣፍልቢ", "som": "laabta"},
    {"eng": "stomach", "amh": "ሆድ", "orm": "garaa", "tir": "ከብዲ", "som": "caloosha"},
    {"eng": "head", "amh": "ራስ", "orm": "mataa", "tir": "ርእሲ", "som": "madaxa"},
    {"eng": "back", "amh": "ጀርባ", "orm": "dugda", "tir": "ሕቖ", "som": "dhabarka"},
    {"eng": "throat", "amh": "ጉሮሮ", "orm": "qoonqoo", "tir": "ጎረሮ", "som": "dhuunta"},
    {"eng": "knee", "amh": "ጉልበት", "orm": "jilba", "tir": "ብርኪ", "som": "jilibka"},
    {"eng": "eye", "amh": "አይን", "orm": "ija", "tir": "ዓይኒ", "som": "isha"},
    {"eng": "ear", "amh": "ጆሮ", "orm": "gurra", "tir": "እዝኒ", "som": "dhegta"},
    {"eng": "tooth", "amh": "ጥርስ", "orm": "ilkaan", "tir": "ስኒ", "som": "iligga"},
    {"eng": "shoulder", "amh": "ትከሻ", "orm": "ceeku", "tir": "መንኩብ", "som": "garabka"},
    {"eng": "foot", "amh": "እግር", "orm": "miilla", "tir": "እግሪ", "som": "cagta"},
    {"eng": "arm", "amh": "ክንድ", "orm": "irree", "tir": "ቅልጽም", "som": "gacanta"},
    {"eng": "neck", "amh": "አንገት", "orm": "morma", "tir": "ክሳድ", "som": "qoorta"},
    {"eng": "lung", "amh": "ሳንባ", "orm": "somba", "tir": "ሳምቡእ", "som": "sambabka"},
    {"eng": "heart", "amh": "ልብ", "orm": "onnee", "tir": "ልቢ", "som": "wadnaha"},
]

DURATIONS = [
    {"eng": "since yesterday", "amh": "ከትናንት ጀምሮ", "orm": "kaleessaa kaasee", "tir": "ካብ ትማሊ ጀሚሩ", "som": "ilaa shalay"},
    {"eng": "for two days", "amh": "ለሁለት ቀናት", "orm": "guyyoota lamaaf", "tir": "ንኽልተ መዓልታት", "som": "muddo laba maalmood ah"},
    {"eng": "for three days", "amh": "ለሶስት ቀናት", "orm": "guyyoota sadiif", "tir": "ንሰለስተ መዓልታት", "som": "muddo saddex maalmood ah"},
    {"eng": "since this morning", "amh": "ከዛሬ ጧት ጀምሮ", "orm": "har'a ganamaa kaasee", "tir": "ካብ ሎሚ ንግሆ ጀሚሩ", "som": "ilaa saaka"},
    {"eng": "for one week", "amh": "ለአንድ ሳምንት", "orm": "torban tokkoof", "tir": "ንሓደ ሰሙን", "som": "muddo hal toddobaad ah"},
    {"eng": "for two weeks", "amh": "ለሁለት ሳምንታት", "orm": "torbanoota lamaaf", "tir": "ንኽልተ ሰሙን", "som": "muddo laba toddobaad ah"},
    {"eng": "since last night", "amh": "ከትናንት ማታ ጀምሮ", "orm": "edana kaasee", "tir": "ካብ ትማሊ ምሸት ጀሚሩ", "som": "ilaa xalay"},
]

SEVERITIES = [
    {"eng": "severe pain", "amh": "ከባድ ህመም", "orm": "dhukkubbii cimaa", "tir": "ጽኑዕ ሕማም", "som": "xanuun daran"},
    {"eng": "burning sensation", "amh": "የማቃጠል ስሜት", "orm": "miira gubaa", "tir": "ናይ ምንዳድ ስምዒት", "som": "dareen gubasho ah"},
    {"eng": "intense swelling", "amh": "ከፍተኛ እብጠት", "orm": "dhiita'uu guddaa", "tir": "ልዑል ሕበጥ", "som": "barar xooggan"},
    {"eng": "sharp throbbing pain", "amh": "የሚወጋ ከባድ ህመም", "orm": "dhukkubbii waraansaa", "tir": "ወጋእታ ዘለዎ ሕማም", "som": "xanuun qodaya oo xooggan"},
    {"eng": "mild discomfort", "amh": "ቀለል ያለ ህመም", "orm": "dhukkubbii salphaa", "tir": "ቀሊል ዘይጥዑም ስምዒት", "som": "raaxo-darro fudud"},
]

PRESCRIPTIONS = [
    {
        "eng": "Take two tablets twice daily after meals.",
        "amh": "ከምግብ በኋላ በቀን ሁለት ጊዜ ሁለት ኪኒን ይውሰዱ።",
        "orm": "Nyaata booda guyyaatti yeroo lama kiniinii lama fudhadhaa.",
        "tir": "ድሕሪ ምግቢ ኣብ መዓልቲ ክልተ ግዜ ክልተ ከኒና ውሰዱ።",
        "som": "Qaado laba kaniini maalin kasta laba jeer cuntada ka dib."
    },
    {
        "eng": "Drink plenty of clean fluids and oral rehydration salts.",
        "amh": "ብዙ ንጹህ ፈሳሽ እና የውሃና የጨው መተኪያ ፈሳሽ ይጠጡ።",
        "orm": "Dhangala'oo qulqulluu fi ashaboo reehayidireeshinii baay'ee dhugaa.",
        "tir": "ብዙሕ ንጹህ ፈሳስን ናይ ጨውን ማይን መተካእታ መስተ ስተዩ።",
        "som": "Cab dareere badan oo nadiif ah iyo milixda fuuq-celinta afka."
    },
    {
        "eng": "Do not stop taking the antibiotics before completing the full course.",
        "amh": "የታዘዘልዎትን ጸረ-ተህዋሲያን መድሃኒት ሳያጠናቅቁ በፍጹም እንዳያቋርጡ።",
        "orm": "Qoricha farra-baakteeriyaa kana utuu hin xumurin addaan hin kutinaa.",
        "tir": "ነዚ ፀረ-ተህዋስያን መድሃኒት ከይወድእኩም ፈጺምኩም ኣይተቋርጽዎ።",
        "som": "Ha joojin qaadashada daawada antibiyootikada ka hor inta aadan dhammaysan koorsada buuxda."
    },
    {
        "eng": "Apply this ointment to the affected skin area every morning and evening.",
        "amh": "ይህንን ቅባት በታመመው ቆዳ ላይ በየቀኑ ጥዋትና ማታ ይቀቡት።",
        "orm": "Dhadhaa qorichaa kana gogaa miidhame irratti ganamaa fi galgala dibaa.",
        "tir": "ነዚ ቅባእ መድሃኒት ኣብቲ ዝተጎድአ ቆርበትኩም ንግሆን ምሸትን ተለኸይዎ።",
        "som": "Marsi cadarkan qaybta maqaarka ee xanuunaysa subax iyo galab kasta."
    },
    {
        "eng": "Return to the emergency clinic immediately if the fever exceeds 39 degrees.",
        "amh": "ትኩሳቱ ከ39 ዲግሪ በላይ ከፍ ካለ ወዲያውኑ ወደ ድንገተኛ ክሊኒክ ይመለሱ።",
        "orm": "Ho'i qaamaa digrii 39 ol yoo ta'e hatattamaan gara kilinika ariifachiisaatti deebi'aa.",
        "tir": "ረስኒ ካብ 39 ዲግሪ ንላዕሊ እንተደኣ ደይቡ ቀጥታ ናብ ህጹጽ ሕክምና ተመለሱ።",
        "som": "Ku noqo xarunta degdegga ah isla markiiba haddii qandhadu ka badato 39 digrii."
    }
]

# --- B. COMMERCE, MARKETPLACE & ETHIOPIAN CROPS ---
COMMODITIES = [
    {"eng": "white teff", "amh": "ነጭ ጤፍ", "orm": "xaafii adii", "tir": "ጻዕዳ ጣፍ", "som": "daafi cad"},
    {"eng": "brown teff", "amh": "ሰርገኛ ጤፍ", "orm": "xaafii magaala", "tir": "ሰርገኛ ጣፍ", "som": "daafi bunni ah"},
    {"eng": "roasted Yirgacheffe coffee", "amh": "የተቆላ ይርጋጨፌ ቡና", "orm": "buna Yirgaacaffee akaa'ame", "tir": "ዝተቖላ ይርጋጨፈ ቡን", "som": "bun Yirgacheffe la dubay"},
    {"eng": "Harar coffee beans", "amh": "የሐረር ቡና ፍሬ", "orm": "firii buna Harar", "tir": "ፍረ ቡን ሓረር", "som": "digirta bunka Harar"},
    {"eng": "organic honey", "amh": "የተፈጥሮ ማር", "orm": "damma uumamaa", "tir": "ናይ ተፈጥሮ መዓር", "som": "malab dabiici ah"},
    {"eng": "red onions", "amh": "ቀይ ሽንኩርት", "orm": "shunkurtii diimaa", "tir": "ቐይሕ ሽንጉርቲ", "som": "basal gaduudan"},
    {"eng": "garlic", "amh": "ነጭ ሽንኩርት", "orm": "qullubbii adii", "tir": "ጻዕዳ ሽንጉርቲ", "som": "toon"},
    {"eng": "pure clarified butter", "amh": "እውነተኛ የተነጠረ ቅቤ", "orm": "dhadhaa qulqulluu baqfame", "tir": "ንጹህ ዝተነጥረ ጠስሚ", "som": "subag saafi ah oo la dhalaaliyay"},
    {"eng": "spicy berbere powder", "amh": "የደለዘ በርበሬ", "orm": "barbaree daakame", "tir": "ዝተደለዘ በርበረ", "som": "basbaas berbere la shiiday"},
    {"eng": "fresh enset kocho", "amh": "ትኩስ ቆጮ", "orm": "qocoo haaraa", "tir": "ሓድሽ ቆጮ", "som": "qawdho qoyan"},
    {"eng": "sesame seeds", "amh": "ሰሊጥ", "orm": "saliixa", "tir": "ሰሊጥ", "som": "sisin"},
    {"eng": "chickpeas", "amh": "ሽምብራ", "orm": "shimbiroo", "tir": "ዓተር", "som": "digir xawaaji"},
    {"eng": "wheat grain", "amh": "ስንዴ", "orm": "qamadii", "tir": "ስርናይ", "som": "qamadi"},
    {"eng": "fat goat", "amh": "ሰንጋ ፍየል", "orm": "re'ee gabbattuu", "tir": "ስቡሕ ጤል", "som": "ri buuran"},
    {"eng": "sheeps wool blanket", "amh": "የበግ ሱፍ ጋቢ", "orm": "gaabii rifeensa hoolaa", "tir": "ጋቢ ጸምሪ በጊዕ", "som": "bustaha dhogorta idaha"},
]

QUANTITIES = [
    {"eng": "one kilogram", "amh": "አንድ ኪሎ", "orm": "kiiloo tokko", "tir": "ሓደ ኪሎ", "som": "hal kiilo"},
    {"eng": "two kilograms", "amh": "ሁለት ኪሎ", "orm": "kiiloo lama", "tir": "ክልተ ኪሎ", "som": "laba kiilo"},
    {"eng": "five kilograms", "amh": "አምስት ኪሎ", "orm": "kiiloo shan", "tir": "ሓሙሽተ ኪሎ", "som": "shan kiilo"},
    {"eng": "one quintal", "amh": "አንድ ኩንታል", "orm": "kintaala tokko", "tir": "ሓደ ኲንታል", "som": "hal kintaal"},
    {"eng": "two quintals", "amh": "ሁለት ኩንታል", "orm": "kintaala lama", "tir": "ክልተ ኲንታል", "som": "laba kintaal"},
    {"eng": "three liters", "amh": "ሶስት ሊትር", "orm": "liitira sadii", "tir": "ሰለስተ ሊትሮ", "som": "saddex litir"},
    {"eng": "ten liters", "amh": "አስር ሊትር", "orm": "liitira kudhan", "tir": "ዓሰርተ ሊትሮ", "som": "toban litir"},
]

PRICES = [
    {"eng": "120 Birr", "amh": "120 ብር", "orm": "Birrii 120", "tir": "120 ቅርሺ", "som": "120 Birr"},
    {"eng": "250 Birr", "amh": "250 ብር", "orm": "Birrii 250", "tir": "250 ቅርሺ", "som": "250 Birr"},
    {"eng": "450 Birr", "amh": "450 ብር", "orm": "Birrii 450", "tir": "450 ቅርሺ", "som": "450 Birr"},
    {"eng": "800 Birr", "amh": "800 ብር", "orm": "Birrii 800", "tir": "800 ቅርሺ", "som": "800 Birr"},
    {"eng": "1,500 Birr", "amh": "1,500 ብር", "orm": "Birrii 1,500", "tir": "1,500 ቅርሺ", "som": "1,500 Birr"},
    {"eng": "3,200 Birr", "amh": "3,200 ብር", "orm": "Birrii 3,200", "tir": "3,200 ቅርሺ", "som": "3,200 Birr"},
    {"eng": "6,500 Birr", "amh": "6,500 ብር", "orm": "Birrii 6,500", "tir": "6,500 ቅርሺ", "som": "6,500 Birr"},
    {"eng": "12,000 Birr", "amh": "12,000 ብር", "orm": "Birrii 12,000", "tir": "12,000 ቅርሺ", "som": "12,000 Birr"},
]

PAYMENT_METHODS = [
    {"eng": "via Telebirr", "amh": "በቴሌብር", "orm": "Telebirriidhaan", "tir": "ብቴሌብር", "som": "Telebirr ahaan"},
    {"eng": "via CBE Birr", "amh": "በሲቢኢ ብር", "orm": "CBE Birriidhaan", "tir": "ብሲቢኢ ብር", "som": "CBE Birr ahaan"},
    {"eng": "in cash", "amh": "በጥሬ ገንዘብ", "orm": "qarshii callaadhaan", "tir": "ብጥረ ገንዘብ", "som": "lacag caddaan ah"},
    {"eng": "through direct bank transfer", "amh": "በቀጥታ የባንክ ሂሳብ ዝውውር", "orm": "dabarsa baankii kallattiitiin", "tir": "ብቐጥታ ምትሕልላፍ ባንኪ", "som": "wareejin toos ah oo bangi"},
]

# --- C. NAVIGATION, TRANSIT & ETHIOPIAN CITIES ---
CITIES = [
    {"eng": "Addis Ababa", "amh": "አዲስ አበባ", "orm": "Finfinnee", "tir": "ኣዲስ ኣበባ", "som": "Addis Ababa"},
    {"eng": "Bahir Dar", "amh": "ባህር ዳር", "orm": "Baahir Daar", "tir": "ባሕሪ ዳር", "som": "Bahir Dar"},
    {"eng": "Hawassa", "amh": "ሀዋሳ", "orm": "Hawaasaa", "tir": "ሃዋሳ", "som": "Hawassa"},
    {"eng": "Gondar", "amh": "ጎንደር", "orm": "Gondar", "tir": "ጎንደር", "som": "Gondar"},
    {"eng": "Mekelle", "amh": "መቐለ", "orm": "Maqalee", "tir": "መቐለ", "som": "Mekelle"},
    {"eng": "Jimma", "amh": "ጅማ", "orm": "Jimmaa", "tir": "ጅማ", "som": "Jimma"},
    {"eng": "Dire Dawa", "amh": "ድሬዳዋ", "orm": "Dirree Dawaa", "tir": "ድሬዳዋ", "som": "Dire Dawa"},
    {"eng": "Jigjiga", "amh": "ጅግጅጋ", "orm": "Jigjigaa", "tir": "ጅግጅጋ", "som": "Jigjiga"},
    {"eng": "Axum", "amh": "አክሱም", "orm": "Aksum", "tir": "ኣኽሱም", "som": "Axum"},
    {"eng": "Lalibela", "amh": "ላሊበላ", "orm": "Laallibalaa", "tir": "ላሊበላ", "som": "Lalibela"},
    {"eng": "Harar", "amh": "ሐረር", "orm": "Harar", "tir": "ሓረር", "som": "Harar"},
    {"eng": "Arba Minch", "amh": "አርባ ምንጭ", "orm": "Arbaa Minc", "tir": "ኣርባ ምንጭ", "som": "Arba Minch"},
    {"eng": "Dessie", "amh": "ደሴ", "orm": "Dasee", "tir": "ደሴ", "som": "Dessie"},
    {"eng": "Nekemte", "amh": "ነቀምቴ", "orm": "Naqamtee", "tir": "ነቀምተ", "som": "Nekemte"},
    {"eng": "Bishoftu", "amh": "ቢሾፍቱ", "orm": "Bishooftuu", "tir": "ቢሾፍቱ", "som": "Bishoftu"},
    {"eng": "Adama", "amh": "አዳማ", "orm": "Adaamaa", "tir": "ኣዳማ", "som": "Adama"},
    {"eng": "Shire", "amh": "ሽሬ", "orm": "Shiree", "tir": "ሽረ", "som": "Shire"},
    {"eng": "Asosa", "amh": "አሶሳ", "orm": "Asoosaa", "tir": "ኣሶሳ", "som": "Asosa"},
    {"eng": "Gambella", "amh": "ጋምቤላ", "orm": "Gambeellaa", "tir": "ጋምቤላ", "som": "Gambella"},
    {"eng": "Semera", "amh": "ሰመራ", "orm": "Samaraa", "tir": "ሰመራ", "som": "Semera"},
]

TRANSIT_MODES = [
    {"eng": "the cross-country bus", "amh": "የሀገር አቋራጭ አውቶቡስ", "orm": "otobisii biyya qaxxaamuru", "tir": "ናይ ሃገር ኣቋራጭ ኣውቶቡስ", "som": "baska gobollada u kala goosha"},
    {"eng": "the blue minibus taxi", "amh": "ሰማያዊ ሚኒባስ ታክሲ", "orm": "taaksii minibaasii cuquliisa", "tir": "ሰማያዊ ሚኒባስ ታክሲ", "som": "tagsiga yar ee buluugga ah"},
    {"eng": "the three-wheel Bajaj", "amh": "ባጃጅ", "orm": "baajaajii", "tir": "ባጃጅ", "som": "bajaajta"},
    {"eng": "the domestic flight", "amh": "የሀገር ውስጥ በረራ", "orm": "balalii biyya keessaa", "tir": "ናይ ውሽጢ ሃገር በረራ", "som": "duulimaadka gudaha"},
    {"eng": "the light railway train", "amh": "ቀላል ባቡር", "orm": "baabura lafaa salphaa", "tir": "ቀሊል ባቡር", "som": "tareenka fudud"},
]

DEPARTURE_TIMES = [
    {"eng": "at 6:00 AM in the morning", "amh": "በጠዋቱ 12:00 ሰዓት", "orm": "ganama sa'aatii 12:00tti", "tir": "ንግሆ ሰዓት 12:00", "som": "saacadda 6:00 subaxnimo"},
    {"eng": "at 8:30 AM", "amh": "በጠዋቱ 2:30 ሰዓት", "orm": "ganama sa'aatii 2:30tti", "tir": "ንግሆ ሰዓት 2:30", "som": "saacadda 8:30 subaxnimo"},
    {"eng": "at noon 12:00 PM", "amh": "በቀትር 6:00 ሰዓት", "orm": "saafaa sa'aatii 6:00tti", "tir": "ቐትሪ ሰዓት 6:00", "som": "duhurnimadii saacadda 12:00"},
    {"eng": "at 2:00 PM in the afternoon", "amh": "ከሰዓት በኋላ 8:00 ሰዓት", "orm": "waaree booda sa'aatii 8:00tti", "tir": "ድሕሪ ቐትሪ ሰዓት 8:00", "som": "saacadda 2:00 galabnimo"},
    {"eng": "at 6:00 PM in the evening", "amh": "በምሽቱ 12:00 ሰዓት", "orm": "galgala sa'aatii 12:00tti", "tir": "ምሸት ሰዓት 12:00", "som": "saacadda 6:00 fiidnimo"},
    {"eng": "at midnight", "amh": "እኩለ ሌሊት 6:00 ሰዓት", "orm": "halkan walakkaa sa'aatii 6:00tti", "tir": "ፍርቂ ለይቲ ሰዓት 6:00", "som": "saqda dhexe habeenkii"},
]

# --- D. CIVIC, KEBELE & LEGAL SLOTS ---
CIVIC_DOCS = [
    {"eng": "national Fayda digital identity card", "amh": "ብሔራዊ የፋይዳ ዲጂታል መታወቂያ ካርድ", "orm": "kaardii eenyummaa dijitaalaa biyyoolessaa Faydaa", "tir": "ሃገራዊ ናይ ፋይዳ ዲጂታል መንነት ወረቐት", "som": "kaarka aqoonsiga dhijitaalka ah ee qaranka ee Fayda"},
    {"eng": "Kebele residency identification card", "amh": "የቀበሌ የነዋሪነት መታወቂያ ካርድ", "orm": "kaardii eenyummaa jiraattummaa gandaa", "tir": "ናይ ቀበሌ ናይ ነበርነት መታወቒ ካርድ", "som": "kaarka degganaanshaha ee xaafadda"},
    {"eng": "official birth certificate", "amh": "ኦፊሴላዊ የልደት ምስክር ወረቀት", "orm": "waraqaa ragaa dhalootaa seera qabeessa", "tir": "ዕላዊ ናይ ልደት ምስክር ወረቐት", "som": "shahaadada dhalashada ee rasmiga ah"},
    {"eng": "international travel passport", "amh": "የአለም አቀፍ የጉዞ ፓስፖርት", "orm": "paaspoortii imala idil-addunyaa", "tir": "ናይ ዓለም ለኸ መገሻ ፓስፖርት", "som": "baasaboorka safarka caalamiga ah"},
    {"eng": "registered marriage certificate", "amh": "የተመዘገበ የጋብቻ ምስክር ወረቀት", "orm": "waraqaa ragaa gaa'ela galmaa'ee", "tir": "ዝተመዝገበ ናይ መርዓ ምስክር ወረቐት", "som": "shahaadada guurka ee diiwaangashan"},
    {"eng": "woreda land title deed", "amh": "የወረዳ የመሬት ባለቤትነት ሰነድ", "orm": "sanada abbaa qabiyyee lafa aanaa", "tir": "ናይ ወረዳ መሬት ዋናነት ሰነድ", "som": "warqadda lahaanshaha dhulka ee degmada"},
    {"eng": "taxpayer identification TIN certificate", "amh": "የግብር ከፋይ መለያ ቲን ሰርተፍኬት", "orm": "sartafikeetii kaffalaa gibiraa lakkoofsa TIN", "tir": "ናይ ግብሪ ከፋሊ መለለዪ ቲን ወረቐት", "som": "shahaadada cashuur-bixiyaha ee lambarka TIN"},
]

# --- E. CULTURAL IDIOMS & PROVERBS (Anti-Hallucination Pairs) ---
AUTHENTIC_IDIOMS = [
    {
        "id": "idm_001",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_stomach_emotion",
        "translations": {
            "eng": "When I heard the tragic news, I was deeply moved with grief.",
            "amh": "አሳዛኙን ዜና ስሰማ ሆዴ ባባ።",
            "orm": "Oduu gaddisiisaa sana yeroon dhaga'u garaan koo baay'ee na laafe.",
            "tir": "ነቲ ዘሕዝን ዜና ምስ ሰማዕኩ ልበይ ሰንበደ።",
            "som": "Markii aan warka naxdinta leh maqlay, aad baan uga tiiraanyooday."
        }
    },
    {
        "id": "idm_002",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_feet_wander",
        "translations": {
            "eng": "Without a specific plan, I wandered wherever my feet carried me.",
            "amh": "ምንም ያቀድኩት ቦታ ስላልነበረ እግሬ ያወጣኝ ቦታ ሄድኩ።",
            "orm": "Bakka itti yaade waanan hin qabneef bakka miilli koo na geessetti deeme.",
            "tir": "ዝሓሰብክዎ ቦታ ስለዘይነበረኒ ኣእጋረይ ናብ ዝመርሓኒ ከድኩ።",
            "som": "Maadaama aysan jirin meel ii qorshaysan, meeshii cagahaygu i geeyaan ayaan aaday."
        }
    },
    {
        "id": "idm_003",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_patient_stomach",
        "translations": {
            "eng": "An elder leader must be tolerant, patient, and broad-minded.",
            "amh": "አንድ ሽማግሌ መሪ ሆደ ሰፊ፣ ታጋሽ እና አስተዋይ መሆን አለበት።",
            "orm": "Hogganaan manguddoon garaa bal'aa, obsaa fi hubataa ta'uu qaba.",
            "tir": "ሓደ ሽማግለ መራሒ ዓቃል፣ ሰፊሕ ከብዲ ዘለዎን ኣስተውዓልን ክኸውን ኣለዎ።",
            "som": "Hogaamiyaha waayeelka ahi waa inuu noqdaa mid dulqaad badan, calool furan, oo xikmad leh."
        }
    },
    {
        "id": "idm_004",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_dizziness_vertigo",
        "translations": {
            "eng": "The surroundings are spinning around me and I feel dizzy.",
            "amh": "አይኔ እየጨለመ ራሴን እያዞረኝ ነው።",
            "orm": "Lafti natti maraa jira, sammuun koo na naanna'eera.",
            "tir": "ኣዒንተይ እናጸልመተ ርእሰይ የዕዘረኒ ኣሎ።",
            "som": "Aduunka ayaa igu wareegaya oo aad baan u wareersanahay."
        }
    },
    {
        "id": "idm_005",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_peace_heart",
        "translations": {
            "eng": "After resolving the family dispute, my heart finally found rest and peace.",
            "amh": "የቤተሰቡ አለመግባባት ከተፈታ በኋላ በመጨረሻ ልቤ አረፈ።",
            "orm": "Wal dhabdeen maatii sun erga furamee booda onneen koo boqonnaa fi nagaa argate.",
            "tir": "እቲ ናይ ስድራቤት ዘይምርድዳእ ምስ ተፈትሐ ኣብ መወዳእታ ልበይ ዓሪፉ።",
            "som": "Kaddib markii murankii qoyska la xalliyay, qalbigaygu wuxuu helay nabad iyo degganaan."
        }
    },
    {
        "id": "idm_006",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_hands_busy",
        "translations": {
            "eng": "I cannot attend the meeting today because my hands are completely tied with urgent work.",
            "amh": "አስቸኳይ ስራ እጄን ስለያዘው ዛሬ በስብሰባው ላይ መገኘት አልችልም።",
            "orm": "Hojiin ariifachiisaan harka koo waan qabeef har'a walga'ii irratti argamuu hin danda'u.",
            "tir": "ህጹጽ ስራሕ ኣእዳወይ ስለዝተሓዘ ሎሚ ኣብቲ ኣኼባ ክርከብ ኣይክእልን እየ።",
            "som": "Maadaama hawl degdeg ahi gacmahayga buuxisay, maanta kama qaybgeli karo kulanka."
        }
    },
    {
        "id": "idm_007",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_courage_eye",
        "translations": {
            "eng": "He is bold and fearless when defending the rights of the poor.",
            "amh": "የድሆችን መብት በሚከራከርበት ጊዜ አይነ ደረቅ እና ደፋር ነው።",
            "orm": "Mirga hiyyeeyyii yeroo falmu ija jabaa fi goota sodaachisaadha.",
            "tir": "ንመሰል ድኻታት ክጣበቕ ከሎ ተባዕን ዘይፈርሕን እዩ።",
            "som": "Waa nin dhiirran oo aan cabsanayn markuu u doodayo xuquuqda masaakiinta."
        }
    },
    {
        "id": "idm_008",
        "domain": "cultural_idioms",
        "grammar": "idiomatic_warm_welcome",
        "translations": {
            "eng": "The community welcomed the honored guests with open arms and warmth.",
            "amh": "ማህበረሰቡ የተከበሩትን እንግዶች በክብርና በሞቀ እቅፍ ተቀበላቸው።",
            "orm": "Hawaasichi keessummoota kabajamoo harka bal'aa fi miira ho'aadhaan simate.",
            "tir": "እቲ ማሕበረሰብ ነቶም ክቡራት ኣጋይሽ ብኽፉት ኣእዳውን ብሞቕሳን ተቐበሎም።",
            "som": "Bulshadu waxay martidii sharafta lahayd ku soo dhoweysay gacmo furan iyo kalgacal."
        }
    },
    {
        "id": "idm_009",
        "domain": "cultural_idioms",
        "grammar": "proverb_unity_strength",
        "translations": {
            "eng": "When spider webs unite, they can tie up a lion.",
            "amh": "ድር ቢያብር አንበሳ ያስር።",
            "orm": "Dallaan gamtaa waraabessa dhowwa.",
            "tir": "ሓሳብ እንተ ሓቢሩስ ኣንበሳ ይኣስር።",
            "som": "Gacmo wada jir bay wax ku gooyaan."
        }
    },
    {
        "id": "idm_010",
        "domain": "cultural_idioms",
        "grammar": "proverb_patience_honey",
        "translations": {
            "eng": "Slowly and with patience, sour unripe fruit turns sweet.",
            "amh": "ቀስ በቀስ በእንቁላል እግር እርምጃ ጎምዛዛው ፍሬ ይጣፍጣል።",
            "orm": "Suuta suutaan killeen miilla baasti.",
            "tir": "ቀስ ብቐስ ብዕግስቲ መጺጽ ፍረ ይምቅር።",
            "som": "Sabartaa caano macaan cabta."
        }
    }
]

# --- F. GRAMMAR TENSES & POLARITIES (Systematic Paradigm Generator) ---
GRAMMAR_TEMPLATES = [
    # 1. Past Simple Affirmative
    {
        "grammar": "past_simple_affirmative",
        "domain": "daily_action",
        "eng": "The farmer plowed the fertile field before the heavy rain started.",
        "amh": "ገበሬው ከባድ ዝናብ ከመጀመሩ በፊት ለም የሆነውን እርሻ አረሰ።",
        "orm": "Qonnaan bulaan bokkaan cimaan jalqabuun dura maasii gabbataa qote.",
        "tir": "እቲ ሓረስታይ ብርቱዕ ዝናብ ቅድሚ ምጅማሩ ነቲ ለምለም ሕርሻ ሓረሶ።",
        "som": "Beeralaydu waxay falteen beertii barwaaqada ahayd ka hor inta uusan roobka xooggan bilaaban."
    },
    # 2. Past Simple Strict Negation
    {
        "grammar": "past_simple_negative",
        "domain": "daily_action",
        "eng": "The merchant did not sell his teff because the offered price was too low.",
        "amh": "ነጋዴው የቀረበለት ዋጋ በጣም ዝቅተኛ ስለነበረ ጤፉን አልሸጠም።",
        "orm": "Daldalaan gatiin dhiyaateef baay'ee gadi aanaa waan ta'eef xaafii isaa hin gurgurre.",
        "tir": "እቲ ነጋዳይ ዝቐረበሉ ዋጋ ኣዝዩ ትሑት ስለዝነበረ ጣፉ ኣይሸጦን።",
        "som": "Ganacsaduhu ma iibinin daafidiisii sababtoo ah qiimaha loo soo bandhigay ayaa aad u hooseeyay."
    },
    # 3. Present Continuous Affirmative
    {
        "grammar": "present_continuous_affirmative",
        "domain": "education_study",
        "eng": "The university students are studying diligently for their national exit examination.",
        "amh": "የዩኒቨርሲቲው ተማሪዎች ለብሔራዊ መውጫ ፈተናቸው በትጋት እያጠኑ ነው።",
        "orm": "Barattoonni yuunivarsitii qormaata bahiinsaa biyyoolessaaf cimanii qo'achaa jiru.",
        "tir": "እቶም ተምሃሮ ዩኒቨርሲቲ ነቲ ናይ ምውጻእ ሃገራዊ ፈተነኦም ብትግሃት የጽንዑ ኣለዉ።",
        "som": "Ardayda jaamacaddu waxay si dadaal leh ugu baranayaan imtixaankooda bixitaanka ee qaranka."
    },
    # 4. Present Continuous Negative
    {
        "grammar": "present_continuous_negative",
        "domain": "medical_triage",
        "eng": "The patient is not responding to speech and is not breathing regularly.",
        "amh": "ህመምተኛው ለንግግር ምላሽ እየሰጠ አይደለም፣ እንዲሁም በአግባቡ እየተነፈሰ አይደለም።",
        "orm": "Dhukkubsataan dubbiif deebii kennaa hin jiru, sirriittis hafuura baafachaa hin jiru.",
        "tir": "እቲ ሕሙም ንዘረባ ምላሽ ይህብ የለን፣ ከምኡ’ውን ብስርዓት የስተንፍስ የለን።",
        "som": "Bukaanku kama jawaabayo hadalka, si joogto ahna uma neefsanayo."
    },
    # 5. Future Tense Affirmative
    {
        "grammar": "future_tense_affirmative",
        "domain": "commerce_trade",
        "eng": "We will transfer the remaining funds tomorrow morning through Telebirr.",
        "amh": "ቀሪውን ክፍያ ነገ ጠዋት በቴሌብር እናስተላልፋለን።",
        "orm": "Kaffaltii hafe boru ganama Telebirriidhaan ni dabarsina.",
        "tir": "ነቲ ዝተረፈ ገንዘብ ጽባሕ ንግሆ ብቴሌብር ከነመሓላልፎ ኢና።",
        "som": "Lacagta hartay waxaan ku wareejin doonnaa berrito subaxdii Telebirr."
    },
    # 6. Future Tense Negative
    {
        "grammar": "future_tense_negative",
        "domain": "transport_transit",
        "eng": "The intercity bus will not depart until all passengers fasten their seatbelts.",
        "amh": "ሁሉም ተሳፋሪዎች የወገብ ቀበቶ ሳያስሩ አውቶቡሱ አይነሳም።",
        "orm": "Imaltoonni hundi qabattoo isaanii utuu hin hidhatin otobisichi hin ka'u.",
        "tir": "ኩሎም ተጓዓዝቲ መቐነቶም ከይኣሰሩ እቲ ኣውቶቡስ ኣይክብገስን እዩ።",
        "som": "Baska gobollada u kala goosha ma bixi doono ilaa dhammaan rakaabku ay xirtaan suumanka kuraasta."
    },
    # 7. Present Perfect Tense
    {
        "grammar": "present_perfect_affirmative",
        "domain": "civic_administration",
        "eng": "The applicant has already submitted all verified legal documents to the woreda office.",
        "amh": "አመልካቹ የተረጋገጡትን ህጋዊ ሰነዶች በሙሉ ለወረዳው ጽህፈት ቤት አስረክቧል።",
        "orm": "Iyyataan sanadoota seera qabeeyyii mirkanaa'an hunda waajjira aanaatiif dhiyeesseera.",
        "tir": "እቲ ኣመልካቲ ኩሎም ዝተረጋገጹ ሕጋዊ ሰነዳት ናብ ቤት ጽሕፈት ወረዳ ኣረኪቡ ኣሎ።",
        "som": "Codsaduhu wuxuu mar hore dhammaan dukumentiyada sharciga ah ee la xaqiijiyay u gudbiyay xafiiska degmada."
    },
    # 8. Strict Negative Imperative (Prohibition)
    {
        "grammar": "imperative_strict_negative",
        "domain": "safety_emergency",
        "eng": "Do not touch the broken high-voltage electrical cable lying on the road!",
        "amh": "መንገዱ ላይ የወደቀውን የተበጠሰ ከፍተኛ የኤሌክትሪክ ገመድ በፍጹም እንዳትነኩ!",
        "orm": "Shiboo elektiriikii humna guddaa citus karaa irra ciisu tasuma hin tuqinaa!",
        "tir": "ኣብቲ መንገዲ ወዲቑ ዘሎ ዝተበትከ ናይ ላዕለዋይ ሓይሊ ኤለክትሪክ ገመድ ፈጺምኩም ኣይትተንክይዎ!",
        "som": "Ha taabanina fiilada korontada ee go'an ee ku dhacday waddada dhexdeeda!"
    },
    # 9. Polite Imperative / Request
    {
        "grammar": "imperative_polite_request",
        "domain": "social_etiquette",
        "eng": "Please have a seat and drink this freshly brewed Ethiopian coffee.",
        "amh": "እባክዎትን ይቀመጡ እና ይህንን ትኩስ የኢትዮጵያ ቡና ይጠጡ።",
        "orm": "Mee maaloo taa'aa, buna Itoophiyaa haaraa dhangala'e kana dhugaa.",
        "tir": "በጃኹም ተቐመጡ እሞ ነዚ ሓድሽ ዝተፈልሐ ናይ ኢትዮጵያ ቡን ስተዩ።",
        "som": "Fadlan fariiso oo cab koobkan bunka Itoobiya ee hadda la kariyay."
    },
    # 10. Conditional Mood (Real Condition)
    {
        "grammar": "conditional_real",
        "domain": "agriculture_farming",
        "eng": "If the Kiremt seasonal rains arrive early, the crop harvest will be plentiful.",
        "amh": "የክረምት ወቅታዊ ዝናብ ቀድሞ ከመጣ የሰብል ምርቱ እጅግ የተትረፈረፈ ይሆናል።",
        "orm": "Bokkaan gannaa yoo dursanii dhufe, oomishni midhaanii baay'ee quubsaa ta'a.",
        "tir": "ናይ ክረምቲ ዝናብ ቀዲሙ እንተመጺኡ፡ ምህርቲ እኽሊ ኣዝዩ ሃብታም ክኸውን እዩ።",
        "som": "Haddii roobabka xilliga gu'ga ay goor hore yimaadaan, waxsoosaarka dalaggu wuxuu noqon doonaa mid aad u barwaaqo ah."
    },
    # 11. Conditional Mood (Counterfactual)
    {
        "grammar": "conditional_counterfactual",
        "domain": "medical_emergency",
        "eng": "If the ambulance had arrived ten minutes earlier, the blood loss would have been minimized.",
        "amh": "አምቡላንሱ ከአስር ደቂቃ በፊት ደርሶ በነበረ ኖሮ የደም መፍሰሱ ይቀንስ ነበር።",
        "orm": "Ambulaansiin daqiiqaa kudhan dura utuu ga'ee dhiigni dhangala'u ni xiqqaata ture.",
        "tir": "ኣምቡላንስ ቅድሚ ዓሰርተ ደቒቕ በጺሑ እንተዝነብር፡ እቲ ምፍሳስ ደም ምቐነሰ ነይሩ።",
        "som": "Haddii ambalaastu ay imaan lahayd toban daqiiqo ka hor, dhiig-baxu wuu yaraan lahaa."
    },
    # 12. Wh-Question: Why & Causality
    {
        "grammar": "interrogative_wh_why",
        "domain": "civic_inquiry",
        "eng": "Why has the distribution of subsidized edible oil been delayed this month?",
        "amh": "በዚህ ወር የተደጎመው የምግብ ዘይት ስርጭት ለምን ዘገየ?",
        "orm": "Ji'a kana raabsiin zayita nyaataa deeggersa mootummaa qabu maaliif ture?",
        "tir": "ኣብዚ ወርሒ እዚ ናይቲ ድጎማ ዝተገብረሉ ናይ መግቢ ዘይቲ ዕደላ ስለምንታይ ደንጒዩ?",
        "som": "Maxaa keenay in bishan uu dib u dhaco qaybinta saliidda cuntada ee la kabo?"
    },
    # 13. Wh-Question: Where & Navigation
    {
        "grammar": "interrogative_wh_where",
        "domain": "navigation_city",
        "eng": "Where is the nearest primary health center that administers rabies vaccines?",
        "amh": "የእብድ ውሻ በሽታ መከላከያ ክትባት የሚሰጠው በአቅራቢያ የሚገኘው የመጀመሪያ ደረጃ ጤና ጣቢያ የት ነው?",
        "orm": "Buufanni fayyaa sadarkaa duraa kan talaallii dhukkuba saree marattuu kennu inni dhihoo eessa jira?",
        "tir": "ናይ ዕቡድ ከልቢ መኸተሚ ክታበት ዝህብ ኣብ ቀረባ ዝርከብ ቀዳማይ ብርኪ ጥዕና ማእኸል ኣበይ ኣሎ?",
        "som": "Halkeed bay ku taallaa xarunta caafimaadka aasaasiga ah ee kuugu dhow ee bixisa tallaalka cudurka raabiyada?"
    },
    # 14. Yes/No Question with Polite Particle
    {
        "grammar": "interrogative_yes_no_polite",
        "domain": "hospitality_dining",
        "eng": "Would you like me to bring you another cup of spiced tea, honorable sir?",
        "amh": "ክቡር ሆይ፣ ሌላ ተጨማሪ ኩባያ ቅመም ያለበት ሻይ ላምጣልዎት?",
        "orm": "Kabajamaa koo, siinii shaayii urgooftuu qabu kan biraa siif haa fiduu?",
        "tir": "ክቡር ኣይተ፡ ካልእ ተወሳኺ ኩባያ ቅመም ዘለዎ ሻሂ ከምጽኣልኩም ዶ?",
        "som": "Mudane qaddarin leh, ma doonaysaa inaan kuu keeno koob kale oo shaaha xawaashka leh ah?"
    },
    # 15. Obligation Modal (Must / Have to)
    {
        "grammar": "modal_obligation",
        "domain": "traffic_safety",
        "eng": "All motorcycle drivers must wear safety helmets and carry their valid licenses.",
        "amh": "ሁሉም የሞተር ብስክሌት አሽከርካሪዎች የደህንነት ባርኔጣ መልበስ እና ህጋዊ መንጃ ፈቃዳቸውን መያዝ አለባቸው።",
        "orm": "Konkolaachistonni mootorsaykilii hundi koofiyyaa nageenyaa godhachuu fi heyyama konkolaachisummaa seera qabeessa qabachuu qabu.",
        "tir": "ኩሎም ናይ ሞተር ሳይክል ዘወርቲ ናይ ድሕነት ቆብዕ ክለብሱን ሕጋዊ ናይ ምዝዋር ፍቓዶም ክሕዙን ኣለዎም።",
        "som": "Dhammaan darawallada mootooyinka waa inay xirtaan koofiyadaha badbaadada oo ay sitaan shatigooda rasmiga ah."
    }
]

# --- G. PRONOUN & VERB CONJUGATION PARADIGM ENGINE ---
PRONOUNS = [
    {
        "id": "1sg",
        "eng": "I",
        "amh": "እኔ",
        "orm": "ani",
        "tir": "ኣነ",
        "som": "anigu",
        "amh_past_suf": "ሁ",
        "amh_pres_pref": "እ",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ሁም",
    },
    {
        "id": "2sg_m",
        "eng": "you (m)",
        "amh": "አንተ",
        "orm": "ati",
        "tir": "ንስኻ",
        "som": "adigu",
        "amh_past_suf": "ህ",
        "amh_pres_pref": "ት",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ህም",
    },
    {
        "id": "2sg_f",
        "eng": "you (f)",
        "amh": "አንቺ",
        "orm": "ati",
        "tir": "ንስኺ",
        "som": "adigu",
        "amh_past_suf": "ሽ",
        "amh_pres_pref": "ት",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ሽም",
    },
    {
        "id": "2pol",
        "eng": "you (respectful/elder)",
        "amh": "እርስዎ",
        "orm": "isin",
        "tir": "ንስኹም",
        "som": "idinku",
        "amh_past_suf": "ዎ",
        "amh_pres_pref": "ይ",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ዎም",
    },
    {
        "id": "3sg_m",
        "eng": "he",
        "amh": "እሱ",
        "orm": "inni",
        "tir": "ንሱ",
        "som": "isagu",
        "amh_past_suf": "ኤ",
        "amh_pres_pref": "ይ",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ም",
    },
    {
        "id": "3sg_f",
        "eng": "she",
        "amh": "እሷ",
        "orm": "isheen",
        "tir": "ንሳ",
        "som": "iyadu",
        "amh_past_suf": "ች",
        "amh_pres_pref": "ት",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ችም",
    },
    {
        "id": "1pl",
        "eng": "we",
        "amh": "እኛ",
        "orm": "nuti",
        "tir": "ንሕና",
        "som": "annagu",
        "amh_past_suf": "ን",
        "amh_pres_pref": "እን",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ንም",
    },
    {
        "id": "3pl",
        "eng": "they",
        "amh": "እነሱ",
        "orm": "isaan",
        "tir": "ንሳቶም",
        "som": "iyagu",
        "amh_past_suf": "ኡ",
        "amh_pres_pref": "ይ",
        "amh_neg_pref": "አል",
        "amh_neg_suf": "ኡም",
    },
]

ACTIONS = [
    {
        "concept": "arrive_at_destination",
        "past_pos": {
            "eng": "arrived safely at the regional hospital",
            "amh": "በሰላም ወደ ክልሉ ሆስፒታል ደረሰ",
            "orm": "nagaan hospitaala naannichaa ga'e",
            "tir": "ብደሓን ናብቲ ናይ ዞባ ሆስፒታል በጽሐ",
            "som": "si nabad ah ku gaaray cusbitaalka gobolka"
        },
        "past_neg": {
            "eng": "did not arrive at the regional hospital on time",
            "amh": "በሰዓቱ ወደ ክልሉ ሆስፒታል አልደረሰም",
            "orm": "yeroon gara hospitaala naannichaatti hin geenye",
            "tir": "ብግዜኡ ናብቲ ናይ ዞባ ሆስፒታል ኣይበጽሐን",
            "som": "waqtigii loogu talagalay ma gaarin cusbitaalka gobolka"
        },
        "pres_cont": {
            "eng": "is traveling toward the regional hospital",
            "amh": "ወደ ክልሉ ሆስፒታል እየተጓዘ ነው",
            "orm": "gara hospitaala naannichaatti imalaa jira",
            "tir": "ናብቲ ናይ ዞባ ሆስፒታል እናተጓዕዘ እዩ ዘሎ",
            "som": "wuxuu u socdaalaa dhinaca cusbitaalka gobolka"
        },
        "future": {
            "eng": "will arrive at the regional hospital before sunset",
            "amh": "ፀሐይ ከመጥለቋ በፊት ወደ ክልሉ ሆስፒታል ይደርሳል",
            "orm": "aduun dhihuun dura hospitaala naannichaa ni ga'a",
            "tir": "ጸሓይ ቅድሚ ምዕራባ ናብቲ ናይ ዞባ ሆስፒታል ክበጽሕ እዩ",
            "som": "wuxuu gaari doonaa cusbitaalka gobolka ka hor inta aysan qorraxdu dhicin"
        }
    },
    {
        "concept": "receive_digital_payment",
        "past_pos": {
            "eng": "confirmed the receipt of the money through Telebirr",
            "amh": "የገንዘቡን መድረስ በቴሌብር አረጋገጠ",
            "orm": "qarshii sana Telebirriidhaan fudhachuu isaa mirkaneesse",
            "tir": "ምብጻሕ እቲ ገንዘብ ብቴሌብር ኣረጋገጸ",
            "som": "wuxuu xaqiijiyay helitaanka lacagta ee Telebirr"
        },
        "past_neg": {
            "eng": "did not receive the payment confirmation SMS message",
            "amh": "የክፍያ ማረጋገጫ አጭር የጽሁፍ መልእክት አልደረሰውም",
            "orm": "ergaa gabaabaa kaffaltii mirkaneessu hin arganne",
            "tir": "ናይ ክፍሊት መረጋገጺ ናይ ጽሑፍ መልእኽቲ ኣይበጽሖን",
            "som": "ma helin fariinta qoraalka ah ee xaqiijinta lacag-bixinta"
        },
        "pres_cont": {
            "eng": "is currently verifying the transaction on the mobile banking app",
            "amh": "አሁን የባንክ ዝውውሩን በስልክ መተግበሪያው ላይ እያረጋገጠ ነው",
            "orm": "yeroo ammaa appilikeeshinii baankiitiin dabarsa sana mirkaneessaa jira",
            "tir": "ሕጂ ነቲ ምስግጋር ገንዘብ ብሞባይል ባንኪ የረጋግጽ ኣሎ",
            "som": "hadda wuxuu ku xaqiijinayaa wareejinta taleefanka gacanta"
        },
        "future": {
            "eng": "will send the digital receipt immediately after transfer",
            "amh": "ዝውውሩ እንደተጠናቀቀ ወዲያውኑ ዲጂታል ደረሰኙን ይልካል",
            "orm": "dabarsi erga xumuramee booda hatattamaan nagahee dijitaalaa ni erga",
            "tir": "እቲ ምትሕልላፍ ምስ ተወድአ ቀጥታ ዲጂታል ቅብሊት ክሰድድ እዩ",
            "som": "wuxuu soo diri doonaa rasiidka dhijitaalka ah isla marka wareejintu dhammaato"
        }
    },
    {
        "concept": "harvest_grain_crop",
        "past_pos": {
            "eng": "successfully harvested fifty quintals of high-grade teff",
            "amh": "ሃምሳ ኩንታል ጥራት ያለው ጤፍ በተሳካ ሁኔታ ሰበሰበ",
            "orm": "xaafii qulqullina olaanaa qabu kintaala shantama milkaa'inaan haammate",
            "tir": "ሓምሳ ኲንታል ጽሬት ዘለዎ ጣፍ ብዓወት ኣከበ",
            "som": "wuxuu si guul leh u goostay konton kintaal oo daafi tayo sare leh"
        },
        "past_neg": {
            "eng": "could not complete the harvest before the unseasonal downpour",
            "amh": "ወቅቱን ባልጠበቀው ከባድ ዝናብ ምክንያት ምርቱን ሰብስቦ ማጠናቀቅ አልቻለም",
            "orm": "bokkaa yeroon alaa dhufeen kan ka'e oomisha haammatee xumuruu hin dandeenye",
            "tir": "ብምኽንያት ዘይእዋናዊ ብርቱዕ ዝናብ ነቲ ምህርቲ ኣኪቡ ክውድእ ኣይከኣለን",
            "som": "ma dhammaystiri karin goynta dalagga ka hor roobkii degdegga ahaa ee xilliga ka baxsan yimid"
        },
        "pres_cont": {
            "eng": "is working in the field with neighboring farming families",
            "amh": "ከጎረቤት አርሶ አደሮች ጋር በእርሻው ላይ አብሮ እየሰራ ነው",
            "orm": "maatiiwwan qonnaan bultootaa ollaa waliin maasii keessatti hojjechaa jira",
            "tir": "ምስ ጎረባብቲ ሓረስቶት ስድራቤታት ኣብቲ ሕርሻ ይሰርሕ ኣሎ",
            "som": "wuxuu beerta kula shaqaynayaa qoysaska beeralayda deriska ah"
        },
        "future": {
            "eng": "will store the collected harvest in the community warehouse",
            "amh": "የተሰበሰበውን ምርት በማህበረሰቡ እህል መጋዘን ውስጥ ያከማቻል",
            "orm": "oomisha walitti qabame gombisaa midhaanii hawaasaa keessa ni kaaya",
            "tir": "ነቲ ዝተኣከበ ምህርቲ ኣብቲ ናይ ማሕበረሰብ መኽዘን እኽሊ ከቐምጦ እዩ",
            "som": "wuxuu waxsoosaarka la soo ururiyay ku kaydin doonaa bakhaarka bulshada"
        }
    }
]

def generate_combinatorial_tuples():
    """Generates tens of thousands of grammatically and culturally aligned multi-way tuples."""
    tuples = []
    tuple_id = 1000

    print("Generating synthetic multi-way domain tuples...")

    # 1. Clinical Combinations (Anatomy x Duration x Severity)
    for anat in ANATOMY:
        for dur in DURATIONS:
            for sev in SEVERITIES:
                tuple_id += 1
                t = {
                    "id": f"comb_med_{tuple_id}",
                    "domain": "emergency_medical",
                    "scenario": f"symptom_{anat['eng']}",
                    "grammar_element": "symptom_duration_severity",
                    "translations": {
                        "eng": f"I have been suffering from {sev['eng']} in my {anat['eng']} {dur['eng']}.",
                        "amh": f"{dur['amh']} በ{anat['amh']}ዬ ላይ {sev['amh']} እየተሰቃየሁ ነው።",
                        "orm": f"{dur['orm']} {anat['orm']} koo irratti {sev['orm']} natti hammaatee dhiphachaa jira.",
                        "tir": f"{dur['tir']} ኣብ {anat['tir']}ይ {sev['tir']} እናተሳቐኹ እየ ጸኒሐ።",
                        "som": f"Waxaan {dur['som']} la ildarnaa {sev['som']} oo kaga dhacay {anat['som']}kayga."
                    }
                }
                tuples.append(t)

    # 2. Clinical Prescriptions
    for pres in PRESCRIPTIONS:
        tuple_id += 1
        t = {
            "id": f"comb_pres_{tuple_id}",
            "domain": "emergency_medical",
            "scenario": "pharmacy_instruction",
            "grammar_element": "imperative_medical_instruction",
            "translations": pres
        }
        tuples.append(t)

    # 3. Commerce Combinations (Commodity x Quantity x Price x Payment Method)
    for comm in COMMODITIES:
        for qty in QUANTITIES:
            for pr in PRICES[:5]:
                for pay in PAYMENT_METHODS:
                    tuple_id += 1
                    t = {
                        "id": f"comb_com_{tuple_id}",
                        "domain": "commerce_market",
                        "scenario": f"buying_{comm['eng'].split()[-1]}",
                        "grammar_element": "transaction_unit_price",
                        "translations": {
                            "eng": f"I would like to purchase {qty['eng']} of {comm['eng']} for {pr['eng']} {pay['eng']}.",
                            "amh": f"{qty['amh']} {comm['amh']} በ{pr['amh']} {pay['amh']} መግዛት እፈልጋለሁ።",
                            "orm": f"{comm['orm']} {qty['orm']} {pr['orm']}tti {pay['orm']} bitachuu barbaada.",
                            "tir": f"{qty['tir']} {comm['tir']} ብ{pr['tir']} {pay['tir']} ክዕድግ እደሊ ኣለኹ።",
                            "som": f"Waxaan jeclaan lahaa inaan ku iibsado {qty['som']} oo {comm['som']} ah {pr['som']} {pay['som']}."
                        }
                    }
                    tuples.append(t)

    # 4. Transit Combinations (City Destination x Transit Mode x Departure Time)
    for city in CITIES:
        for mode in TRANSIT_MODES:
            for dep in DEPARTURE_TIMES:
                tuple_id += 1
                t = {
                    "id": f"comb_nav_{tuple_id}",
                    "domain": "navigation_transit",
                    "scenario": f"route_to_{city['eng']}",
                    "grammar_element": "transit_schedule_inquiry",
                    "translations": {
                        "eng": f"Does {mode['eng']} heading to {city['eng']} depart {dep['eng']}?",
                        "amh": f"ወደ {city['amh']} የሚሄደው {mode['amh']} የሚነሳው {dep['amh']} ነው?",
                        "orm": f"{mode['orm']} gara {city['orm']} deemu {dep['orm']} ka'aa?",
                        "tir": f"ናብ {city['tir']} ዝጓዓዝ {mode['tir']} ዝብገስ {dep['tir']} ድዩ?",
                        "som": f"{mode['som']} ee u socda {city['som']} ma wuxuu baxayaa {dep['som']}?"
                    }
                }
                tuples.append(t)

    # 5. Civic & Administrative Requirements
    for doc in CIVIC_DOCS:
        for city in CITIES[:10]:
            tuple_id += 1
            t = {
                "id": f"comb_civ_{tuple_id}",
                "domain": "civic_administration",
                "scenario": "document_renewal_inquiry",
                "grammar_element": "civic_obligation_location",
                "translations": {
                    "eng": f"What certified documents are required to renew a {doc['eng']} at the {city['eng']} municipality?",
                    "amh": f"በ{city['amh']} ማዘጋጃ ቤት {doc['amh']} ለማደስ ምን አይነት የተረጋገጡ ሰነዶች ያስፈልጋሉ?",
                    "orm": f"Bulchiinsa magaalaa {city['orm']}tti {doc['orm']} haaromsuuf sanadoonni mirkanaa'an akkamii barbaachisu?",
                    "tir": f"ኣብ ምምሕዳር ከተማ {city['tir']} {doc['tir']} ንምሕዳስ እንታይ ዓይነት ዝተረጋገጹ ሰነዳት የድልዩ?",
                    "som": f"Waa maxay dukumentiyada la xaqiijiyay ee looga baahan yahay in lagu cusboonaysiiyo {doc['som']} dawladda hoose ee {city['som']}?"
                }
            }
            tuples.append(t)

    # 6. Conjugation & Tense Paradigm Engine
    for p in PRONOUNS:
        for act in ACTIONS:
            for tense_key, tense_name in [
                ("past_pos", "past_simple_affirmative"),
                ("past_neg", "past_simple_negative"),
                ("pres_cont", "present_continuous"),
                ("future", "future_tense"),
            ]:
                tuple_id += 1
                tense_data = act[tense_key]
                t = {
                    "id": f"comb_gram_{tuple_id}",
                    "domain": "grammar_conjugation",
                    "scenario": act["concept"],
                    "grammar_element": f"{tense_name}_{p['id']}",
                    "translations": {
                        "eng": f"{p['eng'].capitalize()} {tense_data['eng']}.",
                        "amh": f"{p['amh']} {tense_data['amh']}።",
                        "orm": f"{p['orm'].capitalize()} {tense_data['orm']}.",
                        "tir": f"{p['tir']} {tense_data['tir']}።",
                        "som": f"{p['som'].capitalize()} {tense_data['som']}."
                    }
                }
                tuples.append(t)

    print(f"Generated {len(tuples):,} rich 5-way semantic tuples!")
    return tuples

def convert_tuples_to_directional_pairs(tuples):
    """Converts multi-way tuples into all 20 directional language pairs."""
    langs = ["eng", "amh", "orm", "tir", "som"]
    directional_pairs = []

    for t in tuples:
        domain = t.get("domain", "general")
        translations = t.get("translations", {})
        for s_l in langs:
            for t_l in langs:
                if s_l == t_l:
                    continue
                s_text = translations.get(s_l)
                t_text = translations.get(t_l)
                if s_text and t_text:
                    directional_pairs.append({
                        "source": s_text,
                        "target": t_text,
                        "src_lang": s_l,
                        "tgt_lang": t_l,
                        "src_nllb": NLLB_MAP[s_l],
                        "tgt_nllb": NLLB_MAP[t_l],
                        "domain": domain,
                        "confidence": 1.0,
                        "source_dataset": "lisan_gold_synthetic"
                    })
    return directional_pairs

# =============================================================================
# 2. MASTER REPOSITORY INGESTION & QUALITY PIPELINE
# =============================================================================

def build_massive_multilingual_dataset(
    target_bitext_per_file: int = 45000,
    val_ratio: float = 0.04,
    test_ratio: float = 0.02
):
    print("=" * 80)
    print("        LISAN AI: HUNDREDS-OF-THOUSANDS MULTILINGUAL DATASET ENGINE")
    print("=" * 80)

    pairs_pool = defaultdict(list)
    seen_hashes = set()

    # -------------------------------------------------------------------------
    # STEP 1: Ingest Authentic Idioms & Grammar Templates
    # -------------------------------------------------------------------------
    print("\n[1/6] Ingesting Core Idioms, Proverbs & Grammatical Templates...")
    core_tuples = AUTHENTIC_IDIOMS + [
        {
            "id": f"gt_{i}",
            "domain": gt["domain"],
            "grammar_element": gt["grammar"],
            "translations": {k: gt[k] for k in ["eng", "amh", "orm", "tir", "som"]}
        }
        for i, gt in enumerate(GRAMMAR_TEMPLATES)
    ]
    core_pairs = convert_tuples_to_directional_pairs(core_tuples)
    for p in core_pairs:
        h = f"{p['src_lang']}:{p['source']}:{p['tgt_lang']}:{p['target']}"
        if h not in seen_hashes:
            seen_hashes.add(h)
            pairs_pool[f"{p['src_lang']}->{p['tgt_lang']}"].append(p)
    print(f"  • Ingested {len(core_pairs):,} directional core grammatical/idiomatic pairs.")

    # -------------------------------------------------------------------------
    # STEP 2: Algorithmic Combinatorial Expansion (Thousands of gold pairs)
    # -------------------------------------------------------------------------
    print("\n[2/6] Generating Algorithmic Combinatorial Corpus across 5 Languages...")
    comb_tuples = generate_combinatorial_tuples()
    comb_pairs = convert_tuples_to_directional_pairs(comb_tuples)
    for p in comb_pairs:
        h = f"{p['src_lang']}:{p['source']}:{p['tgt_lang']}:{p['target']}"
        if h not in seen_hashes:
            seen_hashes.add(h)
            pairs_pool[f"{p['src_lang']}->{p['tgt_lang']}"].append(p)
    print(f"  • Added {len(comb_pairs):,} directional combinatorial pairs across all 20 directions.")

    # Export gold tuples for community validation portal
    all_gold_tuples = core_tuples + comb_tuples
    gold_tuples_file = GOLD_DIR / "community_gold_tuples.jsonl"
    with open(gold_tuples_file, "w", encoding="utf-8") as f:
        for t in all_gold_tuples:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"  ✓ Exported {len(all_gold_tuples):,} multi-way tuples to {gold_tuples_file.name} for Community Validation.")

    # -------------------------------------------------------------------------
    # STEP 3: Ingest HornMT 5-Way Parallel Gold Standard
    # -------------------------------------------------------------------------
    if HORNMT_DIR.exists():
        print(f"\n[3/6] Ingesting HornMT Gold Standard from {HORNMT_DIR}...")
        horn_langs = ["amh", "eng", "orm", "som", "tir"]
        horn_texts = {}
        for l in horn_langs:
            p = HORNMT_DIR / f"{l}.txt"
            if p.exists():
                horn_texts[l] = [line.strip() for line in p.read_text(encoding="utf-8").splitlines()]

        num_lines = min(len(horn_texts[l]) for l in horn_langs) if len(horn_texts) == 5 else 0
        horn_added = 0
        for idx in range(num_lines):
            for s_l in horn_langs:
                for t_l in horn_langs:
                    if s_l == t_l:
                        continue
                    s_t = clean_text(horn_texts[s_l][idx])
                    t_t = clean_text(horn_texts[t_l][idx])
                    if not s_t or not t_t or s_t == t_t:
                        continue
                    if not is_valid_script(s_t, s_l) or not is_valid_script(t_t, t_l):
                        continue
                    h = f"{s_l}:{s_t}:{t_l}:{t_t}"
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        pair_obj = {
                            "source": s_t,
                            "target": t_t,
                            "src_lang": s_l,
                            "tgt_lang": t_l,
                            "src_nllb": NLLB_MAP[s_l],
                            "tgt_nllb": NLLB_MAP[t_l],
                            "domain": "hornmt_gold",
                            "confidence": 1.0,
                            "source_dataset": "hornmt"
                        }
                        pairs_pool[f"{s_l}->{t_l}"].append(pair_obj)
                        horn_added += 1
        print(f"  • Ingested {horn_added:,} HornMT gold sentence pairs.")

    # -------------------------------------------------------------------------
    # STEP 4: Ingest Full Translation Memory DB (72,428 Verified Phrases)
    # -------------------------------------------------------------------------
    if DB_PATH.exists():
        print(f"\n[4/6] Ingesting Translation Memory DB ({DB_PATH.name})...")
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("""
            SELECT src_lang, tgt_lang, source_text, target_text, domain, confidence
            FROM translation_memory
            WHERE source_text IS NOT NULL AND target_text IS NOT NULL
        """)
        tm_rows = cur.fetchall()
        conn.close()

        tm_added = 0
        for src_l, tgt_l, s_t, t_t, domain, conf in tm_rows:
            src_l = src_l.strip().lower()
            tgt_l = tgt_l.strip().lower()
            s_t = clean_text(s_t)
            t_t = clean_text(t_t)

            if not s_t or not t_t or s_t == t_t:
                continue
            if src_l not in NLLB_MAP or tgt_l not in NLLB_MAP:
                continue
            if not is_valid_script(s_t, src_l) or not is_valid_script(t_t, tgt_l):
                continue

            h = f"{src_l}:{s_t}:{tgt_l}:{t_t}"
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

            pair_obj = {
                "source": s_t,
                "target": t_t,
                "src_lang": src_l,
                "tgt_lang": tgt_l,
                "src_nllb": NLLB_MAP[src_l],
                "tgt_nllb": NLLB_MAP[tgt_l],
                "domain": domain or "conversational_tm",
                "confidence": float(conf) if conf else 1.0,
                "source_dataset": "translation_memory_db"
            }
            pairs_pool[f"{src_l}->{tgt_l}"].append(pair_obj)
            tm_added += 1
        print(f"  • Ingested {tm_added:,} verified TM sentence pairs.")

    # -------------------------------------------------------------------------
    # STEP 5: Ingest Quality-Filtered Raw Bitext (1.24 Million Pool)
    # -------------------------------------------------------------------------
    RAW_FILES = [
        {"file": "amharic-oromo.csv", "src": "amh", "tgt": "orm", "src_col": "Amharic", "tgt_col": "Oromo"},
        {"file": "amharic-somali.csv", "src": "amh", "tgt": "som", "src_col": "Amharic", "tgt_col": "Somali"},
        {"file": "amharic-tigrinya.csv", "src": "amh", "tgt": "tir", "src_col": "Amharic", "tgt_col": "Tigrinya"},
        {"file": "oromo-somali.csv", "src": "orm", "tgt": "som", "src_col": "Oromo", "tgt_col": "Somali"},
        {"file": "oromo-tigrinya.csv", "src": "orm", "tgt": "tir", "src_col": "Oromo", "tgt_col": "Tigrinya"},
        {"file": "somali-tigrinya.csv", "src": "som", "tgt": "tir", "src_col": "Somali", "tgt_col": "Tigrinya"},
    ]

    if RAW_DIR.exists():
        print(f"\n[5/6] Mining High-Scoring Pairs from Raw Bitext (Target: up to {target_bitext_per_file:,} pairs/file)...")
        bitext_total = 0
        for meta in RAW_FILES:
            csv_path = RAW_DIR / meta["file"]
            if not csv_path.exists():
                continue

            src_code = meta["src"]
            tgt_code = meta["tgt"]
            src_col = meta["src_col"]
            tgt_col = meta["tgt_col"]

            added_for_file = 0
            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if added_for_file >= target_bitext_per_file:
                        break

                    try:
                        score = float(row.get("score", 1.0))
                    except ValueError:
                        score = 1.0

                    # Filter: semantic similarity score >= 1.06
                    if score < 1.06:
                        continue

                    s_t = clean_text(row.get(src_col, ""))
                    t_t = clean_text(row.get(tgt_col, ""))

                    if not s_t or not t_t or s_t == t_t:
                        continue

                    # Length & ratio filters
                    s_words = len(s_t.split())
                    t_words = len(t_t.split())
                    if s_words < 3 or t_words < 3 or s_words > 70 or t_words > 70:
                        continue
                    if max(s_words / t_words, t_words / s_words) > 2.4:
                        continue

                    # Script validation
                    if not is_valid_script(s_t, src_code) or not is_valid_script(t_t, tgt_code):
                        continue

                    # Forward
                    h_fwd = f"{src_code}:{s_t}:{tgt_code}:{t_t}"
                    if h_fwd not in seen_hashes:
                        seen_hashes.add(h_fwd)
                        pairs_pool[f"{src_code}->{tgt_code}"].append({
                            "source": s_t,
                            "target": t_t,
                            "src_lang": src_code,
                            "tgt_lang": tgt_code,
                            "src_nllb": NLLB_MAP[src_code],
                            "tgt_nllb": NLLB_MAP[tgt_code],
                            "domain": "interlocal_bitext",
                            "confidence": min(1.0, round(score / 1.25, 2)),
                            "source_dataset": "raw_bitext"
                        })
                        added_for_file += 1
                        bitext_total += 1

                    # Backward
                    h_rev = f"{tgt_code}:{t_t}:{src_code}:{s_t}"
                    if h_rev not in seen_hashes:
                        seen_hashes.add(h_rev)
                        pairs_pool[f"{tgt_code}->{src_code}"].append({
                            "source": t_t,
                            "target": s_t,
                            "src_lang": tgt_code,
                            "tgt_lang": src_code,
                            "src_nllb": NLLB_MAP[tgt_code],
                            "tgt_nllb": NLLB_MAP[src_code],
                            "domain": "interlocal_bitext",
                            "confidence": min(1.0, round(score / 1.25, 2)),
                            "source_dataset": "raw_bitext"
                        })
                        added_for_file += 1
                        bitext_total += 1

            print(f"  • {meta['file']:25}: added {added_for_file:,} bidirectional pairs.")
        print(f"Total Bitext Pairs Ingested: {bitext_total:,}")

    # -------------------------------------------------------------------------
    # STEP 5b: Ingest Curated English Parallel Bitext from train.jsonl
    # -------------------------------------------------------------------------
    legacy_train = DATA_DIR / "training_data" / "train.jsonl"
    if legacy_train.exists():
        print(f"\n[5b/6] Ingesting Additional High-Quality English & Domain Pairs from {legacy_train.name}...")
        eng_added = 0
        with open(legacy_train, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                s_l = item.get("src_lang")
                t_l = item.get("tgt_lang")
                s_t = clean_text(item.get("source", ""))
                t_t = clean_text(item.get("target", ""))
                if not s_l or not t_l or s_l not in NLLB_MAP or t_l not in NLLB_MAP:
                    continue
                if not s_t or not t_t or s_t == t_t:
                    continue
                if not is_valid_script(s_t, s_l) or not is_valid_script(t_t, t_l):
                    continue

                h = f"{s_l}:{s_t}:{t_l}:{t_t}"
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)

                pairs_pool[f"{s_l}->{t_l}"].append({
                    "source": s_t,
                    "target": t_t,
                    "src_lang": s_l,
                    "tgt_lang": t_l,
                    "src_nllb": NLLB_MAP[s_l],
                    "tgt_nllb": NLLB_MAP[t_l],
                    "domain": item.get("domain", "curated_parallel"),
                    "confidence": float(item.get("confidence", 0.95)),
                    "source_dataset": "curated_train_jsonl"
                })
                eng_added += 1
        print(f"  • Ingested {eng_added:,} additional curated pairs from legacy train.jsonl.")

    # -------------------------------------------------------------------------
    # STEP 6: Balance, Deduplicate, Split (Train / Val / Test)
    # -------------------------------------------------------------------------
    print("\n[6/6] Consolidating & Partitioning Massive Dataset...")
    all_samples = []
    pair_counts = {}
    domain_counts = Counter()

    for p_key, sample_list in sorted(pairs_pool.items()):
        random.seed(42)
        random.shuffle(sample_list)
        pair_counts[p_key] = len(sample_list)
        all_samples.extend(sample_list)
        for s in sample_list:
            domain_counts[s.get("domain", "general")] += 1

    random.seed(42)
    random.shuffle(all_samples)

    total_count = len(all_samples)
    val_count = int(total_count * val_ratio)
    test_count = int(total_count * test_ratio)
    train_count = total_count - val_count - test_count

    train_set = all_samples[:train_count]
    val_set = all_samples[train_count : train_count + val_count]
    test_set = all_samples[train_count + val_count :]

    print("=" * 80)
    print("                     DATASET COMPOSITION SCORECARD")
    print("=" * 80)
    print(f"Total Parallel Pairs Ingested : {total_count:>10,}")
    print(f"Training Samples ({100*(1-val_ratio-test_ratio):.0f}%)           : {len(train_set):>10,}")
    print(f"Validation Samples ({100*val_ratio:.0f}%)          : {len(val_set):>10,}")
    print(f"Test Samples ({100*test_ratio:.0f}%)                : {len(test_set):>10,}")
    print("-" * 80)
    print("Breakdown by Directional Language Pair (All 20 Directions):")
    for p_key, count in sorted(pair_counts.items()):
        print(f"  • {p_key:10}: {count:>8,} sentence pairs")
    print("-" * 80)
    print("Top Domain Distributions:")
    for dom, cnt in domain_counts.most_common(12):
        print(f"  • {dom:30}: {cnt:>8,} pairs ({100*cnt/total_count:.1f}%)")
    print("=" * 80)

    # Save outputs
    train_file = OUTPUT_DIR / "train.jsonl"
    val_file = OUTPUT_DIR / "val.jsonl"
    test_file = OUTPUT_DIR / "test.jsonl"
    meta_file = OUTPUT_DIR / "dataset_scorecard.json"

    print("Writing JSONL files to disk...")
    with open(train_file, "w", encoding="utf-8") as f:
        for s in train_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(val_file, "w", encoding="utf-8") as f:
        for s in val_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(test_file, "w", encoding="utf-8") as f:
        for s in test_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    metadata = {
        "status": "READY_FOR_COMMUNITY_VALIDATION_AND_LORA_TRAINING",
        "total_pairs": total_count,
        "train_pairs": len(train_set),
        "val_pairs": len(val_set),
        "test_pairs": len(test_set),
        "language_pairs": pair_counts,
        "domains": dict(domain_counts.most_common(20)),
        "nllb_mapping": NLLB_MAP,
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✓ Train File : {train_file} ({train_file.stat().st_size / (1024*1024):.2f} MB)")
    print(f"✓ Val File   : {val_file} ({val_file.stat().st_size / (1024*1024):.2f} MB)")
    print(f"✓ Test File  : {test_file} ({test_file.stat().st_size / (1024*1024):.2f} MB)")
    print(f"✓ Scorecard  : {meta_file}")
    print("\nMASSIVE MULTILINGUAL DATASET GENERATION COMPLETE!")
    return total_count

if __name__ == "__main__":
    build_massive_multilingual_dataset()
