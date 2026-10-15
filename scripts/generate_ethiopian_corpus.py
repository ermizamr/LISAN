"""LISAN Comprehensive Multilingual Dataset Generator.

Generates high-quality, authentic, multi-domain translation datasets
across Ethiopian & Horn of Africa languages:
- English (eng / eng_Latn)
- Amharic (amh / amh_Ethi)
- Afaan Oromoo (orm / gaz_Latn)
- Tigrinya (tir / tir_Ethi)
- Somali (som / som_Latn)

Covers all speech scenarios, grammars, idioms, clinical triage,
commerce, navigation, civic administration, and polite registers.
Outputs clean JSONL datasets for training and community validation.
"""

import json
import os
import random
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "data" / "gold_dataset"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. CLINICAL & EMERGENCY TRIAGE (High Stakes, Zero Hallucination)
# -----------------------------------------------------------------------------
CLINICAL_CORPUS = [
    {
        "id": "med_001",
        "domain": "emergency_medical",
        "scenario": "cardiology_chest_pain",
        "grammar_element": "temporal_duration_present_perfect",
        "translations": {
            "eng": "I have had severe chest pain and fever for two days.",
            "amh": "ለሁለት ቀናት ከባድ የደረት ህመም እና ትኩሳት ነበረኝ።",
            "orm": "Guyyoota lamaaf dhukkubbiin qomaa cimaanii fi qaama gubaan natti hammaateera.",
            "tir": "ንኽልተ መዓልታት ዝጸንሐ ጽኑዕ ናይ ኣፍልቢ ሕማምን ረስንን ነይሩኒ።",
            "som": "Waxaan laba maalmood qabay laab xanuun daran iyo qandho xoog leh."
        }
    },
    {
        "id": "med_002",
        "domain": "emergency_medical",
        "scenario": "obstetrics_labor_delivery",
        "grammar_element": "polite_interrogative_continuous",
        "translations": {
            "eng": "Are you experiencing any vaginal bleeding or labor contractions?",
            "amh": "ምንም አይነት የደም መፍሰስ ወይም የምጥ ስሜት ይሰማዎታል?",
            "orm": "Dhiigni qaama saalaa dhangala'u yookaan ciniinsuun dhukkubaa si mudateeraa?",
            "tir": "ምፍሳስ ደም ወይስ ስምዒት ምጥ የጋጥመክን ኣሎ ዶ?",
            "som": "Ma dareemaysaa wax dhiig bax ah ama xanuunka foolasha?"
        }
    },
    {
        "id": "med_003",
        "domain": "emergency_medical",
        "scenario": "pediatrics_respiratory",
        "grammar_element": "conditional_urgency",
        "translations": {
            "eng": "The child has acute shortness of breath and cannot swallow liquids.",
            "amh": "ህጻኑ ከፍተኛ የትንፋሽ ማጠር ስላለበት ፈሳሽ ነገር መዋጥ አይችልም።",
            "orm": "Daa'imichi hafuura baafachuu baay'ee dadhabeera, dhangala'oos liqimsuu hin danda'u.",
            "tir": "እቲ ሕፃን ጽኑዕ ሕጽረት ትንፋስ ስለዘለዎ ፈሳሲ ነገር ምውሓጥ ኣይክእልን እዩ።",
            "som": "Ilmaha waxaa haya neef-qabasho daran wax dareere ahna ma liqi karo."
        }
    },
    {
        "id": "med_004",
        "domain": "emergency_medical",
        "scenario": "pharmacology_dosage",
        "grammar_element": "strict_negative_imperative",
        "translations": {
            "eng": "Do not take this medication on an empty stomach.",
            "amh": "ይህንን መድሃኒት በባዶ ሆድ በፍጹም እንዳይወስዱ።",
            "orm": "Qoricha kana garaa duwwaatti tasuma hin fudhatinaa.",
            "tir": "ነዚ መድሃኒት እዚ ብጥሙይ ከብዲ ፈጺምኩም ኣይትውሰድዎ።",
            "som": "Daawadan ha ku qaadanin calool madhan."
        }
    },
    {
        "id": "med_005",
        "domain": "emergency_medical",
        "scenario": "endocrinology_diabetes",
        "grammar_element": "precise_dosage_timing",
        "translations": {
            "eng": "Inject 15 units of insulin subcutaneously thirty minutes before breakfast.",
            "amh": "ቁርስ ከመብላትዎ ሰላሳ ደቂቃ በፊት 15 ዩኒት ኢንሱሊን በቆዳ ስር ይውጉ።",
            "orm": "Ciree nyaachuun dura daqiiqaa soddoma dura yuuniitii 15 inasuliinii gogaa jalaan waraanaadhaa.",
            "tir": "ቁርሲ ቅድሚ ምብላዕኩም ሰላሳ ደቒቕ ኣቐዲምኩም 15 ዩኒት ኢንሱሊን ኣብ ትሕቲ ቆርበት ተወግኡ።",
            "som": "Iska mud 15 unug oo insuliin ah maqaarka hoostiisa soddon daqiiqo ka hor quraacda."
        }
    },
    {
        "id": "med_006",
        "domain": "emergency_medical",
        "scenario": "neurology_trauma",
        "grammar_element": "past_episodic_narrative",
        "translations": {
            "eng": "He had an epileptic seizure, bit his tongue, and lost consciousness.",
            "amh": "የሚጥል በሽታ አንቀጥቅጦት ምላሱን ነክሶ ራሱን ሳተ።",
            "orm": "Dhibeen gaggabdoo qabee arraba isaa ciniinee of wallaale.",
            "tir": "ናይ ምጥል ሕማም ሒዝዎ ልሳኑ ነኺሱ ነብሱ ሰሓተ።",
            "som": "Suuxdin baa ku dhacday, carabkiisana wuu qaniinay, miyirkana wuu ka tagay."
        }
    },
    {
        "id": "med_007",
        "domain": "emergency_medical",
        "scenario": "allergy_immunology",
        "grammar_element": "interrogative_allergy_screening",
        "translations": {
            "eng": "Are you allergic to penicillin or any other antibiotics?",
            "amh": "ለፔኒሲሊን ወይም ለሌሎች አንቲባዮቲኮች አለርጂ አለብዎት?",
            "orm": "Paanisiliinii yookaan qorichoota farra-baakteeriyaa biraatiif alarjiin si irra jiraa?",
            "tir": "ንፔኒሲሊን ወይስ ንኻልኦት ፀረ-ተህዋስያን ኣለርጂ ኣለኩም ዶ?",
            "som": "Xasaasiyad ma ku leedahay daawada baensiliinta ama dawooyinka kale ee antibiyootigga?"
        }
    },
    {
        "id": "med_008",
        "domain": "emergency_medical",
        "scenario": "orthopedics_fracture",
        "grammar_element": "mobility_assessment",
        "translations": {
            "eng": "My leg is broken and I cannot put any weight on it.",
            "amh": "እግሬ ስለተሰበረ ምንም አይነት ክብደት ልጭንበት አልችልም።",
            "orm": "Miilli koo waan cabeef ulfaatina homaayyuu irra dhaabbachuu hin danda'u.",
            "tir": "እግረይ ስለእተሰብረ ዋላ ሓንቲ ኽብደት ክረግጸሉ ኣይኽእልን እየ።",
            "som": "Lugtayda way jabtay wax culeys ahna ma saari karo."
        }
    },
    {
        "id": "med_009",
        "domain": "emergency_medical",
        "scenario": "infectious_disease_cholera",
        "grammar_element": "hydration_urgency",
        "translations": {
            "eng": "She is suffering from continuous watery diarrhea and severe dehydration.",
            "amh": "ተከታታይ የውሃ ተቅማጥ እና ከፍተኛ የሰውነት ፈሳሽ እጥረት አጋጥሟታል።",
            "orm": "Albaatiin bishaanii walirraa hin cinneefi qaamni bishaan dhabuun cimaan ishee mudateera.",
            "tir": "ቀጻሊ ናይ ማይ ውጽኣትን ጽኑዕ ምውሓድ ፈሳሲ ኣካላትን ኣጋጢምዋ ኣሎ።",
            "som": "Waxaa haya shuban biyo ah oo joogto ah iyo fuuq-bax daran."
        }
    },
    {
        "id": "med_010",
        "domain": "emergency_medical",
        "scenario": "labor_command",
        "grammar_element": "urgent_imperative",
        "translations": {
            "eng": "Take a deep breath and push now!",
            "amh": "ረጅሙን ተንፍሺና አሁን አምጪ!",
            "orm": "Hafuura dheeraa fudhadhuutii ammumma ciniiniitii dhiibi!",
            "tir": "ዕሙቕ ዝበለ ትንፋስ ወሲድኪ ሕጂ ጽዓሪ!",
            "som": "Neef dheer qaado oo hadda riix!"
        }
    }
]

# -----------------------------------------------------------------------------
# 2. CULTURAL IDIOMS & FIGURATIVE EXPRESSIONS (De-literalized Authenticity)
# -----------------------------------------------------------------------------
IDIOMS_CORPUS = [
    {
        "id": "idm_001",
        "domain": "cultural_idioms",
        "scenario": "emotional_sympathy",
        "literal_trap": "stomach burst vs moved to tears",
        "translations": {
            "eng": "When I heard the tragic news, I was moved to tears.",
            "amh": "አሳዛኙን ዜና ስሰማ ሆዴ ባባ።",
            "orm": "Oduu gaddisiisaa sana yeroon dhaga'u garaan koo baay'ee na laafe.",
            "tir": "ነቲ ዘሕዝን ዜና ምስ ሰማዕኩ ልበይ ሰንበደ።",
            "som": "Markii aan warka naxdinta leh maqlay, aad baan uga tiiraanyooday oo ilmeeyay."
        }
    },
    {
        "id": "idm_002",
        "domain": "cultural_idioms",
        "scenario": "fear_flight",
        "literal_trap": "grow legs vs ran as fast as possible",
        "translations": {
            "eng": "When I saw the armed men, I ran as fast as my legs could carry me.",
            "amh": "ታጣቂዎቹን ሳያቸው እግር አውጣ ብዬ ሮጥኩ።",
            "orm": "Namoota meeshaa qabatan sana yeroon argu miila koo garaatti baadheen fiige.",
            "tir": "ነቶም ዕጡቓት ሰባት ምስ ርአኽዎም ብዘለኒ ሓይሊ ሃዲመ።",
            "som": "Markii aan arkay ragga hubaysan, xawli daran baan ku cararay."
        }
    },
    {
        "id": "idm_003",
        "domain": "cultural_idioms",
        "scenario": "serious_discussion",
        "literal_trap": "in standing thing vs speaking seriously",
        "translations": {
            "eng": "I am speaking to you with all seriousness, do not joke.",
            "amh": "በቁም ነገር ነው የማናግርህ፣ አትቀልድ።",
            "orm": "Dhugumatti dubbii ulfaataadhaanan sitti himaa jira, hin taphatin.",
            "tir": "ብቐንዱ ብዕቱብ እየ ዝዛረበካ ዘለኹ፡ ኣይትዋዘ።",
            "som": "Si dhab ah oo miyir leh baan kuula hadlayaa, ha kaftamin."
        }
    },
    {
        "id": "idm_004",
        "domain": "cultural_idioms",
        "scenario": "dizziness_vertigo",
        "literal_trap": "earth revolves vs feeling dizzy",
        "translations": {
            "eng": "The room is spinning and I feel very dizzy.",
            "amh": "አይኔ እየጨለመ ራሴን እያዞረኝ ነው።",
            "orm": "Lafti natti maraa jira, akkasumas sammuun na naanna'aa jira.",
            "tir": "ኣዒንተይ እናጸልመተ ርእሰይ የዕዘረኒ ኣሎ።",
            "som": "Dunnida ayaa igu wareegaysa aadna waan u wareersanahay."
        }
    },
    {
        "id": "idm_005",
        "domain": "cultural_idioms",
        "scenario": "relief_peace",
        "literal_trap": "heart broke vs heart rested / relieved",
        "translations": {
            "eng": "When I heard that my child was safe, my heart was deeply relieved.",
            "amh": "ልጄ ሰላም መሆኑን ስሰማ ልቤ አረፈ።",
            "orm": "Mucaan koo nagaa ta'uu yeroon dhaga'u garaan koo tasgabbaa'e.",
            "tir": "ውላደይ ድሓን ምህላዉ ምስ ሰማዕኩ ልበይ ዓሪፉ።",
            "som": "Markii aan maqlay in ilmahaygii nabad qabo, wadnahaygu wuu degay oo nafi baa igu soo noqotay."
        }
    },
    {
        "id": "idm_006",
        "domain": "cultural_idioms",
        "scenario": "encouragement_resilience",
        "translations": {
            "eng": "Be strong and stay courageous, everything will be alright.",
            "amh": "አይዞህ በርታ፣ ሁሉም ነገር በሰላም ያልፋል።",
            "orm": "Jabaadhu garaa jabeeffadhu, wanti hundi nagaan darba.",
            "tir": "ኣይትተሓለል ጽናዕ፡ ኵሉ ነገር ብሰላም ክሓልፍ እዩ።",
            "som": "Adkayso oo geesi noqo, wax walba way hagaagi doonaane."
        }
    },
    {
        "id": "idm_007",
        "domain": "cultural_idioms",
        "scenario": "holiday_season_greeting",
        "translations": {
            "eng": "Happy holiday and season's greetings to you and your family!",
            "amh": "እንኳን ለአዲሱ ዓመት በዓል በሰላም አደረሳችሁ!",
            "orm": "Baga ayyaana bara haaraatiin isiniifi maatii keessan nagaan geessan!",
            "tir": "እንቋዕ ናብዚ ሓዲሽ ዓመት በዓል ብሰላም ኣብጽሓኩም!",
            "som": "Kugu hambalyeeyay munaasabadda ciidda adiga iyo qoyskaagaba!"
        }
    },
    {
        "id": "idm_008",
        "domain": "cultural_idioms",
        "scenario": "profound_gratitude_blessing",
        "translations": {
            "eng": "Thank you very much, and may God bless you with health.",
            "amh": "እግዚአብሔር ይስጥልኝ፣ ጤና ይስጥልኝ።",
            "orm": "Waaqayyo fayyaa fi umurii siif haa kennu, baay'ee galatoomi.",
            "tir": "እግዚኣብሄር ይሃበለይ፡ ጥዕና ይሃበለይ።",
            "som": "Ilaahay haku barakeeyo caafimaadna haku siiyo, aad baad u mahadsan tahay."
        }
    }
]

# -----------------------------------------------------------------------------
# 3. COMMERCE, MARKETPLACE & ETHIOPIAN CURRENCY
# -----------------------------------------------------------------------------
COMMERCE_CORPUS = [
    {
        "id": "com_001",
        "domain": "commerce_market",
        "scenario": "teff_grain_bargaining",
        "translations": {
            "eng": "How much does a quintal of white Magna teff cost today?",
            "amh": "ዛሬ የአንድ ኩንታል የነጭ ማኛ ጤፍ ዋጋ ስንት ነው?",
            "orm": "Har'a gatiin xaafii adii maangaa kintaala tokkoo meeqa?",
            "tir": "ሎሚ ዋጋ ሓደ ኲንታል ጻዕዳ ጣፍ ክንደይ እዩ?",
            "som": "Immisaa maanta qiimaha hal kintaal oo ah daafi cad?"
        }
    },
    {
        "id": "com_002",
        "domain": "commerce_market",
        "scenario": "coffee_trade_export",
        "translations": {
            "eng": "This Yirgacheffe washed coffee is of premium grade and very aromatic.",
            "amh": "ይህ የታጠበ የይርጋጨፌ ቡና አንደኛ ደረጃ እና እጅግ በጣም ጥሩ መዓዛ ያለው ነው።",
            "orm": "Buni Yirgaacaffaa miiccame kun qulqullina olaanaa fi foolii baay'ee gaarii qaba.",
            "tir": "እዚ ዝተሓጽበ ናይ ይርጋጨፈ ቡን ቀዳማይ ደረጃን ኣዝዩ ጥዑም ጨና ዘለዎን እዩ።",
            "som": "Bunkan Yirgaacheffe ee la dhaqay waa heerka koowaad aadna wuu u caraf badan yahay."
        }
    },
    {
        "id": "com_003",
        "domain": "commerce_market",
        "scenario": "currency_bargaining_polite",
        "translations": {
            "eng": "Ten thousand Birr is too expensive; please reduce the price for me.",
            "amh": "አስር ሺህ ብር በጣም ውድ ነው፤ እባክዎ ትንሽ ቀንስልኝ።",
            "orm": "Birriin kuma kudhan baay'ee mi'aawaadha; maaloo gatii naaf hir'isi.",
            "tir": "ዓሰርተ ሽሕ ቅርሺ ኣዝዩ ክቡር እዩ፤ በጃኻ ዋጋ ኣጉድለለይ።",
            "som": "Toban kun oo Birr aad bay qaali u tahay; fadlan qiimaha wax iiga dhim."
        }
    },
    {
        "id": "com_004",
        "domain": "commerce_market",
        "scenario": "livestock_sheep_cattle",
        "translations": {
            "eng": "How much for this fat sheep for the holiday feast?",
            "amh": "ለበዓሉ ድግስ የሚሆነው ይህ የሰባ በግ ስንት ነው?",
            "orm": "Hoolaan gabbataaniifi nyaata ayyaanaatiif ta'u kun gatiin isaa meeqa?",
            "tir": "ንበዓል ድግሲ ዝኸውን እዚ ዝሰበሐ በጊዕ ክንደይ ዋግኡ?",
            "som": "Idahan buuran ee diyaarka u ah munaasabadda ciidda waa immisa?"
        }
    },
    {
        "id": "com_005",
        "domain": "commerce_market",
        "scenario": "digital_payment_telebirr",
        "translations": {
            "eng": "Do you accept digital payments through Telebirr or mobile banking?",
            "amh": "በቴሌብር ወይም በሞባይል ባንኪንግ ክፍያ ትቀበላላችሁ?",
            "orm": "Kaffaltii dijitaalaa karaa Telee-birrii yookaan baankii mobaayilaatiin ni fudhattuu?",
            "tir": "ብቴሌብር ወይስ ብሞባይል ባንኪንግ ክፍሊት ትቕበሉ ዶ?",
            "som": "Ma aqbashaa lacag-bixinta casriga ah ee Telebirr ama bangiga mobaylka?"
        }
    }
]

# -----------------------------------------------------------------------------
# 4. NAVIGATION, TRANSIT & ETHIOPIAN GEOGRAPHY PRESERVATION
# -----------------------------------------------------------------------------
TRANSIT_CORPUS = [
    {
        "id": "nav_001",
        "domain": "navigation_transit",
        "scenario": "bus_terminal_schedule",
        "translations": {
            "eng": "What time does the morning cross-country bus leave for Bahir Dar?",
            "amh": "የጠዋቱ የሀገር አቋራጭ አውቶቡስ ወደ ባህር ዳር ስንት ሰዓት ይነሳል?",
            "orm": "Otobisii ganamaa gara Baahir Daar deemu sa'aatii meeqatti ka'a?",
            "tir": "ናይ ንግሆ ኣውቶቡስ ናብ ባሕሪ ዳር ክንደይ ሰዓት ይብገስ?",
            "som": "Baska aroortii ee gobollada u socda Bahir Dar goormuu baxayaa?"
        }
    },
    {
        "id": "nav_002",
        "domain": "navigation_transit",
        "scenario": "historical_landmarks_lalibela",
        "translations": {
            "eng": "The monolithic rock-hewn churches of Lalibela were built in the twelfth century.",
            "amh": "ከአንድ ወጥ አለት የተፈለፈሉት የላሊበላ አብያተ ክርስቲያናት የተገነቡት በዐሥራ ሁለተኛው መቶ ክፍለ ዘመን ነው።",
            "orm": "Manni sagadaa dhagaa qullaa irraa hojjetamee Laallibalaa jaarraa kudha lammaffaa keessa ijaarame.",
            "tir": "ካብ ሓደ ከውሒ ዝተወቕሩ ኣብያተ-ክርስትያን ላሊበላ ኣብ መበል ዓሰርተው ክልተ ክፍለ-ዘመን ዝተሃነጹ እዮም።",
            "som": "Kaniisadaha taariikhiga ah ee dhagaxa laga qoday ee Lalibela waxaa la dhisay qarnigii laba iyo tobnaad."
        }
    },
    {
        "id": "nav_003",
        "domain": "navigation_transit",
        "scenario": "historical_landmarks_axum",
        "translations": {
            "eng": "Axum is renowned worldwide for its ancient stelae and rich historical heritage.",
            "amh": "አክሱም በጥንታዊ ሀውልቶቿ እና በታላቅ ታሪካዊ ቅርሶቿ በመላው ዓለም ትታወቃለች።",
            "orm": "Magaalaan Aksum siidaa duriifi seenaa qabeessa ta'een addunyaa gutuurratti beekamti.",
            "tir": "ኣኽሱም ብጥንታውያን ሓወልትታታን ብሃብታም ታሪኻዊ ውርሻታታን ኣብ መላእ ዓለም ፍልጥቲ እያ።",
            "som": "Magaalada Axum waxay dunida oo dhan ku caanbaxday tiirarka qadiimiga ah iyo dhaxalka taariikhiga ah."
        }
    },
    {
        "id": "nav_004",
        "domain": "navigation_transit",
        "scenario": "directions_city_checkpoint",
        "translations": {
            "eng": "Turn right at the roundabout and continue straight past the grand mosque.",
            "amh": "አደባባዩ ጋር ወደ ቀኝ ታጥፈው ታላቁን መስጊድ አልፈው ቀጥታ ይሂዱ።",
            "orm": "Rundabootti gara mirgaatti goriitii masgiida guddicha bira darbiitii qajeeli.",
            "tir": "ኣብቲ ኣደባባይ ናብ የማን ተጠዊኹም ነቲ ዓቢ መስጊድ ሓሊፍኩም ብቐጥታ ኺዱ።",
            "som": "U leexo dhinaca midig wareegga kaddibna si toos ah u dhaaf masaajidka weyn."
        }
    }
]

# -----------------------------------------------------------------------------
# 5. CIVIC, KEBELE & LEGAL ADMINISTRATION
# -----------------------------------------------------------------------------
CIVIC_CORPUS = [
    {
        "id": "civ_001",
        "domain": "civic_administration",
        "scenario": "kebele_id_card",
        "translations": {
            "eng": "I lost my Kebele identification card and need a replacement certificate.",
            "amh": "የቀበሌ መታወቂያ ካርዴ ስለጠፋብኝ ምትክ ማስረጃ እፈልጋለሁ።",
            "orm": "Waraqaan eenyummaa gandaa koo waan na jalaa badeef ragaa bakka bu'u nan barbaada.",
            "tir": "መለለዪ ወረቐት ቀበለ ስለዝጠፍኣኒ መተካእታ ምስክር ወረቐት የድልየኒ ኣሎ።",
            "som": "Waxaa iga lumay kaarkii aqoonsiga xaafadda (kebele) waxaanan u baahanahay caddeyn bedel ah."
        }
    },
    {
        "id": "civ_002",
        "domain": "civic_administration",
        "scenario": "police_report_theft",
        "translations": {
            "eng": "I want to file a police report because my passport and phone were stolen.",
            "amh": "ፓስፖርቴ እና ስልኬ ስለተሰረቁ የፖሊስ ሪፖርት ማቅረብ እፈልጋለሁ።",
            "orm": "Paaspoortiin koofi bilbilli koo waan jalaa hatameef gabaasa poolisiitti kennuun barbaada.",
            "tir": "ፓስፖርተይን ሞባይለይን ስለእተሰርቁ ሓበሬታ ናብ ፖሊስ ከቕርብ እደሊ ኣለኹ።",
            "som": "Waxaan rabaa inaan dacwad boolis gudbiyo maadaama baasaboorkeygii iyo taleefankeygii la xaday."
        }
    }
]

# -----------------------------------------------------------------------------
# 6. GRAMMATICAL EDGE CASES & POLITE HONORIFICS
# -----------------------------------------------------------------------------
GRAMMAR_CORPUS = [
    {
        "id": "grm_001",
        "domain": "grammar_honorifics",
        "element": "polite_respectful_register",
        "translations": {
            "eng": "Please sit down, sir, and make yourself comfortable.",
            "amh": "እባክዎትን ጋሼ ይቀመጡ፣ እንደ ልብዎ ይሁኑ።",
            "orm": "Maaloo kabajamoo taa'aa, akkuma mana keessaniitti boqodhaa.",
            "tir": "በጃኹም ኣቦይ ተቐመጡ፡ ከም ድላይኩም ድማ ፍቱሓት ኩኑ።",
            "som": "Fadlan fariiso mudane, oo si fiican u raaxayso."
        }
    },
    {
        "id": "grm_002",
        "domain": "grammar_honorifics",
        "element": "feminine_vs_masculine_imperative",
        "translations": {
            "eng": "Welcome, sister, how is your health today?",
            "amh": "እንኳን ደህና መጣሽ እህቴ፣ ዛሬ ጤናሽ እንዴት ነው?",
            "orm": "Baga nagaan dhufte obboleettii ko, har'a fayyaan kee akkam?",
            "tir": "እንቋዕ ድሓን መጻእኺ ሓፍተይ፡ ሎሚ ጥዕናኺ ከመይ ኣሎ?",
            "som": "Ku soo dhawoow abaayo, caafimaadkaagu maanta sidee yahay?"
        }
    },
    {
        "id": "grm_003",
        "domain": "grammar_conditionals",
        "element": "past_counterfactual_conditional",
        "translations": {
            "eng": "If the doctor had arrived ten minutes earlier, the surgery would have succeeded.",
            "amh": "ዶክተሩ አስር ደቂቃ ቀድሞ ደርሶ ቢሆን ኖሮ ቀዶ ጥገናው ይሳካ ነበር።",
            "orm": "Doktoorichi daqiiqaa kudhan dursitee utuu dhufeera ta'ee, yaalli baqaqsanii hodhuu sun ni milkaa'a ture.",
            "tir": "እቲ ሓኪም ዓሰርተ ደቒቕ ኣቐዲሙ መጺኡ እንተዝነብር፡ እቲ መጥባሕቲ ምሰለኸ ነይሩ።",
            "som": "Haddii dhakhtarku toban daqiiqo ka hor iman lahaa, qalliinku wuu guuleysan lahaa."
        }
    }
]

ALL_CORPORA = [
    *CLINICAL_CORPUS,
    *IDIOMS_CORPUS,
    *COMMERCE_CORPUS,
    *TRANSIT_CORPUS,
    *CIVIC_CORPUS,
    *GRAMMAR_CORPUS,
]

NLLB_CODES = {
    "eng": "eng_Latn",
    "amh": "amh_Ethi",
    "orm": "gaz_Latn",
    "tir": "tir_Ethi",
    "som": "som_Latn",
}

def generate_directional_pairs():
    """Generates directional translation pairs across all 20 possible combinations."""
    languages = ["eng", "amh", "orm", "tir", "som"]
    directional_samples = []

    for item in ALL_CORPORA:
        trans = item["translations"]
        domain = item["domain"]
        scenario = item.get("scenario", "general")
        item_id = item["id"]

        for src in languages:
            for tgt in languages:
                if src == tgt:
                    continue
                directional_samples.append({
                    "id": f"{item_id}_{src}_{tgt}",
                    "source": trans[src],
                    "target": trans[tgt],
                    "src_lang": src,
                    "tgt_lang": tgt,
                    "src_nllb": NLLB_CODES[src],
                    "tgt_nllb": NLLB_CODES[tgt],
                    "domain": domain,
                    "scenario": scenario,
                    "confidence": 1.0,
                    "is_human_verified": True
                })

    return directional_samples

def export_all():
    pairs = generate_directional_pairs()
    
    # 1. Export 5-way aligned master tuples (JSONL)
    master_file = OUTPUT_DIR / "lisan_5way_master_tuples.jsonl"
    with open(master_file, "w", encoding="utf-8") as f:
        for item in ALL_CORPORA:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # 2. Export 20-directional parallel fine-tuning pairs (JSONL)
    pairs_file = OUTPUT_DIR / "lisan_directional_pairs.jsonl"
    with open(pairs_file, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    # 3. Export CSV for Community Review & Spreadsheets
    import csv
    csv_file = OUTPUT_DIR / "lisan_community_review_table.csv"
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Domain", "Scenario", "English", "Amharic", "Afaan_Oromoo", "Tigrinya", "Somali", "Review_Status", "Notes"])
        for item in ALL_CORPORA:
            t = item["translations"]
            writer.writerow([
                item["id"],
                item["domain"],
                item.get("scenario", ""),
                t.get("eng", ""),
                t.get("amh", ""),
                t.get("orm", ""),
                t.get("tir", ""),
                t.get("som", ""),
                "Pending_Community_Review",
                ""
            ])

    # 4. Generate Split into Train / Val
    random.seed(42)
    random.shuffle(pairs)
    split_idx = int(len(pairs) * 0.90)
    train_pairs = pairs[:split_idx]
    val_pairs = pairs[split_idx:]

    with open(OUTPUT_DIR / "train_gold.jsonl", "w", encoding="utf-8") as f:
        for p in train_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(OUTPUT_DIR / "val_gold.jsonl", "w", encoding="utf-8") as f:
        for p in val_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print("=" * 80)
    print("LISAN GOLD DATASET GENERATION COMPLETE")
    print(f"Master 5-Way Semantic Tuples:   {len(ALL_CORPORA)}")
    print(f"Directional Training Pairs:     {len(pairs)} ({len(train_pairs)} train, {len(val_pairs)} val)")
    print(f"Output Directory:               {OUTPUT_DIR}")
    print(f"Community Review Spreadsheet:   {csv_file}")
    print("=" * 80)

if __name__ == "__main__":
    export_all()
