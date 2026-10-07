"""
Deep Ethiopian Conversational & Domain Dialogue Corpus Seeder for LISAN AI.

Injects human-grade, high-impact 5-way parallel dialogues across:
- Afaan Oromoo (orm)
- Amharic (amh)
- Tigrinya (tir)
- Somali (som)
- English (eng)

Domains:
1. Emergency Medical & Rural Clinic Consultations
2. Merkato & Regional Trade, Bargaining & Digital Payments (Telebirr/CBE)
3. Minibus, Taxi, Bajaj & Urban Transport Navigation
4. Kebele, Police, Civic Administration & Documentation
5. Cultural Hospitality, Coffee Ceremonies, Holidays & Entity Shielding
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai_pipeline.translation_memory import TranslationMemory

DEEP_ETHIOPIAN_CORPUS: list[dict[str, str]] = [
    # =========================================================================
    # 1. EMERGENCY MEDICAL & CLINICAL CONSULTATIONS
    # =========================================================================
    {
        "domain": "emergency_medical",
        "orm": "Daa'imni koo guyyoota sadiif ho'a qaamaa olka'aa fi qufaa cimaa qaba.",
        "amh": "ልጄ ለሦስት ቀናት ከፍተኛ ትኩሳት እና ከባድ ሳል አለበት።",
        "tir": "ወደይ/ጓለይ ንሰለስተ መዓልቲ ዝኣክል ብርቱዕ ረስኒን ከቢድ ሰዓልን ኣለዎ/ዋ።",
        "som": "Ilmahaygu wuxuu qabaa qandho daran iyo qufac culus muddo saddex maalmood ah.",
        "eng": "My child has had a high fever and a severe cough for three days.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Dawaa kana nyaata booda bishaan qulqulluun guyyaatti yeroo lama fudhadhaa.",
        "amh": "ይህን መድኃኒት ከምግብ በኋላ በቀን ሁለት ጊዜ በንፁህ ውኃ ይውሰዱ።",
        "tir": "እዚ መድሃኒት ድሕሪ ምግቢ ብንጹህ ማይ መዓልቲ ክልተ ግዜ ውሰዱ።",
        "som": "Daawadan qaado cuntada kadib laba jeer maalintii adigoo biyo nadiif ah ku cabaya.",
        "eng": "Take this medication twice a day after meals with clean water.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Dhukkubbichi gara ceekuu ykn mudhiitti ni babal'ataa mee?",
        "amh": "ሕመሙ ወደ ትከሻዎ ወይም ወደ ወገብዎ ይሰራጫል?",
        "tir": "እቲ ሕማም ናብ መንከብካ/መንከብኪ ወይ ናብ ሕቋኻ/ኺ ይላባዕ ድዩ?",
        "som": "Xanuunku ma u gudbaa garabkaaga ama dhabarkaaga?",
        "eng": "Does the pain radiate to your shoulder or your lower back?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Dhiigni baay'inaan dhangala'aa jira, hatattamaan qoricha dhiiga dhaabu barbaanna.",
        "amh": "ደሙ በከፍተኛ ሁኔታ እየፈሰሰ ነው፣ በአስቸኳይ ደም የሚያቆም መድኃኒት እንፈልጋለን።",
        "tir": "እቲ ደም ብሓይሊ ይፈስስ ኣሎ፣ ብህጹጽ ደም ደው ዘብል መድሃኒት የድልየና ኣሎ።",
        "som": "Dhiig aad u badan ayaa daadanaya, waxaan si degdeg ah ugu baahannahay daawada dhiig-joojinta.",
        "eng": "There is heavy bleeding, we urgently need medication to stop the blood.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Haati ciniinsuun itti cimeera, ambulaansii ariifachiisaa nuuf waamaa.",
        "amh": "እናቲቱ ምጥ ፀንቶባታል፣ እባካችሁ አምቡላንስ በአስቸኳይ ጥሩልን።",
        "tir": "ኣደ ሕርሲ በርቲዕዋ ኣሎ፣ በጃኹም ኣምቡላንስ ብህጹጽ ጸውዑልና።",
        "som": "Hooyada fooshii ayaa ku cuslaatay, fadlan si degdeg ah ambalaas noogu waca.",
        "eng": "The mother is in severe labor, please call an ambulance immediately.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Dhibee sukkaaraa fi dhiibbaa dhiigaa qabduu?",
        "amh": "የስኳር በሽታ ወይም የደም ግፊት አለብዎት?",
        "tir": "ናይ ሽኮር ሕማም ወይ ናይ ደም ጸቕጢ ኣለኩም ድዩ?",
        "som": "Macaan ama dhiigkar ma leedahay?",
        "eng": "Do you have diabetes or high blood pressure?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Qorichi busaa fi alarjikii asuma kilinika keessatti ni argama.",
        "amh": "የወባ እና የአለርጂ መድኃኒት እዚሁ ክሊኒክ ውስጥ ይገኛል።",
        "tir": "ናይ ዓሶን ናይ ኣለርጂን መድሃኒት ኣብዚ ክሊኒክ ይርከብ እዩ።",
        "som": "Daawada duumada iyo xasaasiyadda halkan rugta caafimaadka ayaa laga helaa.",
        "eng": "Malaria and allergy medications are available right here at the clinic.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Mee siree qorannoo irratti ciisaa, qoma keessan dhagahuun barbaada.",
        "amh": "እባክዎን በመመርመሪያው አልጋ ላይ ጋደም ይበሉ፣ ደረትዎን ማዳመጥ እፈልጋለሁ።",
        "tir": "በጃኹም ኣብ መመርመሪ ዓራት ጋደም በሉ፣ ኣፍ-ልብኹም ክሰምዕ እደሊ ኣለኹ።",
        "som": "Fadlan jiifso sariirta baaritaanka, waxaan rabaa inaan dhageysto laabtaada.",
        "eng": "Please lie down on the examination bed, I need to listen to your chest.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Dhukkubbii keessan tokko hanga kudhaniitti meeqa kennituuf?",
        "amh": "ሕመምዎን ከአንድ እስከ አስር ባለው መለኪያ ስንት ይሰጡታል?",
        "tir": "ንሕማምኩም ካብ ሓደ ክሳብ ዓሰርተ ኣብ ዘሎ መለክዒ ክንደይ ትህብዎ?",
        "som": "Xanuunkaaga cabirka koox ilaa toban inteed galinaysaa?",
        "eng": "On a scale of one to ten, how would you rate your pain?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Daa'imni kun talaallii kanaan dura fudhatee beekaa?",
        "amh": "ይህ ህፃን ከዚህ በፊት ክትባት ወስዶ ያውቃል?",
        "tir": "እዚ ህጻን ቅድሚ ሕጂ ክታበት ወሲዱ ይፈልጥ ድዩ?",
        "som": "Ilmahani horay ma u qaatay tallaallada?",
        "eng": "Has this child received any vaccinations before?",
    },

    # =========================================================================
    # 2. MERKATO & TRADE, BARGAINING, TELEBIRR & COMMERCE
    # =========================================================================
    {
        "domain": "commerce_bargaining",
        "orm": "Xaafoo Maagnaa fi Sergeenyaa kun kiiloon tokko meeqa ta'a?",
        "amh": "ይህ የማኛ እና የሰርገኛ ጤፍ አንድ ኪሎው ስንት ነው?",
        "tir": "እዚ ናይ ማኛን ሰርገኛን ጣፍ ሓደ ኪሎ ክንደይ እዩ?",
        "som": "Kiilada tefka maagna ama sergenya intee weeye?",
        "eng": "How much is one kilo of this Magna and Sergegna teff?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Gatiin kun baay'ee qaala'aadha, mee gatii dhumaa naaf godhaa.",
        "amh": "ይህ ዋጋ በጣም ውድ ነው፣ እባክዎ የመጨረሻ ዋጋ ያድርጉልኝ።",
        "tir": "እዚ ዋጋ ኣዝዩ ክቡር እዩ፣ በጃኻ ናይ መወዳእታ ዋጋ ግበረለይ።",
        "som": "Qiimahani aad buu qaali u yahay, fadlan qiimihii ugu dambeeyay iigu dhim.",
        "eng": "This price is too expensive, please give me your best final price.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Telebirriin ykn baankii daldalaa Itoophiyaan kaffaluu nan danda'aa?",
        "amh": "በቴሌብር ወይም በኢትዮጵያ ንግድ ባንክ መክፈል እችላለሁ?",
        "tir": "ብቴሌብር ወይ ብንግዲ ባንኪ ኢትዮጵያ ክኸፍል እኽእል ድየ?",
        "som": "Ma ku bixin karaa Telebirr mise Bangiga Ganacsiga Itoobiya?",
        "eng": "Can I pay using Telebirr or the Commercial Bank of Ethiopia (CBE)?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Kaffaltiin koo darbeeraa? Mee lakkoofsa herregaa fi ergaa gabaabaa ilaalaa.",
        "amh": "ክፍያዬ አልፏል? እባክዎ የሂሳብ ቁጥሩን እና አጭር የጽሑፍ መልዕክቱን ይመልከቱ።",
        "tir": "ክፍሊተይ ሓሊፉ ድዩ? በጃኹም ናይ ሒሳብ ቁጽርን ናይ ጽሑፍ መልእኽትን ርኣዩ።",
        "som": "Lacagtaydu ma gudubtay? Fadlan fiiri lambarka koontada iyo farriinta SMS-ka.",
        "eng": "Did my payment go through? Please check the account number and SMS message.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Qullubbii diimaa fi shunkurtii kana kiiloo sadii naaf madaalaa.",
        "amh": "ቀይ ሽንኩርት እና ነጭ ሽንኩርት ሦስት ኪሎ መዝነው ይስጡኝ።",
        "tir": "ቀይሕ ሽጉርትን ጻዕዳ ሽጉርትን ሰለስተ ኪሎ መዚንኩም ሃቡኒ።",
        "som": "Basasha cas iyo toonta iigu miis saddex kiilo.",
        "eng": "Weigh three kilos of red onions and garlic for me, please.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Kun qarsi dhibba shan, qarshii digdama deebii naaf kennaa.",
        "amh": "ይህ አምስት መቶ ብር ነው፣ ሃያ ብር መልስ ስጡኝ።",
        "tir": "እዚ ሓሙሽተ ሚእቲ ብር እዩ፣ ዕስራ ብር መልሲ ሃቡኒ።",
        "som": "Kani waa shan boqol oo birr, ii soo celi labaatan birr oo baaqi ah.",
        "eng": "Here is five hundred Birr, please give me twenty Birr in change.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Bunni kun kan Hararii moo kan Jimmaa fi Sidaamaati?",
        "amh": "ይህ ቡና የሐረር ነው ወይስ የጅማ እና የሲዳማ?",
        "tir": "እዚ ቡን ናይ ሓረር ድዩ ወይስ ናይ ጅማን ሲዳማን?",
        "som": "Bunkani ma kii Harar baa mise waa kii Jimma iyo Sidama?",
        "eng": "Is this coffee from Harar, or from Jimma and Sidama?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Hoolaa fi re'ee kana gabaa Finfinneetti meeqaan gurgurtu?",
        "amh": "ይህን በግና ፍየል በአዲስ አበባ ገበያ በስንት ነው የሚሸጡት?",
        "tir": "ነዚ በጊዕን ጤልን ኣብ ዕዳጋ ኣዲስ ኣበባ ብኽንደይ ትሸጥዎ ኣለኹም?",
        "som": "Idahan iyo riyahan suuqa Addis Ababa intee baad ku iibinaysaan?",
        "eng": "How much are you selling this sheep and goat for in the Addis Ababa market?",
    },

    # =========================================================================
    # 3. MINIBUS, TAXI, BAJAJ & TRANSIT NAVIGATION
    # =========================================================================
    {
        "domain": "navigation_directions",
        "orm": "Woyyaalaa! Taaksiin kun gara Boolee, Meeksikoo moo Maganaanyaa deema?",
        "amh": "ወያላ! ይህ ታክሲ ወደ ቦሌ፣ ሜክሲኮ ወይስ መገናኛ ነው የሚሄደው?",
        "tir": "ወያላ! እዚ ታክሲ ናብ ቦሌ፣ ሜክሲኮ ወይስ መገናኛ እዩ ዝኸይድ ዘሎ?",
        "som": "Wayaale! Tagsigani ma wuxuu aadayaa Bole, Mexico mise Megenagna?",
        "eng": "Conductor! Is this taxi heading to Bole, Mexico, or Megenagna?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Mee naannoo ifaa tiraafikaa ykn boba'aa sanatti na buusaa.",
        "amh": "እባክዎን የትራፊክ መብራቱ ወይም ማደያው አካባቢ አውርዱኝ።",
        "tir": "በጃኹም ኣብቲ መብራህቲ ትራፊክ ወይ መዕደሊ ነዳዲ ኣውርዱኒ።",
        "som": "Fadlan igu daji meesha layrka taraafikada ama kaalinta shidaalka.",
        "eng": "Please drop me off near the traffic lights or the gas station.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Bajajii kanaan gara buufata xiyyaaraa ykn buufata baaburaatti deemuun meeqa?",
        "amh": "በዚህ ባጃጅ ወደ አየር ማረፊያ ወይም ባቡር ጣቢያ ለመሄድ ስንት ነው?",
        "tir": "በዚ ባጃጅ ናብ መዕርፎ ነፈርቲ ወይ መደበር ባቡር ንምኻድ ክንደይ እዩ?",
        "som": "Bajaajtan intee bay ku geynaysaa garoonka diyaaradaha ama saldhigga tareenka?",
        "eng": "How much is it to go to the airport or train station by this Bajaj?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Konkolaataan kun Piyaasaa, Kaazaanchiis fi Qirqoos qaxxaamuraa?",
        "amh": "ይህ መኪና ፒያሳ፣ ካዛንቺስ እና ቂርቆስን ያቋርጣል?",
        "tir": "እዚ መኪና ፒያሳ፣ ካዛንቺስን ቂርቆስን የቋርጽ ድዩ?",
        "som": "Gaarigani ma dhex maraa Piazza, Kazanchis iyo Kirkos?",
        "eng": "Does this car pass through Piazza, Kazanchis, and Kirkos?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Karaa qaxxaamuraa kana qabadhaatii gara mirgaatti dacha'aa.",
        "amh": "ይህን አቋራጭ መንገድ ይዘው ወደ ቀኝ ይታጠፉ።",
        "tir": "ነዚ ኣቋራጭ መንገዲ ሒዝኩም ናብ የማን ተጠወዩ።",
        "som": "Qaad jidkan tooska ah oo u leexo dhanka midig.",
        "eng": "Take this shortcut road and turn right.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Buufanni otoobisii goolaba magaalaa Adamaa fi Hawaasaa eessa jira?",
        "amh": "የአዳማ እና የሐዋሳ የረጅም ርቀት አውቶቡስ መነኸሪያ የት ነው የሚገኘው?",
        "tir": "ናይ ኣዳማን ሓዋሳን ናይ ነዊሕ ርሕቀት መኪና መበገሲ ኣበይ ይርከብ?",
        "som": "Xaggee ku yaallaa xarunta basaska ee aada magaalooyinka Adama iyo Hawassa?",
        "eng": "Where is the long-distance bus station for Adama and Hawassa located?",
    },

    # =========================================================================
    # 4. KEBELE, CIVIC ADMINISTRATION, POLICE & ID REGISTRATION
    # =========================================================================
    {
        "domain": "civic_administration",
        "orm": "Waraqaa eenyummaa gandaa koo haaromsuuf uunkaa kam guutuun qaba?",
        "amh": "የቀበሌ የቀበሌ መታወቂያዬን ለማደስ የትኛውን ቅጽ መሙላት አለብኝ?",
        "tir": "ናይ ቐበሌ መንነት ወረቐተይ ንምሕዳስ ኣየናይ ቅጥዒ ክመልእ ኣለኒ?",
        "som": "Waa kuwee foomamka aan u baahanahay inaan buuxiyo si aan u cusboonaysiiyo aqoonsiga xaafadda?",
        "eng": "Which form do I need to fill out to renew my Kebele resident ID card?",
    },
    {
        "domain": "civic_administration",
        "orm": "Suuraa gabaabaa fi ragaa dhalootaa qabadhaatii boru ganama koottaa.",
        "amh": "ፓስፖርት ሳይዝ ፎቶግራፍ እና የልደት ምስክር ወረቀት ይዘው ነገ ጠዋት ይምጡ።",
        "tir": "ናይ ፓስፖርት ዓቐን ዘለዎ ፎቶግራፍን ናይ ልደት ወረቐት ምስክርን ሒዝኩም ጽባሕ ንግሆ ምጹ።",
        "som": "Soo qaado sawirka baasaboorka iyo shahaadada dhalashada berri subax.",
        "eng": "Bring passport-sized photographs and your birth certificate tomorrow morning.",
    },
    {
        "domain": "legal_police",
        "orm": "Boorsaan koo fi bilbilli harkaa koo na duraa badeera, gabaasa poolisii barbaada.",
        "amh": "ቦርሳዬ እና የእጅ ስልኬ ጠፍተውብኛል፣ የፖሊስ ሪፖርት ማውጣት እፈልጋለሁ።",
        "tir": "ቦርሳይን ናይ ኢድ ተንቀሳቓሲ ስልከይን ጠፊኡኒ፣ ናይ ፖሊስ ሪፖርት ክገብር እደሊ ኣለኹ።",
        "som": "Boorsadaydii iyo taleefankaygii gacanta ayaa iga lumay, waxaan rabaa warbixinta booliska.",
        "eng": "My bag and mobile phone have been lost, I need to file a police report.",
    },
    {
        "domain": "civic_administration",
        "orm": "Waraqaan ragaa gaa'elaa fi dhalootaa biiroo dhimma lammummaa keessatti kennama.",
        "amh": "የጋብቻ እና የልደት ምስክር ወረቀት በወሳኝ ኩነት ምዝገባ ቢሮ ይሰጣል።",
        "tir": "ናይ መርዓን ናይ ልደትን ምስክር ወረቐት ኣብ ወሳኒ ኩነታት መዝገብ ቤት ጽሕፈት ይወሃብ።",
        "som": "Shahaadada guurka iyo dhalashada waxaa lagu bixiyaa xafiiska diiwaangelinta madaniga ah.",
        "eng": "Marriage and birth certificates are issued at the civil registration office.",
    },

    # =========================================================================
    # 5. CULTURAL HOSPITALITY, COFFEE CEREMONY & ENTITY SHIELDING
    # =========================================================================
    {
        "domain": "dining_hospitality",
        "orm": "Baga nagaan dhuftan! Koottuu buna qalaa fi buddeena ittoo waliin nyaadhaa.",
        "amh": "እንኳን ደህና መጣችሁ! ኑ ቡና ጠጡ፣ ከእንጀራ እና ወጥ ጋር አብረን እንብላ።",
        "tir": "እንቋዕ ብደሓን መጻእኩም! ንዑ ቡን ስተዩ፣ ምስ እንጀራን ጸብሕን ሓቢርና ንብላዕ።",
        "som": "Soo dhowaada! Kaalaya bunka cabba oo canjeelada iyo maraqa nala cuna.",
        "eng": "Welcome! Come have coffee and eat injera with stew with us.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Buni kun baay'ee mi'aawa, fooliin isaas mana kana guuteera.",
        "amh": "ይህ ቡና በጣም ይጣፍጣል፣ መዓዛውም ቤቱን ሞልቶታል።",
        "tir": "እዚ ቡን ኣዝዩ ጥዑም እዩ፣ መኣዛኡ ድማ ነዛ ገዛ መሊእዋ ኣሎ።",
        "som": "Bunkani aad buu u macaan yahay, carafadiisuna guriga ayay buuxisay.",
        "eng": "This coffee is delicious, and its aroma fills the entire house.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Guyyaa ayyaana Irreechaa, Masqalaa fi Iidaa maatiin hundi walitti qabama.",
        "amh": "በኢሬቻ፣ በመስቀል እና በኢድ በዓል ቀን መላው ቤተሰብ በአንድነት ይሰበሰባል።",
        "tir": "ብበዓል መስቀል፣ ዒድን ልደትን መላእ ስድራቤት ብሓባር ይእከብ።",
        "som": "Maalmaha ciidaha sida Ciidul Fidri iyo kuwa dhaqanka, qoyska oo dhan baa isu yimaada.",
        "eng": "During holidays like Irreecha, Meskel, and Eid, the entire family gathers together.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Abebeen, Caalaan, Almaazii fi Haagoos gara magaalaa Hawaasaa fi Dirree Dhawaatti imalan.",
        "amh": "አበበ፣ ጫላ፣ አልማዝ እና ሓጎስ ወደ ሐዋሳ እና ድሬዳዋ ከተሞች ተጓዙ።",
        "tir": "ኣበበ፣ ጫላ፣ ኣልማዝን ሓጎስን ናብ ከተማታት ሓዋሳን ድሬዳዋን ተጓዒዞም።",
        "som": "Abebe, Chala, Almaz iyo Hagos waxay u safreen magaalooyinka Hawassa iyo Dire Dawa.",
        "eng": "Abebe, Chala, Almaz, and Hagos traveled to the cities of Hawassa and Dire Dawa.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Nyaata aadaa akka kittafoo, doro woxxii, gaafii fi qoochoo baay'ee jaallanna.",
        "amh": "እንደ ክትፎ፣ የዶሮ ወጥ፣ ገንፎ እና ቆጮ ያሉ የባህል ምግቦችን በጣም እንወዳለን።",
        "tir": "ከም ክትፎ፣ ጸብሒ ደርሆ፣ ገንፎን ቆጮን ዝኣመሰሉ ባህላዊ ምግብታት ኣዝዩ ባህ ይብለና።",
        "som": "Waxaan aad u jecelnahay cuntooyinka dhaqanka sida kitfo, suugo digaag, genfo iyo kocho.",
        "eng": "We love traditional dishes such as Kitfo, Doro Wat, Genfo, and Kocho.",
    },
    {
        "domain": "greetings",
        "orm": "Fayyaa fi nagaan keessan eegamaa haa ta'u, Waaqayyo isin haa eebbisu.",
        "amh": "ጤናችሁና ሰላማችሁ የተጠበቀ ይሁን፣ እግዚአብሔር ይባርካችሁ።",
        "tir": "ጥዕናኹምን ሰላምኩምን ዝተሓለወ ይኹን፣ እግዚኣብሄር ይባርክኩም።",
        "som": "Caafimaad iyo nabadba ha laydiin barakeeyo, Ilaahay ha idin barakeeyo.",
        "eng": "May your health and peace be protected, may God bless you.",
    },
]


def seed_deep_dialogues() -> int:
    tm = TranslationMemory.get_instance()
    langs = ["orm", "amh", "tir", "som", "eng"]
    records = []

    for entry in DEEP_ETHIOPIAN_CORPUS:
        domain = entry["domain"]
        for src in langs:
            for tgt in langs:
                if src == tgt:
                    continue
                records.append({
                    "src_lang": src,
                    "tgt_lang": tgt,
                    "source": entry[src],
                    "target": entry[tgt],
                    "domain": domain,
                    "dataset": "deep_ethiopian_v2",
                    "confidence": 1.0,
                })

    inserted = tm.bulk_insert(records, bidirectional=False)
    print(f"✓ Successfully seeded {inserted} pristine 5-way dialogue pairs into Translation Memory!")
    print(f"✓ Total Translation Memory records now: {tm.count():,}")
    return inserted


if __name__ == "__main__":
    seed_deep_dialogues()
