"""
Scenario-by-Scenario Intelligence Seeder for LISAN Translation Memory.

Scenarios:
1. In a Clinic (Medical & Health)
2. On a Road (Transit & Directions)
3. In a Cafe (Buna Culture & Hospitality)
4. In a Market (Trade, Bargaining & Produce)

Seeded across all 5 languages:
- orm (Afaan Oromoo)
- amh (Amharic)
- tir (Tigrinya)
- som (Somali)
- eng (English)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_pipeline.translation_memory import TranslationMemory


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: In a Clinic (Medical & Health)
# ─────────────────────────────────────────────────────────────────────────────
CLINIC_CORPUS: list[dict[str, str]] = [
    {
        "domain": "emergency_medical",
        "orm": "Bakka kamtu si dhukkuba, yoom eegale mee?",
        "amh": "የት አካባቢ ያመዎታል፣ መቼ ነው የጀመረው?",
        "tir": "ኣበይ የሕምመካ ኣሎ፣ መዓስከ ጀሚሩ?",
        "som": "Xaggee ku xanuunaysaa, goormayse bilaabatay?",
        "eng": "Where does it hurt, and when did it start?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Qoma na dhukkuba, akkasumas hafura baafachuun natti ulfaata.",
        "amh": "ደረቴን በብርቱ ያመኛል፣ እንዲሁም መተንፈስ ከብዶኛል።" ,
        "tir": "ኣፍ-ልበይ ኣበርቲዑ የሕምመኒ ኣሎ፣ ከምኡ'ውን ምስትንፋስ ከቢዱኒ።",
        "som": "Laabta ayaa aad ii xanuunaysa, neefsashaduna way igu adagtahay.",
        "eng": "I have severe chest pain and difficulty breathing.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Mee taa'aa, hafura gadi fageenyaan fudhadhaa, tasgabbaa'aa.",
        "amh": "እባክዎን ይቀመጡ፣ ረጅምና ጥልቅ ትንፋሽ ይውሰዱ፣ ይረጋጉ።",
        "tir": "በጃኹም ተቐመጡ፣ ዓሚቝ ትንፋስ ውሰዱ እሞ ህድእ በሉ።",
        "som": "Fadlan fariiso, neef dheer qaado, oo is daji.",
        "eng": "Please sit down, take deep breaths, and relax.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Dhiibbaa dhiigaa fi ho'a qaamaa keessan safaruun qaba.",
        "amh": "የደም ግፊትዎን እና የሰውነት ሙቀትዎን መለካት አለብኝ።",
        "tir": "ጸቕጢ ደምኩምን ረስኒ ኣካላትኩምን ክልክዕ ኣለኒ።",
        "som": "Waa inaan cabbiraa cadaadiska dhiiggaaga iyo heerkulka jirkaaga.",
        "eng": "I need to measure your blood pressure and body temperature.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Mataan na mara, akkasumas ho'i qaamaa guddaan natti jira.",
        "amh": "ራሴን ያዞረኛል፣ እንዲሁም ከፍተኛ ትኩሳት አለብኝ።",
        "tir": "ርእሰይ የዘውረኒ ኣሎ፣ ከምኡ'ውን ሓያል ረስኒ ኣሎኒ።",
        "som": "Madaxa ayaa i wareeraya, sidoo kale qandho sare ayaa i haysa.",
        "eng": "I feel very dizzy and I have a high fever.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Dhibee ykn busaa mirkaneeffachuuf qorannoon dhiigaa isin barbaachisa.",
        "amh": "ኢንፌክሽን ወይም የወባ በሽታ መኖሩን ለማረጋገጥ የደም ምርመራ ያስፈልግዎታል።",
        "tir": "ኢንፈክሽን ወይ ዓሶ ምህላዉ ንምርግጋጽ ናይ ደም መርመራ የድልየኩም እዩ።",
        "som": "Waxaad u baahantahay baaritaan dhiig si loo hubiyo infekshan ama duumo.",
        "eng": "You need a blood test to check for infection or malaria.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Kutaan laaboraatoorii qorannoo dhiigaa eessa jira mee?",
        "amh": "የደም ምርመራ የሚያደርገው የላቦራቶሪ ክፍል የት ይገኛል?",
        "tir": "ናይ ደም መርመራ ዝግበረሉ ክፍሊ ላቦራቶሪ ኣበይ ኣሎ?",
        "som": "Qolka shaybaarka ee baaritaanka dhiigga xaggee ku yaallaa?",
        "eng": "Where is the laboratory room for the blood test?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Laaboraatooriin karaa gamoo kanaa gara bitaatti isa dhuma irratti argama.",
        "amh": "ላቦራቶሪው በዚህ መተላለፊያ መጨረሻ ላይ በስተግራ በኩል ይገኛል።",
        "tir": "ላቦራቶሪ ኣብዚ መተሓላለፊ መወዳእታ ብሸነኽ ጸጋም ይርከብ።",
        "som": "Shaybaarku wuxuu ku yaallaa dhamaadka marinkan dhanka bidixda.",
        "eng": "The laboratory is located at the end of this hallway on the left.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Kun waraqaa ajaja qoricha farra dhibee fi dhukkubbii hir'isuuti.",
        "amh": "ይህ የፀረ-ተህዋስያን እና የህመም ማስታገሻ መድኃኒት ማዘዣ ወረቀት ነው።",
        "tir": "እዚ ናይ ፀረ-ተህዋስያንን መስተኻኸሊ ሕማምን ናይ መድሃኒት ወረቐት እዩ።",
        "som": "Kani waa warqadda daawada ee antibiyootiga iyo xanuun baabi'iyaha.",
        "eng": "This is your prescription for antibiotics and pain relief medication.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Guyyaatti yeroo meeqa qoricha kana fudhachuu qaba?",
        "amh": "ይህን መድኃኒት በቀን ስንት ጊዜ መውሰድ አለብኝ?",
        "tir": "እዚ መድሃኒት ኣብ መዓልቲ ክንደይ ግዜ ክወስዶ ኣለኒ?",
        "som": "Maalintii imisa jeer ayaan qaadanayaa daawadan?",
        "eng": "How many times a day should I take this medicine?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Kiniina tokko sa'aatii saddeet saddeetiin bishaan baay'ee wajjin liqimsaa.",
        "amh": "አንድ ኪኒን በየስምንት ሰዓቱ ከብዙ ውሃ ጋር ይዋጡ።",
        "tir": "ሓደ ፍረ ኪኒን ኣብ ነፍሲ ወከፍ ሸሞንተ ሰዓት ምስ ብዙሕ ማይ ውሰድዎ።",
        "som": "Hal xabbo oo kaniini ah qaado sideedii saacadoodba adigoo biyo badan cabbaya.",
        "eng": "Swallow one tablet every eight hours with plenty of water.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Kiliniika kana keessatti manneen qorichaa ni jiraa?",
        "amh": "በዚህ ክሊኒክ ውስጥ የመድኃኒት መሸጫ ቤት ወይም ፋርማሲ አለ?",
        "tir": "ኣብዚ ክሊኒክ ውሽጢ ቤት መሸጣ መድሃኒት ወይ ፋርማሲ ኣሎዶ?",
        "som": "Ma ku dhex yaallaa farmashiye rugtan caafimaadka?",
        "eng": "Is there a pharmacy or dispensary inside this clinic?",
    },
    {
        "domain": "emergency_medical",
        "orm": "Eeyyee, balbala lakkofsa lama irratti qoricha argattu.",
        "amh": "አዎ፣ በበር ቁጥር ሁለት ላይ መድኃኒቱን ያገኛሉ።",
        "tir": "እወ፣ ኣብ ኣፍደገ ቍጽሪ ክልተ መድሃኒት ክትረኽቡ ትኽእሉ ኢኹም።",
        "som": "Haa, daawada waxaad ka helaysaa qolka lambar laba.",
        "eng": "Yes, you will get the medicine at counter number two.",
    },
    {
        "domain": "emergency_medical",
        "orm": "Galatoomaa doktora, fayyuu keessan haa ta'u, eebbi isiniif haa baay'atu.",
        "amh": "አመሰግናለሁ ዶክተር፣ እግዜር ይማርልኝ፣ እድሜና ጤና ይስጥዎት።",
        "tir": "የቐንየለይ ዶክተር፣ ፈጣሪ ይምሓርኩም፣ ጥዕናን ዕድመን ይሃብኩም።",
        "som": "Mahadsanid dhakhtar, alla ha ku barakeeyo, caafimaadna ha ku siiyo.",
        "eng": "Thank you doctor, may God heal and bless you with good health.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: On a Road (Transit & Directions)
# ─────────────────────────────────────────────────────────────────────────────
ROAD_CORPUS: list[dict[str, str]] = [
    {
        "domain": "navigation_directions",
        "orm": "Buufata konkolaataa inni guddaan eessatti argama?",
        "amh": "ዋናው የአውቶቡስ ተራ የት ነው የሚገኘው?",
        "tir": "እቲ ቀንዲ መደበር ኣውቶቡስ ኣበይ ይርከብ?",
        "som": "Xaggee ku yaallaa istaanka weyn ee basaska?",
        "eng": "Where is the main bus terminal located?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Baajaajii qabadhuutii addabaabaayii guddaa irratti gara mirgaatti maqi.",
        "amh": "ባጃጅ ይዘህ በትልቁ አደባባይ ወደ ቀኝ ታጠፍ።",
        "tir": "ባጃጅ ተሳፊርካ ኣብቲ ዓብዪ ኣደባባይ ናብ የማን ተጠወቕ።",
        "som": "Bajaaj raac oo wareegtada weyn dhanka midig uga leexo.",
        "eng": "Take a bajaj and turn right at the big roundabout.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Gara walakkaa magaalaatti kaffaltiin baajaajii meeqa?",
        "amh": "ወደ ከተማው መሀል የባጃጅ ታሪፍ ስንት ብር ነው?",
        "tir": "ናብ ማእከል ከተማ ናይ ባጃጅ ታሪፍ ክንዲ ምንታይ እዩ?",
        "som": "Waa imisa lacagta bajaajta ee bartamaha magaalada?",
        "eng": "How much is the bajaj fare to the city center?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Kaffaltiin idilee nama tokkoof birrii kudha shan.",
        "amh": "መደበኛው ታሪፍ ለአንድ መንገደኛ አስራ አምስት ብር ነው።",
        "tir": "እቲ ስሩዕ ታሪፍ ንሓደ ተሳፋሪ ዓሰርተ ሓሙሽተ ቅርሺ እዩ።",
        "som": "Qiimaha caadiga ah waa shan iyo toban Birr qofkiiba.",
        "eng": "The standard fare is fifteen Birr per passenger.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Maaloo ibsaa tiraafikii isa fuulduraa biratti na buusi.",
        "amh": "እባክህ ከፊትህ ባለው የትራፊክ መብራት አጠገብ አውርደኝ።",
        "tir": "በጃኻ ኣብቲ ቀዳማይ መብራህቲ ትራፊክ ጥቓኡ ኣውርደኒ።",
        "som": "Fadlan igu deji laydhka taraafikada ee soo socda agtiisa.",
        "eng": "Please drop me off near the upcoming traffic light.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Kaffaltii geejjibaa miiniibaasii kan hin kaffalle eenyu?",
        "amh": "የታክሲ ወይም የሚኒባስ ሂሳብ ያልከፈለ ማነው?",
        "tir": "ናይ ሚኒባስ ታሪፍ ዘይከፈለ መን ኣሎ?",
        "som": "Yaan weli bixinin lacagta gaariga yar ee basaska?",
        "eng": "Who hasn't paid their minibus transport fare yet?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Kunoo birrii shantama, deebii koo naaf kenni mee.",
        "amh": "ሀምሳ ብር ይኸውልህ፣ እባክህ መልሴን ስጠኝ።",
        "tir": "ሓምሳ ቅርሺ እንሀልካ፣ በጃኻ መልሰይ ሃበኒ።",
        "som": "Waa kan konton Birr, fadlan soo celi baaqiga.",
        "eng": "Here is fifty Birr, please give me my change.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Miiniibaasiin kun qajeeltoon gara isteediyeemiitti deemaa?",
        "amh": "ይህ ሚኒባስ በቀጥታ ወደ ስታዲየም ይሄዳል?",
        "tir": "እዚ ሚኒባስ ብቐጥታ ናብ ስታድየም ይኸይድ ድዩ?",
        "som": "Gaarigan yar ma wuxuu toos u tagayaa garoonka ciyaaraha?",
        "eng": "Does this minibus go directly towards the stadium?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Eeyyee, galiitii taa'i, ammumma kana kaana.",
        "amh": "አዎ፣ ግባና ተቀመጥ፣ አሁኑኑ እንነሳለን።",
        "tir": "እወ፣ እቶ እሞ ተቐመጥ፣ ሕጂ ንብገስ ኣለና።",
        "som": "Haa, soo gal oo fariiso, hadda ayaan baxaynaa.",
        "eng": "Yes, come in and take a seat, we are leaving right away.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Boba'aa naqachuuf buufanni boba'aa dhihoo jiru eessa jira?",
        "amh": "ነዳጅ ለመቅዳት በአቅራቢያ የሚገኝ ማደያ የት አለ?",
        "tir": "ነዳዲ ንምምላእ ኣብ ቀረባ ዘሎ መዕደሊ ነዳዲ ኣበይ ኣሎ?",
        "som": "Xaggee ku yaallaa kaalinta shidaalka ee ugu dhow?",
        "eng": "Where is the nearest gas station to refill fuel?",
    },
    {
        "domain": "navigation_directions",
        "orm": "Riqicha ce'iitii buufata boba'aa gara bitaa keetiin argatta.",
        "amh": "ድልድዩን ተሻገርና የነዳጅ ማደያውን በስተግራህ ታገኘዋለህ።",
        "tir": "ነቲ ድልድል ተሳጊርካ ነቲ መዕደሊ ነዳዲ ብሸነኽ ጸጋምካ ክትረኽቦ ኢኻ።",
        "som": "Gudub buundada waxaadna kaalinta shidaalka ku arki doontaa bidixdaada.",
        "eng": "Cross the bridge and you will see the fuel station on your left.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Yeroo ammaa kana daandii guddaa irratti cufamni tiraafikaa cimaan jira.",
        "amh": "በአሁኑ ሰዓት በዋናው መንገድ ላይ ከፍተኛ የትራፊክ መጨናነቅ አለ።",
        "tir": "ኣብዚ ሕጂ እዋን ኣብቲ ዓብዪ መንገዲ ሓያል ናይ ትራፊክ ጽቕጥቅጥ ኣሎ።",
        "som": "Waxa hadda jira saxmad baabuur oo aad u daran waddada weyn.",
        "eng": "There is heavy traffic congestion on the main road right now.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Maaloo saffisa hir'isiitii goolbii irratti of eeggannoon oofi.",
        "amh": "እባክህ ፍጥነትህን ቀንስና መታጠፊያው ላይ በጥንቃቄ አሽከርክር።",
        "tir": "በጃኻ ፍጥነትካ ኣጉድል እሞ ኣብቲ መቐየሪ ብጥንቃቐ ንደቕ።",
        "som": "Fadlan xawaaraha dhim oo si taxadar leh ugu wad gooladda.",
        "eng": "Please slow down and drive carefully around the curve.",
    },
    {
        "domain": "navigation_directions",
        "orm": "Waan na geessifteef galatoomi, nagaan deemi karaa nagaa!",
        "amh": "ስላደረስከኝ አመሰግናለሁ፣ መንገዱን ያቅናልህ መልካም ጉዞ!",
        "tir": "ስለ ዘብጻሕካኒ የቐንየለይ፣ መንገዲ የቀንዓልካ ቡሩኽ ጉዕዞ!",
        "som": "Waad ku mahadsantahay gaadiidka, safaro wanaagsan oo nabad ku tag!",
        "eng": "Thank you for the ride, have a safe and smooth journey!",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3: In a Cafe (Buna Culture & Hospitality)
# ─────────────────────────────────────────────────────────────────────────────
CAFE_CORPUS: list[dict[str, str]] = [
    {
        "domain": "dining_hospitality",
        "orm": "Akkam bultan, foddaa bira teessoon duwwaan ni jiraa?",
        "amh": "እንደምን አደራችሁ፣ መስኮቱ አጠገብ ክፍት ጠረጴዛ አለ?",
        "tir": "ከመይ ሓዲርኩም፣ ጥቓ መስኮት ባዶ ሰሌዳ ኣሎዶ?",
        "som": "Subax wanaagsan, miis banaan ma ka jiraa daaqadda agteeda?",
        "eng": "Good morning, is there an empty table available by the window?",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Baga nagaan dhuftan, mee taa'aa, tarreen dhugaatii ho'aa fi ciree kunoo ti.",
        "amh": "እንኳን ደህና መጣችሁ፣ እባካችሁ ተቀመጡ፣ የሙቅ መጠጦችና የቁርስ ዝርዝር ይኸውላችሁ።",
        "tir": "እንቋዕ ብደሓን መጻእኩም፣ በጃኹም ተቐመጡ፣ ናይ ውዑይ መስተን ቁርስን ዝርዝር እንሆ።",
        "som": "Soo dhawoow, fadlan fariiso, kani waa liiska cabbitaannada kulul iyo cunnada fudud.",
        "eng": "Welcome, please take a seat, here is our hot drink and snack menu.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Buna jabanaa haaraa xenaa addaamaa qabu nuuf danfisuu dandeessaa?",
        "amh": "በጤና አዳም የተፈላ ትኩስ የጀበና ቡና ልታፈላልን ትችላለህ?",
        "tir": "ብጨና ኣዳም ዝተፈልሐ ሓዲሽ ናይ ጀበና ቡን ከተፍልሓልና ትኽእልዶ?",
        "som": "Ma noo karin kartaa bun jabana cusub oo leh caleenta xawaashka?",
        "eng": "Can you brew a fresh clay pot of Jebena coffee with rue herb for us?",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Gammachuudhaan, bunni naanna'aa duraa aboliin daqiiqaa shan keessatti qophaa'a.",
        "amh": "በደስታ፣ የአቦል ዙር ቡና በአምስት ደቂቃ ውስጥ ይደርሳል።",
        "tir": "ብሓጎስ፣ ናይ ኣቦል ዙር ቡን ኣብ ውሽጢ ሓሙሽተ ደቒቕ ክቐርብ እዩ።",
        "som": "Farxad weyn leh, wejiga koowaad ee bunka Abol wuxuu diyaar ku noqonayaa shan daqiiqo gudahood.",
        "eng": "Certainly, the first round Abol coffee will be served in five minutes.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Maaloo buna sana wajjin fandishaa haaraa fi qollo nuuf fidi.",
        "amh": "እባክህ ከቡናው ጋር ትኩስ ፈንድሻ እና ቆሎ አብረህ አምጣልን።",
        "tir": "በጃኻ ምስቲ ቡን ውዑይ ፈንዲሻን ቖሎን ሒዝካልና ምጻእ።",
        "som": "Fadlan sidoo kale noo keen baaquli salool kulul ah iyo garow shiilan.",
        "eng": "Please also bring a bowl of freshly popped corn and roasted barley.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Hiriyyaan koo buna mannaa shaayee qarafaa zinjibilaa fi qarafuuda qabu filata.",
        "amh": "ጓደኛዬ ከቡና ይልቅ በዝንጅብልና በቅርንፉድ የተዘጋጀ የቅመም ሻይ ይፈልጋል።",
        "tir": "ዓርከይ ካብ ቡን ንላዕሊ ብጅንጅብልን ቅርንፍልን ዝተዳለወ ናይ ቅመም ሻሂ ይመርጽ።",
        "som": "Saaxiibkay wuxuu ka doorbidayaa shaah xawaash leh oo leh sinjibiil iyo qaranful.",
        "eng": "My friend prefers spiced black tea with ginger and clove instead of coffee.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Sukkaara wajjin, giddu galeessa moo guutummaatti sukkaara malee ha ta'u?",
        "amh": "ስኳር ያለው፣ መካከለኛ ወይስ ጭራሽ ያለ ስኳር ይሁን?",
        "tir": "ሽኮር ዘለዎ፣ ማእከላይ ወይስ ጭራሽ ብዘይ ሽኮር ይኹነልኩም?",
        "som": "Ma sonkor leh, ma mid dhexdhexaad ah, mise gabi ahaanba sonkor la'aan?",
        "eng": "Would you like regular sugar, medium sweet, or completely without sugar?",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Maaloo maakiyaatoo fi shaayee sana gonkumaa sukkaara malee nuuf godhi.",
        "amh": "እባክህ ማኪያቶውንና ሻዩን ያለ ምንም ስኳር አድርግልን።",
        "tir": "በጃኻ ነቲ ማክያቶን ሻህን ጭራሽ ብዘይ ሽኮር ግበረልና።",
        "som": "Fadlan maakiyaatada iyo shaaha nooga dhig kuwo aan sonkor lahayn.",
        "eng": "Please make the macchiato and tea completely sugar-free.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Har'a cireen soomaa ykn keekiin soomaa qophaa'e ni jiraa?",
        "amh": "ዛሬ የሚገኝ የጾም ቁርስ ወይም የጾም ኬክ አለ?",
        "tir": "ሎሚ ዝርከብ ናይ ጾም ቁርሲ ወይ ናይ ጾም ኬክ ኣሎዶ?",
        "som": "Ma jiraan cuntooyin soon ah ama keeg fudud oo maanta diyaarsan?",
        "eng": "Is there any fasting snack or vegan pastry available today?",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Eeyyee, sambuusa misiraa fi keekii kuduraa soomaa qabna.",
        "amh": "አዎ፣ ትኩስ የምስር ሳምቡሳ እና የጾም የአትክልት ኬክ አለን።",
        "tir": "እወ፣ ውዑይ ናይ ብርስን ሳምቡሳን ናይ ኣሕምልቲ ናይ ጾም ኬክን ኣሎና።",
        "som": "Haa, waxaan haynaa sambuus diirran oo misir ah iyo keeg qudaar ah.",
        "eng": "Yes, we have fresh lentil sambusa and fasting vegetable pastries.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Urgooftuun buna kanaa adda, harki kee haa eebbifamu!",
        "amh": "የቡናው መዓዛ እጅግ ያውዳል፣ እጅህ ይባረክ!",
        "tir": "ናይቲ ቡን ጨና ኣዝዩ ጥዑም እዩ፣ ኣእዳውካ ይባረኽ!",
        "som": "Udgoonka bunku waa mid cajiib ah, gacmahaaga ha barakoobeen!",
        "eng": "The coffee aroma is wonderful, blessed be your hands!",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Galatoomaa! Kunoo naanna'aa barakaa isa dhumaa, eebbaa fi fayyaa isiniif haa ta'u.",
        "amh": "አመሰግናለሁ! ይኸውላችሁ የበረካ ዙር ቡና፣ በረካና ጤና ይሁንላችሁ።",
        "tir": "የቐንየለይ! እንሆ ናይ በረኻ ናይ መወዳእታ ዙር፣ ጥዕናን በረኸትን ይኹነልኩም።",
        "som": "Mahadsanid! Kani waa wareeggii ugu dambeeyay ee Baraka, caafimaad iyo barako ha idiin noqoto.",
        "eng": "Thank you! Here is the final Baraka round, may it bring health and blessing.",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Keessummeessaa, mee herrega keenya shallagdee nuuf fiduu dandeessaa?",
        "amh": "አስተናጋጅ፣ እባክህ ሒሳባችንን አስልተህ ልታመጣልን ትችላለህ?",
        "tir": "ኣሳላይ፣ በጃኻ ሒሳብና ጸቢጽካ ከተምጽኣልና ትኽእልዶ?",
        "som": "Mudlab, fadlan xisaabteena noo soo xisaabi oo noo keen biilka?",
        "eng": "Waiter, could you please calculate our bill and bring it to us?",
    },
    {
        "domain": "dining_hospitality",
        "orm": "Kaffaltiin tiippii dabalatee kunooti, deebii sana dhiisiitii guyyaa gaarii qabaadhu!",
        "amh": "የአስተናጋጅ ጉርሻውን ጨምሮ ክፍያው ይኸውልህ፣ መልሱን ተወውና መልካም ቀን ይሁንልህ!",
        "tir": "ናይ ኣሳላይ ጉርሻ ሓዊስካ ክፍሊት እንሆልካ፣ መልሲ ሕደጎ እሞ ቡሩኽ መዓልቲ ይኹነልካ!",
        "som": "Waa kan lacag bixinta oo ay ku jirto gunnadaadu, baaqiga qaado oo maalin wanaagsan ku qaado!",
        "eng": "Here is the payment including your tip, keep the change and have a great day!",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4: In a Market (Trade, Bargaining & Produce)
# ─────────────────────────────────────────────────────────────────────────────
MARKET_CORPUS: list[dict[str, str]] = [
    {
        "domain": "commerce_bargaining",
        "orm": "Akkam jirtu, xaafiin adii sadarkaa tokkoffaa kun kuntaalli meeqa?",
        "amh": "ጤና ይስጥልኝ፣ የአንደኛ ደረጃ የነጭ ጤፍ ኩንታል ስንት ነው?",
        "tir": "ከመይ ውዒልኩም፣ ናይ ቀዳማይ ብርኪ ጻዕዳ ጣፍ ኩንታል ክንዲ ምንታይ እዩ?",
        "som": "Galab wanaagsan, waa imisa qiimaha kiintaalka teff-ka cad ee tayada koowaad?",
        "eng": "Good day, how much is a quintal of this Grade One white teff?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Xaafii sirrii Ada'aa ti, kireen kantaala tokkoo birrii kuma torba.",
        "amh": "ትክክለኛ የአደዓ ጤፍ ነው፣ አንድ ኩንታል ሰባት ሺህ ብር ነው።",
        "tir": "ትክክለኛ ናይ ዓዳዕ ጣፍ እዩ፣ ሓደ ኩንታል ሾብዓተ ሽሕ ቅርሺ እዩ።",
        "som": "Waa teff-ka dhabta ah ee Ada'a, kiintaalkiiba waa toddoba kun oo Birr.",
        "eng": "It is genuine Ada'a teff, seven thousand Birr per quintal.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Baay'ee qaalii dha, yoo kuntaala lama fudhadhe gatii naaf hir'iftaa?",
        "amh": "ትንሽ ውድ ነው፣ ሁለት ኩንታል ከወሰድኩ ቅናሽ ታደርግልኛለህ?",
        "tir": "እዚ ንእሽቶ ክቡር እዩ፣ ክልተ ኩንታል እንተወሲደ ዋጋ ተጉድለለይዶ?",
        "som": "Aad bay qaali u tahay, haddii aan laba kiintaal qaato ma ii dhimaysaa?",
        "eng": "That is rather expensive, can you make a discount if I take two quintals?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Kuntaala lama waan fudhattuuf, gatii dhumaa birrii kuma jahaa fi dhibba shan siif godha.",
        "amh": "ሁለት ኩንታል ስለምትወስድ የመጨረሻ ዋጋ ስድስት ሺህ አምስት መቶ አደርግልሃለሁ።",
        "tir": "ክልተ ኩንታል ስለ እትወስድ፣ ናይ መወዳእታ ዋጋ ሽዱሽተ ሽሕን ሓሙሽተ ሚእትን ክገብረልካ እየ።",
        "som": "Maadaama aad laba kiintaal qaadanayso, qiimaha ugu dambeeya waxaan kaaga dhigayaa lix kun iyo shan boqol.",
        "eng": "Since you are buying two quintals, I will reduce it to six thousand five hundred.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Qullubbiin diimaa fi qullubbiin adii kiiloon tokko meeqa meeqa?",
        "amh": "ቀይ ሽንኩርት እና ነጭ ሽንኩርት በኪሎ ስንት ስንት ናቸው?",
        "tir": "ቀይሕ ሽጉርትን ጻዕዳ ሽጉርትን ሓደ ኪሎ ክንዲ ምንታይ እዮም?",
        "som": "Waa immisa basasha gaduudan iyo toonta kiiloodiiba?",
        "eng": "How much are the red onions and garlic per kilogram?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Qullubbiin diimaan birrii shantama, qullubbiin adii ammoo kiiloon birrii dhibba tokkoo fi digdama.",
        "amh": "ቀይ ሽንኩርቱ ሀምሳ ብር፣ ነጭ ሽንኩርቱ ደግሞ በኪሎ አንድ መቶ ሀያ ብር ነው።",
        "tir": "ቀይሕ ሽጉርቲ ሓምሳ ቅርሺ፣ ጻዕዳ ሽጉርቲ ኸኣ ብኪሎ ሓደ ሚእትን ዕስራን ቅርሺ እዩ።",
        "som": "Basasha gaduudan waa konton Birr, toontuna waa boqol iyo labaatan Birr kiiloodiiba.",
        "eng": "The red onions are fifty Birr, and the garlic is one hundred twenty Birr per kilo.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Maaloo madaallii irratti qullubbii kiiloo sadii fi timaatima haaraa kiiloo lama naaf madaali.",
        "amh": "እባክህ በሚዛኑ ላይ ሶስት ኪሎ ሽንኩርት እና ሁለት ኪሎ ትኩስ ቲማቲም መዝነህ ስጠኝ።",
        "tir": "በጃኻ ኣብቲ ሚዛን ሰለስተ ኪሎ ሽጉርትን ክልተ ኪሎ ውዑይ ቲማቲምን ሚዚንካ ሃበኒ።",
        "som": "Fadlan miisaanka iigu miis saddex kiilo oo basal ah iyo laba kiilo oo yaanyo cusub ah.",
        "eng": "Please weigh three kilos of onions and two kilos of fresh tomatoes on the scale.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Timaatimichi kan hin banne, bilchaataa fi jabaa ta'uu isaa mirkaneessi.",
        "amh": "ቲማቲሞቹ ያልተበላሹና የደረሱ መሆናቸውን አረጋግጥ።",
        "tir": "እቶም ቲማቲም ዘይተበላሸዉን ዝበሰሉን ምዃኖም ኣረጋግጽ።",
        "som": "Hubi in yaanyadu ay wada adagtahay oo bisishahay, oo aysan waxyeelo gaarin.",
        "eng": "Make sure all the tomatoes are firm and ripe, not bruised.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Barbarree Itoophiyaa isa qulqullina qabu haaraa daakame qabdaa?",
        "amh": "ትኩስ የተፈጨ ጥራት ያለው ንጹህ የኢትዮጵያ በርበሬ አለህ?",
        "tir": "ጽሩይ ዝተጠሕነ ናይ ኢትዮጵያ ጽሩይ በርበረ ኣሎካዶ?",
        "som": "Ma haysaa basbaaska Itoobiyaanka ee saafiga ah ee hadda la shiiday?",
        "eng": "Do you have freshly ground, pure Ethiopian berbere spice powder?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Eeyyee, barbarreen kun mi'eessituu gosa digdama guutuu of keessaa qaba.",
        "amh": "አዎ፣ ይህ በርበሬ ሃያዎቹም የቅመም አይነቶች በሙሉ ተደባልቀውበታል።",
        "tir": "እወ፣ እዚ በርበረ ኲሎም ዕስራ ዓይነታት ቀመማት ተሓዊሶምዎ እዮም።",
        "som": "Haa, basbaaskani wuxuu ka kooban yahay dhammaan labaatanka xawaash ee kala duwan.",
        "eng": "Yes, this berbere has all twenty sacred spices blended into it.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Waliigala gatiin xaafii, kuduraalee fi barbarree meeqa ta'e?",
        "amh": "የጤፉ፣ የአትክልቱ እና የበርበሬው ጠቅላላ ድምር ስንት ሆነ?",
        "tir": "ናይቲ ጣፍ፣ ኣሕምልትን በርበረን ሓፈሻዊ ድምር ክንዲ ምንታይ ኮይኑ?",
        "som": "Wadarta guud ee lacagta teff-ka, qudaarta iyo basbaaska waa imisa?",
        "eng": "What is the total sum for the teff, vegetables, and berbere?",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Ida'amni waliigalaa birrii kuma jahaa fi dhibba saddeet ta'eera.",
        "amh": "ጠቅላላ ድምሩ በአንድ ላይ ስድስት ሺህ ስምንት መቶ ብር ሆኗል።",
        "tir": "ሓፈሻዊ ድምር ብሓባር ሽዱሽተ ሽሕን ሸሞንተ ሚእትን ቅርሺ ኮይኑ ኣሎ።",
        "som": "Wadarta guud waxay noqotay lix kun iyo sideed boqol oo Birr.",
        "eng": "The total comes to six thousand eight hundred Birr altogether.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Kunoo maallaqa callaa birrii kuma torba, deebii koo fi nagahee naaf kenni.",
        "amh": "ሰባት ሺህ ብር ጥሬ ገንዘብ ይኸውልህ፣ እባክህ መልሴንና ደረሰኝ ስጠኝ።",
        "tir": "ሾብዓተ ሽሕ ቅርሺ ጥረ ገንዘብ እንሆልካ፣ በጃኻ መልሰይን ቅብሊትን ሃበኒ።",
        "som": "Waa kan toddoba kun oo Birr oo caddaan ah, fadlan i sii baaqigayga iyo rasiidka.",
        "eng": "Here is seven thousand Birr in cash, please give me my change and a receipt.",
    },
    {
        "domain": "commerce_bargaining",
        "orm": "Deebiin kee birrii dhibba lama kunooti, gabaan haa tolu, eebbi daldalaa siif haa baay'atu!",
        "amh": "ሁለት መቶ ብር መልስህ ይኸውልህ፣ ገበያ ይቅናልህ፣ በረከቱ ይግባህ!",
        "tir": "ናይ ክልተ ሚእቲ ቅርሺ መልስኻ እንሆልካ፣ ዕዳጋ የቀንዓልካ፣ በረኸት ይእተወልካ!",
        "som": "Waa kan laba boqol oo Birr oo baaqigaaga ah, suuqu ha kuu barakoobo, iibsasho wacan!",
        "eng": "Here is your two hundred Birr change, may your trade and home be blessed!",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5: In a Kebele / Government Office (Civic Administration)
# ─────────────────────────────────────────────────────────────────────────────
KEBELE_CORPUS: list[dict[str, str]] = [
    {
        "domain": "civic_administration",
        "orm": "Akkam bultan, waraqaa eenyummaa haaromsuuf lakkofsa dabaree eessaa fudhadha?",
        "amh": "እንደምን አደራችሁ፣ የቀበሌ መታወቂያ ለማደስ የሰልፍ ቁጥር ከየት ነው የምወስደው?",
        "tir": "ከመይ ሓዲርኩም፣ ናይ ቀበሌ መንነት ወረቐት ንምሕዳስ ናይ ተራ ቍጽሪ ካበይ እየ ዝወስድ?",
        "som": "Subax wanaagsan, xaggee baan ka qaadan karaa lambarka safka ee cusboonaysiinta aqoonsiga?",
        "eng": "Good morning, where can I get a queue ticket number for resident ID renewal?",
    },
    {
        "domain": "civic_administration",
        "orm": "Maaloo lakkofsa dabaree digdami afur fudhadhaatii foddaa lakkofsa sadii bira eegaa.",
        "amh": "እባክዎን የሰልፍ ቁጥር ሃያ አራትን ይውሰዱና መስኮት ቁጥር ሶስት አጠገብ ይጠብቁ።",
        "tir": "በጃኹም ናይ ተራ ቍጽሪ ዕስራን ኣርባዕተን ውሰዱ እሞ መስኮት ቍጽሪ ሰለስተ ጥቓኣ ተጸበዩ።",
        "som": "Fadlan qaado lambarka safka ee afar iyo labaatanka oo ku sug daaqadda lambar saddex agteeda.",
        "eng": "Please take ticket number twenty-four and wait near window number three.",
    },
    {
        "domain": "civic_administration",
        "orm": "Waraqaa eenyummaa koo isa yeroon irra darbe haaromsuuf ragaalee akkamiitu barbaachisa?",
        "amh": "የጊዜው ያለፈበትን የቀበሌ መታወቂያዬን ለማደስ ምን ምን ማስረጃዎች ያስፈልጉኛል?",
        "tir": "እቲ ግዜኡ ዝሓለፎ ናይ ቀበሌ መንነት ወረቐተይ ንምሕዳስ እንታይ መረዳእታታት የድልየኒ?",
        "som": "Waa maxay dukumentiyada looga baahan yahay cusboonaysiinta kaarkayga aqoonsiga ee dhacay?",
        "eng": "What documents are required to renew my expired resident identification card?",
    },
    {
        "domain": "civic_administration",
        "orm": "Waraqaa eenyummaa isa duraa, suuraa paaspoortii lama, fi ragaa jireenyaa qabaachuu qabdu.",
        "amh": "የቀደመውን መታወቂያ፣ ሁለት የፓስፖርት መጠን ፎቶግራፍ እና የነዋሪነት ማረጋገጫ ያስፈልግዎታል።",
        "tir": "ነቲ ናይ ቀደም መንነት ወረቐት፣ ክልተ ናይ ፓስፖርት መጠን ስእልን መረጋገጺ መንበሪን የድልየኩም።",
        "som": "Waxaad u baahantahay kaarkii hore, laba sawir oo baasaboor ah, iyo caddeynta degganaanshaha.",
        "eng": "You need the expired ID, two passport-sized photographs, and proof of residence.",
    },
    {
        "domain": "civic_administration",
        "orm": "Sanadoota hunda fi lakkoofsa waraqaa eenyummaa dijitaalaa biyyoolessaa Fayidaa koo qabadheen dhufe.",
        "amh": "ሁሉንም ሰነዶች እና የፋይዳ ብሄራዊ ዲጂታል መታወቂያ ቁጥሬን ይዤ መጥቻለሁ።",
        "tir": "ኲሎም ሰነዳትን ናይ ፋይዳ ሃገራዊ ዲጂታል መንነት ቍጽረይን ሒዘ መጺአ ኣለኹ።",
        "som": "Waxaan keenay dhammaan dukumentiyada iyo lambarka aqoonsiga dhijitaalka ah ee qaranka ee Fayda.",
        "eng": "I have brought all the documents and my Fayda national digital ID number.",
    },
    {
        "domain": "civic_administration",
        "orm": "Baay'ee gaarii dha, mirkaneessaaf quba abbaa gurguddaa keessan iskaanaara ashaaraa irratti kaa'aa.",
        "amh": "በጣም ጥሩ፣ ለማረጋገጥ እባክዎን አውራ ጣትዎን በዲጂታል የጣት አሻራ መመርመሪያው ላይ ያድርጉ።",
        "tir": "ብጣዕሚ ጽቡቕ፣ ንምርግጋጽ በጃኹም ዓባይ ዓባይ ኣጻብዕትኹም ኣብቲ ዲጂታል መመርመሪ ኣሰር ኣቐምጡ።",
        "som": "Aad u wanaagsan, fadlan suulkaaga saar aaladda baarta faraha dhijitaalka ah si loo xaqiijiyo.",
        "eng": "Very good, please place your thumb on the digital biometric scanner for verification.",
    },
    {
        "domain": "civic_administration",
        "orm": "Akkasumas daa'ima koo isa haaraa dhalateef waajjira ragaa dhalootaa irraa waraqaa ragaa fudhachuun barbaada.",
        "amh": "እንዲሁም ለአራስ ልጄ የልደት ምስክር ወረቀት ከወሳኝ ኩነቶች ቢሮ መውሰድ እፈልጋለሁ።",
        "tir": "ከምኡ'ውን ነቲ ሓዲሽ እተወልደ ቈልዓይ ናይ ልደት ምስክር ወረቐት ካብ ቤት ጽሕፈት ወሳኒ ኲነታት ክወስድ እደሊ ኣለኹ።",
        "som": "Sidoo kale waxaan u baahanahay inaan u qaado shahaadada dhalashada ilmahayga cusub ee dhashay.",
        "eng": "I also need to obtain a vital events birth certificate for my newborn child.",
    },
    {
        "domain": "civic_administration",
        "orm": "Waraqaa ragaa da'umsaa hospitaala irraa kenname qabadhaatii gara kutaa torbaatti galmeef deemaa.",
        "amh": "የሆስፒታሉን የወሊድ ማረጋገጫ ወረቀት ይዘው ወደ ቢሮ ቁጥር ሰባት ለምዝገባ ይሂዱ።",
        "tir": "ነቲ ናይ ሆስፒታል ወሊድ መረጋገጺ ወረቐት ሒዝኩም ናብ ክፍሊ ቍጽሪ ሾብዓተ ንምዝገባ ኺዱ።",
        "som": "Fadlan warqadda dhalashada ee cisbitaalka u qaad qolka lambar toddoba si loo diiwaangeliyo.",
        "eng": "Please take the hospital delivery notification paper to room number seven for registration.",
    },
    {
        "domain": "civic_administration",
        "orm": "Waraqaan eenyummaa gandaa inni haaraan qophaa'ee gahuuf guyyoota hojii meeqa fudhata?",
        "amh": "አዲሱ የቀበሌ መታወቂያ ካርድ ተዘጋጅቶ ለመድረስ ስንት የስራ ቀናት ይወስዳል?",
        "tir": "እቲ ሓዲሽ ናይ ቀበሌ መንነት ወረቐት ተዳልዩ ክሳብ ዝበጽሕ ክንደይ ናይ ስራሕ መዓልታት ይወስድ?",
        "som": "Imisa maalmood oo shaqo ayay qaadanaysaa inuu diyaar ku noqdo kaarka cusub ee xaafaddu?",
        "eng": "How many business days will it take for the new resident ID card to be ready?",
    },
    {
        "domain": "civic_administration",
        "orm": "Sanadni erga mirkanaa'ee booda Kamisa ganama dhuftanii fudhachuu dandeessu.",
        "amh": "ሰነዱ ከተረጋገጠ በኋላ ሐሙስ ጠዋት መጥተው መውሰድ ይችላሉ።",
        "tir": "እቲ ሰነድ ምስ ተረጋገጸ ሓሙስ ንግሆ መጺእኩም ክትወስድዎ ትኽእሉ ኢኹም።",
        "som": "Waxay diyaar noqonaysaa Khamiista subaxdii kadib marka dukumentiga la xaqiijiyo.",
        "eng": "It will be ready for pickup on Thursday morning after document verification.",
    },
    {
        "domain": "civic_administration",
        "orm": "Xalayaa waliigaltee kana irratti chaappaa fi mallattoo gandaa naaf gochuu dandeessuu?",
        "amh": "እባክዎን በዚህ የውል ስምምነት ደብዳቤ ላይ የቀበሌውን ማህተም እና ፊርማ ያድርጉልኝ?",
        "tir": "ኣብዚ ናይ ውዕል ደብዳበ ናይ ቀበሌ ማሕተምን ፊርማን ከተዕርፉለይ ትኽእሉዶ?",
        "som": "Fadlan ma ku dhufan kartaa shaabadda xaafadda iyo saxiixa warqaddan heshiiska?",
        "eng": "Could you please stamp and apply the official seal on this agreement letter?",
    },
    {
        "domain": "civic_administration",
        "orm": "Chaappaan dhoofamuu dura qaamoleen lachuu waraqaa eenyummaa wajjin qaamaan dhihaachuu qabu.",
        "amh": "ማህተሙ ከመደረጉ በፊት ሁለቱም ወገኖች ከመታወቂያቸው ጋር በአካል መገኘት አለባቸው።",
        "tir": "እቲ ማሕተም ቅድሚ ምግባሩ ክልቲኦም ወገናት ምስ መንነት ወረቐቶም ብኣካል ክቐርቡ ኣለዎም።",
        "som": "Labada dhinacba waa inay shakhsiyan u joogaan iyagoo wata kaararkooda aqoonsiga ka hor intaan shaabadda la dhufan.",
        "eng": "Both parties must be present in person with their IDs before the official seal is affixed.",
    },
    {
        "domain": "civic_administration",
        "orm": "Kaffaltii tajaajila mana qopheessaa eessatti kaffala, nagaheen seera qabeessi naaf kennamaa?",
        "amh": "የማዘጋጃ ቤት አገልግሎት ክፍያውን የት ነው የምከፍለው፣ ህጋዊ ደረሰኝ ይሰጠኛል?",
        "tir": "ናይ ምምሕዳር ኣገልግሎት ክፍሊት ኣበይ እየ ዝኸፍል፣ ሕጋዊ ቅብሊት ይወሃበኒ ድዩ?",
        "som": "Xaggee baan ku bixiyaa lacagta adeegga dawladda hoose, ma heli karaa rasiid rasmi ah?",
        "eng": "Where do I pay the municipal service fee, and can I get an official receipt?",
    },
    {
        "domain": "civic_administration",
        "orm": "Foddaa tokko irratti kaffalaatii nagahee keessan fudhadhaa, dhimmi keessan haa xumuramu!",
        "amh": "በመስኮት አንድ ከፍለው ደረሰኝዎን ይውሰዱ፣ ጉዳይዎ በተሳካ ሁኔታ ይፈጸም!",
        "tir": "ኣብ መስኮት ሓደ ኸፊልኩም ቅብሊትኩም ውሰዱ፣ ጉዳይኩም ብዓወት ይፈጸም!",
        "som": "Ku bixi daaqadda koowaad oo qaado rasiidkaaga, arrintaaduna si guul leh ha u hirgasho!",
        "eng": "Pay at counter one, take your receipt, and may your administrative matter be successfully resolved!",
    },
]

# ──────────────────────────────────────────────────────────────────
# SCENARIO 6: Commercial Banking & Mobile Money
# Exactly 14 multi-turn dialogue turns across 5 languages (280 directed pairs)
# ──────────────────────────────────────────────────────────────────
BANKING_CORPUS: list[dict[str, str]] = [
    {
        "domain": "commercial_banking",
        "orm": "Akkam jirtu, herrega qusannaa koo keessatti maallaqa callaa galchuu nan barbaada.",
        "amh": "ጤና ይስጥልኝ፣ ወደ ቁጠባ ሂሳቤ ጥሬ ገንዘብ ማስገባት እፈልጋለሁ።",
        "tir": "ከመይ ኣለኹም፣ ናብ ናይ ቁጠባ ሕሳበይ ጥረ ገንዘብ ከእቱ እደሊ ኣለኹ።",
        "som": "Nabadeey, waxaan rabaa inaan lacag caddaan ah ku shubo akoonkayga kaydka.",
        "eng": "Hello, I would like to deposit cash into my savings account.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Waraqaa eenyummaa keessanii fi dabalata baankii keessan lakkoofsa herregaan wajjin naaf kennaa.",
        "amh": "እባክዎን የቀበሌ መታወቂያዎን እና የባንክ ደብተርዎን ከሂሳብ ቁጥሩ ጋር ይስጡኝ።",
        "tir": "በጃኹም ናይ ቀበሌ መንነት ወረቐትኩምን ናይ ባንክ ደብተርኩምን ምስ ቍጽሪ ሕሳቡ ሃቡኒ።",
        "som": "Fadlan i sii kaarkaaga aqoonsiga iyo buugga bangiga oo uu ku qoran yahay lambarka akoonku.",
        "eng": "Please hand me your identification card and your passbook with the account number.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Waraqaa galii guutamee fi birrii kuma kudha shan qulqulluun qabadheen jira.",
        "amh": "የተሞላውን የገንዘብ ማስገቢያ ሰነድ እና አስራ አምስት ሺህ ብር ጥሬ ገንዘብ ይኸውልዎት።",
        "tir": "እተመልአ ናይ ምእታው ፎርምን ዓሰርተ ሓሙሽተ ሽሕ ቅርሺ ጥረ ገንዘብን እንሆልኩም።",
        "som": "Waa kan foomkii dhigaalka oo buuxa iyo shan iyo toban kun oo Birr oo caddaan ah.",
        "eng": "Here is the completed deposit slip and fifteen thousand Birr in cash.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Maashiniin maallaqicha lakkaa'eera, sirrii birrii kuma kudha shan ta'uu isaa mirkaneesseera.",
        "amh": "ገንዘቡ በማሽን ተቆጥሯል፣ ትክክል አስራ አምስት ሺህ ብር መሆኑ ተረጋግጧል።",
        "tir": "እቲ ገንዘብ ብማሽን ተቖጺሩ እዩ፣ ልክዕ ዓሰርተ ሓሙሽተ ሽሕ ቅርሺ ምዃኑ ተረጋጊጹ።",
        "som": "Lacagta waxaa lagu tiriyay mishiinka, waxaana la xaqiijiyay inay tahay sax shan iyo toban kun oo Birr.",
        "eng": "The cash has been machine-counted, and exactly fifteen thousand Birr is confirmed.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Herrega baankii koo kana moobaayil baankingii fi Teeleebirrii wajjin wal qabsiisuun danda'aa?",
        "amh": "ይህንን የባንክ ሂሳቤን ከሞባይል ባንኪንግ እና ከቴሌብር ጋር ማገናኘት እችላለሁ?",
        "tir": "ነዚ ናይ ባንክ ሕሳበይ ምስ ሞባይል ባንኪንግን ቴሌብርን ከተሓሕዞ እኽእልዶ?",
        "som": "Akoonkaygan bangiga ma ku xiriiri karaa bangiga mobaylka iyo Telebirr?",
        "eng": "Can I link this bank account with mobile banking and Telebirr?",
    },
    {
        "domain": "commercial_banking",
        "orm": "Eeyyee, foomii tajaajila dijitaalaa mallatteessuudhaan koodii USSD fi appii bilbilaa fayyadamuu dandeessu.",
        "amh": "አዎ፣ የዲጂታል አገልግሎት ፎርም በመፈረም በUSSD ኮድ እና በስልክ መተግበሪያ መጠቀም ይችላሉ።",
        "tir": "እወ፣ ናይ ዲጂታል ኣገልግሎት ፎርም ብምፍራም ብUSSD ኮድን ናይ ሞባይል ኣፕን ክትጥቀሙ ትኽእሉ ኢኹም።",
        "som": "Haa, adigoo saxiixaya foomka adeegga dhijitaalka ah waxaad isticmaali kartaa koodhka USSD iyo barnaamijka mobaylka.",
        "eng": "Yes, by signing the digital service form you can use USSD codes and the mobile app.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Guyyaatti gara baankii biraatti hangam daddabarsuu danda'a, kaffaltiin tajaajilaa meeqa?",
        "amh": "በቀን ወደ ሌላ ባንክ ምን ያህል ማስተላለፍ እችላለሁ፣ የአገልግሎት ክፍያው ስንት ነው?",
        "tir": "ኣብ መዓልቲ ናብ ካልእ ባንክ ክንደይ ከመሓላልፍ እኽእል፣ ናይ ኣገልግሎት ክፍሊት ክንዲ ምንታይ እዩ?",
        "som": "Maalintii intee baan u wareejin karaa bangi kale, waana imisa khidmadda adeeggu?",
        "eng": "How much can I transfer to another bank per day, and what is the transaction fee?",
    },
    {
        "domain": "commercial_banking",
        "orm": "Karaa EthSwitch hanga birrii kuma dhibba tokkootti kaffaltii xiqqaan daqiiqaa muraasa keessatti darba.",
        "amh": "በኢትስዊች በኩል እስከ አንድ መቶ ሺህ ብር በትንሽ ክፍያ በጥቂት ደቂቃዎች ውስጥ ይተላለፋል።",
        "tir": "ብኢትስዊች ኣቢልኩም ክሳብ ሓደ ሚእቲ ሽሕ ቅርሺ ብንእሽቶ ክፍሊት ኣብ ውሽጢ ሒደት ደቓይቕ ይመሓላለፍ።",
        "som": "Iyadoo loo marayo EthSwitch ilaa boqol kun oo Birr waxay ku gudbaysaa daqiiqado gudahood iyadoo khidmad yar leh.",
        "eng": "Via EthSwitch you can transfer up to one hundred thousand Birr within minutes for a small fee.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Galgala kaleessaa kaardiin eetiyeemii koo maashina baankii kanarraatti na jalaa liqimfameera.",
        "amh": "ትናንት ማታ የኤቲኤም ካርዴ እዚህ ባንክ ማሽን ላይ ተውጦብኛል።",
        "tir": "ትማሊ ምሸት ናይ ኤቲኤም ካርደይ ኣብዚ ማሽን ባንኪ ተወሓጢኒ።",
        "som": "Xalay fiidkii kaarkaygii ATM-ka waxaa liqay mishiinka bangigan.",
        "eng": "Yesterday evening my ATM card was captured by this branch's ATM machine.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Nagaheen eetiyeemii kenname yoo jiraate waraqaa eenyummaa keessan wajjin kennaa, maashinicha keessaa ni baafna.",
        "amh": "የኤቲኤሙ ደረሰኝ ካለዎት ከመታወቂያዎ ጋር ይስጡን፣ ከማሽኑ ውስጥ አውጥተን እንሰጥዎታለን።",
        "tir": "ናይቲ ኤቲኤም ቅብሊት እንተሃልዩኩም ምስ መንነት ወረቐትኩም ሃቡና፣ ካብቲ ማሽን ኣውጺእና ክንህበኩም ኢና።",
        "som": "Haddii aad haysato rasiidkii ATM-ka fadlan noo dhiib adigoo wata kaarkaaga aqoonsiga, mishiinkana waanu ka soo saaraynaa.",
        "eng": "If you have the ATM transaction slip, please show it with your ID and we will retrieve it from the machine.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Maatii koo irraa hawaalaan doolaara Ameerikaa dhufeera, sharafa biyyaalessaan baasuu barbaada.",
        "amh": "ከቤተሰቦቼ በአሜሪካ ዶላር የተላከ ሐዋላ አለኝ፣ በህጋዊ የባንክ ምንዛሬ ማውጣት እፈልጋለሁ።",
        "tir": "ካብ ስድራቤተይ ብናይ ኣመሪካ ዶላር እተላእከ ሓዋላ ኣሎኒ፣ ብሕጋዊ ናይ ባንክ ሸርፊ ከውጽኦ እደሊ ኣለኹ።",
        "som": "Waxaa iiga yimid qoyskayga xawaalad doolarka Maraykanka ah, waxaan rabaa inaan ku qaato sarrifka rasmiga ah ee bangiga.",
        "eng": "I have a foreign remittance in US dollars from family, and I wish to cash it out at the official bank exchange rate.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Koodii icciitii hawaalaa lakkofsa saddeetii fi maqaa nama ergee nuuf himaa.",
        "amh": "እባክዎን የስምንት አሃዝ የሐዋላውን ሚስጥር ቁጥር እና የላኪውን ሙሉ ስም ይንገሩን።",
        "tir": "በጃኹም ናይቲ ሓዋላ ናይ ሸሞንተ ኣሃዝ ምስጢር ቍጽርን ናይቲ ሰዳዲ ምሉእ ስምን ንገሩና።",
        "som": "Fadlan noo sheeg koodhka sirta ah ee xawaaladda oo sideed lambar ah iyo magaca buuxa ee qofka soo diray.",
        "eng": "Please provide the eight-digit remittance secret code and the sender's full name.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Ibsa herrega baankii ji'oota jaha darbanii chaappaa seera qabeessaan naaf maxxansaa.",
        "amh": "ያለፉትን ስድስት ወራት የባንክ ሂሳብ መግለጫ በህጋዊ ማህተም ታትሞ ይሰጠኝ።",
        "tir": "ናይ ዝሓለፉ ሽዱሽተ ኣዋርሕ መግለጺ ሕሳብ ብሕጋዊ ማሕተም ተሓቲሙ ይወሃበኒ።",
        "som": "Fadlan ii dabaa bayaanka xisaabta bangiga ee lixdii bilood ee u dambeeyay oo wata shaabadda rasmiga ah.",
        "eng": "Please print my bank account statement for the past six months stamped with the official seal.",
    },
    {
        "domain": "commercial_banking",
        "orm": "Nagaheen galii fi dabalanni herregaa kunooti, maallaqni keessan haa eebbifamu!",
        "amh": "የተቀማጭ ደረሰኝዎ እና የተስተካከለው የባንክ ደብተርዎ ይኸውልዎት፣ ገንዘብዎ ይባረክ!",
        "tir": "ናይ ተቐማጢ ቅብሊትኩምን እተዓረየ ደብተር ባንክኹምን እንሆልኩም፣ ገንዘብኩም ይባረኽ!",
        "som": "Waa kan rasiidkii dhigaalka iyo buuggii xisaabta ee la cusboonaysiiyay, lacagtiinuna ha barakoowdo!",
        "eng": "Here is your deposit receipt and updated passbook, and may your wealth and finances be blessed!",
    },
]

# ──────────────────────────────────────────────────────────────────
# SCENARIO 7: School & University Administration
# Exactly 14 multi-turn dialogue turns across 5 languages (280 directed pairs)
# ──────────────────────────────────────────────────────────────────
SCHOOL_CORPUS: list[dict[str, str]] = [
    {
        "domain": "school_administration",
        "orm": "Akkam jirtu, biiroo rejistiraaraa fi kaffaltii barumsaa eessatti argadha?",
        "amh": "ጤና ይስጥልኝ፣ የሬጅስትራር ቢሮ እና የትምህርት ክፍያ መስኮት የት ይገኛል?",
        "tir": "ከመይ ኣለኹም፣ ናይ ሬጅስትራር ቤት ጽሕፈትን ናይ ክፍሊት ትምህርቲ መስኮትን ኣበይ ይርከብ?",
        "som": "Nabadeey, xaggee baan ka heli karaa xafiiska diiwaangeliyaha iyo daaqadda lacag-bixinta?",
        "eng": "Hello, where can I find the registrar's office and tuition payment counter?",
    },
    {
        "domain": "school_administration",
        "orm": "Gama kutaa lamaffaa jirti, galmee haaraaf moo tiraanskiriiptii barbaaddanii dhuftan?",
        "amh": "ማዶ በሁለተኛው ፎቅ ላይ ነው፣ ለአዲስ ምዝገባ ወይስ ኦፊሴላዊ ትራንስክሪፕት ፍለጋ መጡ?",
        "tir": "ኣብቲ ማዶ ኣብ ካልኣይ ደብሪ ኣሎ፣ ንሓዲሽ ምዝገባ ዲኹም ወይስ ወግዓዊ ትራንስክሪፕት ደሊኹም መጺእኩም?",
        "som": "Waxay ku taallaa dabaqa labaad ee ka soo horjeeda, ma waxaad u timid diiwaangelin cusub mise shahaadada natiijooyinka?",
        "eng": "It is across on the second floor; have you come for new enrollment or for an official transcript?",
    },
    {
        "domain": "school_administration",
        "orm": "Waraqaa ragaa digirii koo fi kooppii tiraanskiriiptii ifaa embaasiif qophaa'u nan barbaada.",
        "amh": "የዲግሪ ምስክር ወረቀቴን እና ለኤምባሲ የሚሆን ይፋዊ የትራንስክሪፕት ቅጅ እፈልጋለሁ።",
        "tir": "ናይ ዲግሪ ምስክር ወረቐተይን ንኤምባሲ ዝኸውን ወግዓዊ ቅዳሕ ትራንስክሪፕትን እደሊ ኣለኹ።",
        "som": "Waxaan u baahanahay shahaadada darajada jaamacadeed iyo koobi rasmi ah oo transcript ah oo loogu talagalay safaaradda.",
        "eng": "I need my degree certificate and an official transcript copy prepared for an embassy.",
    },
    {
        "domain": "school_administration",
        "orm": "Tiraanskiriiptii ifaa fudhachuuf waraqaa qulqullinaa fi ragaa kaffaltii baasii qooddachuu dhiheessuu qabdu.",
        "amh": "ይፋዊ ትራንስክሪፕት ለመውሰድ የመውጫ ክሊራንስ እና የኮስት ሼሪንግ ክፍያ ማረጋገጫ ማቅረብ አለብዎት።",
        "tir": "ወግዓዊ ትራንስክሪፕት ንምውሳድ ናይ መወዳእታ ክሊራንስን ናይ ኮስት ሸሪንግ ክፍሊት መረጋገጽን ከተቕርቡ ኣለኩም።",
        "som": "Si aad u hesho transcript-ka rasmiga ah waa inaad keentaa warqadda fasaxa (clearance) iyo caddeynta bixinta kharash-wadaagga.",
        "eng": "To receive an official transcript, you must present a clearance form and proof of cost-sharing payment.",
    },
    {
        "domain": "school_administration",
        "orm": "Waraqaa eenyummaa barataa koo fi xalayaa qulqullinaa yuunivarsiitiin mallatteesse kunooti.",
        "amh": "የተማሪ መታወቂያዬ እና በዩኒቨርሲቲው የተፈረመው የክሊራንስ ደብዳቤ ይኸውልዎት።",
        "tir": "ናይ ተማሃራይ መንነት ወረቐተይን ብዩኒቨርሲቲ እተፈርመ ናይ ክሊራንስ ደብዳበን እንሆልኩም።",
        "som": "Waa kan kaarkaygii aqoonsiga ardayga iyo warqaddii fasaxa ee jaamacaddu saxiixday.",
        "eng": "Here is my student ID card and the official clearance letter signed by the university.",
    },
    {
        "domain": "school_administration",
        "orm": "Sanadni keessan guutuu dha, guyyoota hojii sadii booda dhuftanii chaappaan fudhachuu dandeessu.",
        "amh": "ሰነድዎ የተሟላ ነው፣ ከሶስት የስራ ቀናት በኋላ መጥተው በማህተም የተረጋገጠውን መውሰድ ይችላሉ።",
        "tir": "ሰነድኩም ምሉእ እዩ፣ ድሕሪ ሰለስተ ናይ ስራሕ መዓልታት መጺእኩም ብማሕተም እተረጋገጸ ክትወስዱ ትኽእሉ ኢኹም።",
        "som": "Dukumentigaagu waa dhammaystiran yahay, waxaad ku qaadan kartaa saddex maalmood oo shaqo kadib isagoo shaabadeysan.",
        "eng": "Your documents are complete; you can pick up the sealed transcript after three working days.",
    },
    {
        "domain": "school_administration",
        "orm": "Koorsii samiisteera kanaa dabalataan galmeessuuf yookiin haquuf hanga yoomiitti eeyyamama?",
        "amh": "የዚህን ሴሚስተር ትምህርቶች ለመጨመር ወይም ለመሰረዝ የአድ-ድሮፕ ጊዜው እስከ መቼ ነው?",
        "tir": "ናይዚ ሰሚስተር ትምህርትታት ንምውሳኽ ወይ ንምስራዝ ናይ ኣድ-ድሮፕ ግዜ ክሳብ መዓስ እዩ?",
        "som": "Waqtiga ku darista ama ka noqoshada koorsooyinka simistarkan ilaa goormaa la oggol yahay?",
        "eng": "Until when is the add-drop period open to add or drop courses for this semester?",
    },
    {
        "domain": "school_administration",
        "orm": "Jum'aa dhufu sa'aatii kudha tokko irratti galmeen koorsii add-drop guutummaatti cufama.",
        "amh": "የሚመጣው አርብ ከቀኑ አስራ አንድ ሰዓት ላይ የትምህርት ምዝገባው እና አድ-ድሮፕ ሙሉ በሙሉ ይዘጋል።",
        "tir": "ዝመጽእ ዓርቢ ሰዓት ዓሰርተ ሓደ ናይ ድሕሪ ቐትሪ ናይ ትምህርቲ ምዝገባን ኣድ-ድሮፕን ምሉእ ብምሉእ ይዕጾ።",
        "som": "Jimcaha soo socda shanta galabnimo ayaa gebi ahaanba la xiri doonaa diiwaangelinta koorsooyinka.",
        "eng": "Next Friday at five PM course registration and add-drop will be completely closed.",
    },
    {
        "domain": "school_administration",
        "orm": "Sagantaan qormaata xumuraa fi galmi qormaataa eessatti maxxanfama?",
        "amh": "የማጠቃለያ ፈተና የጊዜ ሰሌዳ እና የፈተና ክፍሎች ድልድል የት ይለጠፋል?",
        "tir": "ናይ መዛዘሚ ፈተና ናይ ግዜ ሰሌዳን ናይ ፈተና ኣዳራሻት ምደባን ኣበይ ይልጠፍ?",
        "som": "Jadwalka imtixaanka ugu dambeeya iyo qolalka imtixaanka xaggee lagu dhajiyaa?",
        "eng": "Where is the final examination timetable and exam hall allocation posted?",
    },
    {
        "domain": "school_administration",
        "orm": "Gabatee beeksisaa kooppasiitti fi poortaalii barattootaa irratti lakkofsa galmee keessaniin ilaalaa.",
        "amh": "በዋናው ማስታወቂያ ሰሌዳ እና በተማሪዎች የድረ-ገጽ ፖርታል ላይ በመለያ ቁጥርዎ መመልከት ይችላሉ።",
        "tir": "ኣብቲ ዓቢ ናይ መወዓውዒ ሰሌዳን ኣብ ናይ ተመሃሮ መርበብ ሓበሬታ ፖርታልን ብመለለዪ ቍጽርኹም ርኣዩ።",
        "som": "Waxaad kaga eegi kartaa sabuuradda ogeysiisyada ee xarunta iyo barta ardayda lambarkaaga diiwaanka.",
        "eng": "You can view it on the main campus noticeboard and on the student web portal using your ID.",
    },
    {
        "domain": "school_administration",
        "orm": "Barattoota haaraaf kutaan doormii fi sireen eessatti ramadama?",
        "amh": "ለአዲስ ገቢ ተማሪዎች የዶርም ክፍል እና የአልጋ ምደባ በየት በኩል ነው የሚከናወነው?",
        "tir": "ንሓደሽቲ ተመሃሮ ናይ ዶርም ክፍሊን ዓራትን ምደባ በየናይ ወገን እዩ ዝግበር?",
        "som": "Xaggee baa ardayda cusub looga qoondeeyaa qolalka hoyga iyo sariiraha?",
        "eng": "Where is the dormitory room and bed allocation handled for newly admitted students?",
    },
    {
        "domain": "school_administration",
        "orm": "Waajjira jireenya barattootaatti waraqaa galmee qabadhaatii furtuu kutaafi firaashii fudhadhaa.",
        "amh": "ወደ ተማሪዎች አገልግሎት ቢሮ የምዝገባ ወረቀትዎን ይዘው በመሄድ የክፍል ቁልፍ እና ፍራሽ ይረከቡ።",
        "tir": "ናብ ናይ ተመሃሮ ኣገልግሎት ቤት ጽሕፈት ናይ ምዝገባ ወረቐትኩም ሒዝኩም ብምኻድ መፍትሕ ክፍሊን ፍራሽን ተረከቡ።",
        "som": "U qaad warqadda diiwaangelinta xafiiska adeegga ardayda si aad u hesho furaha qolka iyo joodariga.",
        "eng": "Take your registration slip to the student services office to receive your room key and mattress.",
    },
    {
        "domain": "school_administration",
        "orm": "Ayyaana eebbaatiif gaawunii fi qophii waraqaa eebbaa eessatti xumuruu dandeenya?",
        "amh": "ለምረቃ በዓል የምረቃ ጋውን እና ሌሎች ቅድመ-ዝግጅቶችን የት ነው የምናጠናቅቀው?",
        "tir": "ንናይ ምረቓ በዓል ናይ ምረቓ ጋውንን ካልኦት ምድላዋትን ኣበይ ኢና እነጻፍፍ?",
        "som": "Xaggee baan ku dhammaystiri karnaa marada qalin-jabinta iyo u diyaargarowga munaasabadda?",
        "eng": "Where can we finalize graduation gowns and arrangements for the commencement ceremony?",
    },
    {
        "domain": "school_administration",
        "orm": "Hoolii guddaa duraatti gaawunii fudhadhaa, barumsi keessan siif haa ifu, baay'ee baga gammaddan!",
        "amh": "ከዋናው አዳራሽ ፊት ለፊት ጋውኑን ውሰዱ፣ ትምህርታችሁ ያብራችሁ፣ እንኳን ደስ አላችሁ!",
        "tir": "ኣብ ቅድሚ ዓቢ ኣዳራሽ ጋውን ውሰዱ፣ ትምህርትኹም የብርሃልኩም፣ እንቋዕ ሓጐሰኩም!",
        "som": "Hoolka weyn hortiisa ka qaata marada qalin-jabinta, waxbarashadiinnu ha idiin iftiinto, hambalyo weyn!",
        "eng": "Collect your gown in front of the grand hall; may your education illuminate your future, and warmest congratulations!",
    },
]

# ──────────────────────────────────────────────────────────────────
# SCENARIO 8: Police Station & Legal Dispute Resolution
# Exactly 14 multi-turn dialogue turns across 5 languages (280 directed pairs)
# ──────────────────────────────────────────────────────────────────
POLICE_CORPUS: list[dict[str, str]] = [
    {
        "domain": "legal_police",
        "orm": "Akkam jirtu, sa'aatii muraasa dura manni koo waan hatameef iyyannoo yakkaa galmeessuun barbaada.",
        "amh": "ጤና ይስጥልኝ፣ ከጥቂት ሰዓታት በፊት ቤቴ በሌባ ስለተሰበረ የወንጀል አቤቱታ ማስመዝገብ እፈልጋለሁ።",
        "tir": "ከመይ ኣለኹም፣ ቅድሚ ሒደት ሰዓታት ቤተይ ብሰራቒ ስለ እተሰርቀ ናይ ገበን ጥርዓን ከምዝግብ እደሊ ኣለኹ።",
        "som": "Nabadeey, dhowr saacadood ka hor gurigayga ayaa la jabsaday oo la xaday, waxaana rabaa inaan diiwaangeliyo cabasho dambiyeed.",
        "eng": "Hello, a few hours ago my home was broken into and burglarized; I want to file a formal crime report.",
    },
    {
        "domain": "legal_police",
        "orm": "Nagaa qabaadhaa, yeroo kam raawwatamee fi meeshaaleen jalaa hataman maal fa'i?",
        "amh": "እባክዎን ይረጋጉ፣ ድርጊቱ የተፈጸመው በየትኛው ሰዓት ነው እና የተሰረቁት እቃዎች ምንድናቸው?",
        "tir": "በጃኹም ህድእ በሉ፣ እቲ ተግባር እተፈጸመሉ ሰዓት መዓስ እዩ እተሰረቑ ኣቑሑትከ እንታይ እዮም?",
        "som": "Fadlan is deji, goormaa ayay dhacday maxayse yihiin alaabta lagaa xaday?",
        "eng": "Please remain calm; what time did the incident occur and what specific items were stolen?",
    },
    {
        "domain": "legal_police",
        "orm": "Laaptooppiin hojii, bilbilli harkaa, birrii kuma afurtamaa fi paaspoortiin maatii koo hatameera.",
        "amh": "የስራ ላፕቶፕ፣ ስልክ፣ አርባ ሺህ ብር ጥሬ ገንዘብ እና የቤተሰቤ ፓስፖርቶች ተሰርቀዋል።",
        "tir": "ናይ ስራሕ ላፕቶፕ፣ ተንቀሳቓሲ ስልኪ፣ ኣርብዓ ሽሕ ቅርሺ ጥረ ገንዘብን ናይ ስድራቤተይ ፓስፖርታትን ተሰሪቖም እዮም።",
        "som": "Waxaa la xaday laptop-kaygii shaqada, taleefankaygii, afartan kun oo Birr oo caddaan ah, iyo baasaboorradii qoyskayga.",
        "eng": "My work laptop, smartphone, forty thousand Birr in cash, and my family's passports were stolen.",
    },
    {
        "domain": "legal_police",
        "orm": "Poolisii qorataa yakkaa guyyaa har'aa waamee jecha keessan fuula duraatti akka qabatu nan godha.",
        "amh": "የዕለቱን የወንጀል መርማሪ ፖሊስ ጠርቼ ቃልዎን በዝርዝር እንዲመዘግብ አደርጋለሁ።",
        "tir": "ነቲ ናይቲ መዓልቲ መርማሪ ፖሊስ ገበን ጸዊዐ ቃልኩም ብዝርዝር ክምዝግብ ክገብር እየ።",
        "som": "Waxaan u yeerayaa sarkaalka baareha dambiyada ee maanta jooga si uu qoraal rasmi ah kaaga qaado.",
        "eng": "I will call today's duty criminal investigator to take down your detailed formal statement.",
    },
    {
        "domain": "legal_police",
        "orm": "Mallattoon caccabuu balbalaa jiraa, nama shakkamu yookiin kaameraa nageenyaa qabduu?",
        "amh": "የበር መሰበር ወይም መገንጠል ምልክት አለ ወይ፣ የተጠረጠረ ሰው ወይም የጥበቃ ካሜራ መረጃ አላችሁ?",
        "tir": "ናይ ማዕጾ ምስባር ምልክት ኣሎዶ፣ እትጠርጥርዎ ሰብ ወይ ናይ ጸጥታ ካሜራ መርትዖ ኣለኩምዶ?",
        "som": "Ma jiraan wax calaamado ah oo muujinaya in albaabka la jabiyay, ma jiraa qof aad ka shakisan tahay ama kamaradaha amniga?",
        "eng": "Are there signs of forced door entry, any suspected individuals, or security camera surveillance footage?",
    },
    {
        "domain": "legal_police",
        "orm": "Ollaan koo nama uffata gurraacha uffate yoo fiigu argeera, kaameraan suuraa isaa qabateera.",
        "amh": "ጎረቤቴ ጥቁር ልብስ የለበሰ ሰው ሲሮጥ አይቷል፣ የደህንነት ካሜራውም ምስሉን ቀርጾታል።",
        "tir": "ጐረቤተይ ጸሊም ክዳን ዝተኸድነ ሰብ እናጐየየ ርእይዎ እዩ፣ ናይ ድሕንነት ካሜራ'ውን ስእሉ ቀሪጽዎ ኣሎ።" ,
        "som": "Deriskaygu wuxuu arkay nin dhar madow xiran oo ordaya, kamaradda amniguna waxay duubtay muuqaalkiisa.",
        "eng": "My neighbor saw a man in black clothing fleeing the scene, and our security camera recorded his image.",
    },
    {
        "domain": "legal_police",
        "orm": "Galmee qorannoo banaatii fiilmii sanadaa fudhannee ashaaraa qubaa sakatta'uuf gara manichaatti deemna.",
        "amh": "የምርመራ መዝገብ ከፍተን የቪዲዮ ማስረጃውን እንወስዳለን፣ የጣት አሻራ ለማንሳትም ወደ ቤቱ እንሄዳለን።",
        "tir": "ናይ መርመራ መዝገብ ከፊልና ነቲ ናይ ቪድዮ መርትዖ ክንወስዶ ኢና፣ ናይ ኣጻብዕቲ ኣሰር ንምውሳድ ድማ ናብቲ ገዛ ክንከይድ ኢና።",
        "som": "Waxaan furi doonaa gal-dacwadeed baaris, waxaan qaadan doonaa muuqaalka, waxaana aadi doonaa guriga si aan faraha uga soo qaadno.",
        "eng": "We will open an investigation file, secure the video evidence, and dispatch a forensics unit to dust for fingerprints.",
    },
    {
        "domain": "legal_police",
        "orm": "Jecha keessan dubbisaatii mirkaneessaa, dhuma irratti maqaa guutuu fi mallattoo keessan kaa'aa.",
        "amh": "የሰጡትን ቃል አንብበው ያረጋግጡ፣ በመጨረሻው ገጽ ላይ ሙሉ ስምዎን ጽፈው ይፈርሙ።",
        "tir": "እቲ ዝሃብክምዎ ቃል ኣንቢብኩም ኣረጋግጹ፣ ኣብ መወዳእታ ምሉእ ስምኩም ጽሒፍኩም ፈርሙ።",
        "som": "Fadlan akhri qoraalkaaga markhaatiga si aad u xaqiijiso, dabadeedna ku saxiix magacaaga buuxa.",
        "eng": "Please read over your written statement to verify its accuracy, and sign with your full name at the bottom.",
    },
    {
        "domain": "legal_police",
        "orm": "Paaspoortii fi baankii beeksisuuf waraqaa xalayaa ragaa poolisii naaf kennuu dandeessuu?",
        "amh": "ፓስፖርት ለማሳገድ እና ለባንክ ለማሳወቅ የፖሊስ ማስረጃ ደብዳቤ ልትሰጡኝ ትችላላችሁ?",
        "tir": "ፓስፖርት ንምእጋድን ንባንክ ንምሕባርን ናይ ፖሊስ መርትዖ ደብዳበ ክትህቡኒ ትኽእሉዶ?",
        "som": "Ma i siin kartaa warqad caddeyn boolis ah oo rasmi ah si aan u wargeliyo bangiga iyo xafiiska baasaboorka?",
        "eng": "Could you issue an official police incident confirmation letter for the bank and passport authority?",
    },
    {
        "domain": "legal_police",
        "orm": "Chaappaa seera qabeessaa fi lakkoofsa galmee qorannootiin xalayaan mirkaneessaa ni kennama.",
        "amh": "በህጋዊ ማህተም እና በምርመራ መዝገብ ቁጥር የተረጋገጠ ደብዳቤ ወዲያውኑ ይሰጥዎታል።",
        "tir": "ብሕጋዊ ማሕተምን ብናይ መርመራ መዝገብ ቍጽርን እተረጋገጸ ደብዳበ ብኡንብኡ ክወሃበኩም እዩ።",
        "som": "Waxaa isla markiiba laguu soo saari doonaa warqad xaqiijin ah oo wadata shaabadda rasmiga ah iyo lambarka galka.",
        "eng": "An official confirmation letter with an authentic seal and crime reference number will be provided right away.",
    },
    {
        "domain": "legal_police",
        "orm": "Akkasumas wal dhabdee daangaa lafaa ollaa koo wajjin qabnu araaraan xumuruu dandeenyaa?",
        "amh": "እንዲሁም ከጎረቤቴ ጋር ያለብንን የይገባኛል ወሰን አለመግባባት በሽምግልናና እርቅ መጨረስ እንችላለን?",
        "tir": "ከምኡ'ውን ምስ ጐረቤተይ ዘሎ ናይ ዶብ መሬት ዘይምርድዳእ ብሽምግልናን ዕርቅን ክንውድኦ ንኽእልዶ?",
        "som": "Sidoo kale, khilaafka xudduudda dhulka ee naga dhexeeya aniga iyo deriskayga ma ku xallin karnaa dhex-dhexaadin?",
        "eng": "Can we also resolve a land boundary dispute with my neighbor through peaceful mediation and reconciliation?",
    },
    {
        "domain": "legal_police",
        "orm": "Jaarsolii biyyaa fi poolisii hawaasaatiin dhimma nageenyaa araaraan furuun seeraan ni eeyyamama.",
        "amh": "በሀገር ሽማግሌዎች እና በማህበረሰብ አቀፍ ፖሊስ በኩል ሰላማዊ እርቅ ማውረድ በህግ የተፈቀደ ነው።",
        "tir": "ብዓበይቲ ዓድን ብናይ ማሕበረሰብ ፖሊስን ኣቢልካ ሰላማዊ ዕርቂ ምፍጻም ብሕጊ እተፈቕደ እዩ።",
        "som": "Waxaa sharcigu oggol yahay in khilaafaadka noocaas ah lagu xalliyo odayaasha dhaqanka iyo booliska bulshada.",
        "eng": "Settling civil matters peacefully through respected elders and community policing is legally encouraged.",
    },
    {
        "domain": "legal_police",
        "orm": "Guyyaa qabamee fi lakkoofsa galmee koo naaf himaa, yoom deebi'ee dhiyaadha?",
        "amh": "የተሰጠኝን የመዝገብ ቁጥር ይንገሩኝ፣ ለክትትል መቼ ነው ተመልሼ መምጣት ያለብኝ?",
        "tir": "እተዋህበኒ ናይ መዝገብ ቍጽሪ ንገሩኒ፣ ንክትትል መዓስ እየ ተመሊሰ ክመጽእ ዘለኒ?",
        "som": "Fadlan ii sheeg lambarka galkayga dacwadda, goormaan ku soo laabtaa dabagalka?",
        "eng": "Please give me my case file number, and when should I return to follow up on the investigation?",
    },
    {
        "domain": "legal_police",
        "orm": "Lakkofsi galmee kurnooti, gareen sakatta'insaa ni hordofa, dhugaa fi haqi ni injifata!",
        "amh": "የመዝገብ ቁጥርዎ ይኸውልዎት፣ የምርመራ ቡድኑ ሌባውን ይከታተላል፣ እውነትና ፍትህ ያሸንፋል!",
        "tir": "ናይ መዝገብ ቍጽርኩም እንሆልኩም፣ ናይ መርመራ ጉጅለ ነቲ ሰራቒ ክከታተሎ እዩ፣ ሓቅን ፍትሕን ይስዕር!",
        "som": "Waa kan lambarka galkaaga, kooxda baaristu waxay daba-gali doontaa tuugga, runta iyo caddaaladdu way guulaysan doontaa!",
        "eng": "Here is your crime file number; our investigative unit will pursue the suspect, and truth and justice shall prevail!",
    },
]


def seed_scenario(corpus: list[dict[str, str]], tag: str) -> int:
    tm = TranslationMemory.get_instance()
    langs = ["orm", "amh", "tir", "som", "eng"]
    records_to_insert = []

    for entry in corpus:
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
                    "dataset": f"scenario_{tag}",
                    "confidence": 1.0,
                })

    inserted = tm.bulk_insert(records_to_insert, bidirectional=False)
    print(f"[{tag.upper()}] Successfully seeded {inserted} pairs into TM!")
    return inserted


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed scenario dialogues into TM.")
    parser.add_argument("--scenario", choices=["clinic", "road", "cafe", "market", "kebele", "banking", "school", "police", "all"], default="police")
    args = parser.parse_args()

    tm = TranslationMemory.get_instance()
    print("Initial TM count:", tm.count())

    if args.scenario in ("clinic", "all"):
        seed_scenario(CLINIC_CORPUS, "clinic")
    if args.scenario in ("road", "all"):
        seed_scenario(ROAD_CORPUS, "road")
    if args.scenario in ("cafe", "all"):
        seed_scenario(CAFE_CORPUS, "cafe")
    if args.scenario in ("market", "all"):
        seed_scenario(MARKET_CORPUS, "market")
    if args.scenario in ("kebele", "all"):
        seed_scenario(KEBELE_CORPUS, "kebele")
    if args.scenario in ("banking", "all"):
        seed_scenario(BANKING_CORPUS, "banking")
    if args.scenario in ("school", "all"):
        seed_scenario(SCHOOL_CORPUS, "school")
    if args.scenario in ("police", "all"):
        seed_scenario(POLICE_CORPUS, "police")

    print("Total in TM now:", tm.count())
