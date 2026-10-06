"""Ethiopian Entity & Colloquial Glossary Normalizer for Lisan.

Ensures accurate translation of Ethiopian greetings, colloquial idioms,
proper nouns, cities, and landmarks that generic NMT models (like NLLB-200) misinterpret.
"""

import re

# English -> Amharic named entities & landmarks
ENG_TO_AMH_GLOSSARY = {
    # Historical & Tourist Cities
    r"\bLalibela\b": "ላሊበላ",
    r"\bAxum\b": "አክሱም",
    r"\bAksum\b": "አክሱም",
    r"\bBahir\s*Dar\b": "ባህር ዳር",
    r"\bBahardar\b": "ባህር ዳር",
    r"\bGondar\b": "ጎንደር",
    r"\bGonder\b": "ጎንደር",
    r"\bAddis\s*Ababa\b": "አዲስ አበባ",
    r"\bFinfinne\b": "ፊንፊኔ",
    r"\bHawassa\b": "ሐዋሳ",
    r"\bAwassa\b": "ሐዋሳ",
    r"\bHarar\b": "ሐረር",
    r"\bDire\s*Dawa\b": "ድሬዳዋ",
    r"\bJimma\b": "ጅማ",
    r"\bMekelle\b": "መቀሌ",
    r"\bMekele\b": "መቀሌ",
    r"\bArba\s*Minch\b": "አርባ ምንጭ",
    r"\bBishoftu\b": "ቢሾፍቱ",
    r"\bDebre\s*Zeit\b": "ደብረ ዘይት",
    r"\bAdama\b": "አዳማ",
    r"\bNazret\b": "ናዝሬት",
    r"\bSemera\b": "ሰመራ",
    r"\bJijiga\b": "ጅጅጋ",
    r"\bAsosa\b": "አሶሳ",
    r"\bGambela\b": "ጋምቤላ",
    # Cultural & Food
    r"\bInjera\b": "እንጀራ",
    r"\bShiro\b": "ሽሮ",
    r"\bDoro\s*Wat\b": "ዶሮ ወጥ",
    r"\bTeff\b": "ጤፍ",
    r"\bTej\b": "ጠጅ",
    r"\bBuna\b": "ቡና",
    r"\bKolo\b": "ቆሎ",
}

# High-precision Amharic to English conversational dictionary
# Catches colloquial phrases before or after NMT
AMH_TO_ENG_EXACT = {
    # Standard Greetings
    "ሰላም": "Hello",
    "ሰላም ነው": "Hello, how are you?",
    "ሰላም ነው?": "Hello, how are you?",
    "ሰላም ነህ": "Hello, how are you?",
    "ሰላም ነህ?": "Hello, how are you?",
    "ሰላም ነክ": "Hello, how are you?",
    "ሰላም ነክ?": "Hello, how are you?",
    "ሰላም ነሽ": "Hello, how are you?",
    "ሰላም ነሽ?": "Hello, how are you?",
    "ሰላም ኖት": "Hello, how are you?",
    "ሰላም ኖት?": "Hello, how are you?",
    "ሰላም ነዎት": "Hello, how are you?",
    "ሰላም ነዎት?": "Hello, how are you?",
    "ሰላም ነው ወንድሜ": "Hello, how are you, my brother?",
    "ሰላም ነው ወንድሜ?": "Hello, how are you, my brother?",
    "ሰላም ወዳጄ": "Hello, my friend.",
    "ሰላም ወዳጄ!": "Hello, my friend!",
    "ሰላም ጤና ይስጥልኝ": "Hello, greetings.",
    "ሰላም እንዴት ነው": "Hello, how are you?",
    "ሰላም እንዴት ነው?": "Hello, how are you?",
    "ሳላም": "Hello",
    "ሳላም!": "Hello!",
    "ስላም": "Hello",
    "ስላም!": "Hello!",
    "ሰላም ወንድሜ": "Hello, my brother.",
    "ሰላም ወንድሜ!": "Hello, my brother!",
    "ሰላም እህቴ": "Hello, my sister.",
    "ሰላም እህቴ!": "Hello, my sister!",
    "ሰላም ናችሁ": "Hello everyone, how are you?",
    "ሰላም ናችሁ?": "Hello everyone, how are you?",
    "ሰላም እንዴት ነህ": "Hello, how are you?",
    "ሰላም እንዴት ነህ?": "Hello, how are you?",
    "ሰላም እንዴት ነክ": "Hello, how are you?",
    "ሰላም እንዴት ነክ?": "Hello, how are you?",
    "ሰላም እንዴት ነህ ወንድሜ": "Hello, how are you, my brother?",
    "ሰላም እንዴት ነህ ወንድሜ?": "Hello, how are you, my brother?",
    "ሰላም ወንድሜ እንዴት ነህ": "Hello, how are you, my brother?",
    "ሰላም ወንድሜ እንዴት ነህ?": "Hello, how are you, my brother?",
    "ሰላም እንዴት ነሽ": "Hello, how are you?",
    "ሰላም እንዴት ነሽ?": "Hello, how are you?",
    "ሰላም እንዴት ነሽ እህቴ": "Hello, how are you, my sister?",
    "ሰላም እንዴት ነሽ እህቴ?": "Hello, how are you, my sister?",
    "ሰላም እንዴት ና": "Hello, how are you?",
    "ሰላም እንዴት ና?": "Hello, how are you?",
    "ሰላም እንዴት ናችሁ": "Hello, how are you all?",
    "ሰላም እንዴት ናችሁ?": "Hello, how are you all?",
    "እንዴት ነህ": "How are you?",
    "እንዴት ነህ?": "How are you?",
    "እንዴት ነህ ወንድሜ": "How are you, my brother?",
    "እንዴት ነህ ወንድሜ?": "How are you, my brother?",
    "እንዴት ነሽ": "How are you?",
    "እንዴት ነሽ?": "How are you?",
    "እንዴት ነሽ እህቴ": "How are you, my sister?",
    "እንዴት ነሽ እህቴ?": "How are you, my sister?",
    "እንዴት ነው": "How are you?",
    "እንዴት ነው?": "How are you?",
    "እንዴት ናችሁ": "How are you all?",
    "እንዴት ናችሁ?": "How are you all?",
    "እንዴት ና": "How are you?",
    "እንዴት ና?": "How are you?",
    "እንዴት ኖት": "How are you?",
    "እንዴት ኖት?": "How are you?",
    "እንደምን አለህ": "How are you?",
    "እንደምን አለህ?": "How are you?",
    "እንደምን አለሽ": "How are you?",
    "እንደምን አለሽ?": "How are you?",
    "እንደምን አላችሁ": "How are you all?",
    "እንደምን አላችሁ?": "How are you all?",
    "ደህና ነህ": "Are you doing well?",
    "ደህና ነህ?": "Are you doing well?",
    "ደህና ነሽ": "Are you doing well?",
    "ደህና ነሽ?": "Are you doing well?",
    "ደህና ናችሁ": "Are you all doing well?",
    "ደህና ናችሁ?": "Are you all doing well?",
    "ደህና ነኝ": "I am fine.",
    "ደህና ነኝ አመሰግናለሁ": "I am fine, thank you.",
    "እግዚአብሔር ይመስገን": "Praise God, I am doing well.",
    "አልሃምዱሊላህ": "Praise be to God, I am fine.",
    # Travel & Conversation
    "ወደ ኢትዮጵያ መጥተህ ታውቃለህ": "Have you ever visited Ethiopia?",
    "ወደ ኢትዮጵያ መጥተህ ታውቃለህ?": "Have you ever visited Ethiopia?",
    "ወደ ኢትዮጵያ መጥተህ ታውቃለህ በሆነ አጋጣሚ መጥተህ ልታውቅ ትችላለህ": "Have you ever visited Ethiopia? Maybe you might visit sometime.",
    "ወደ ኢትዮጵያ መጥተህ ታውቃለህ በሆነ አጋጣሚ መጥተህ ልታውቅ ትችላለህ?": "Have you ever visited Ethiopia? Maybe you might visit sometime.",
    "አዎ ወደ ኢትዮጵያ መጥቼ አውቃለሁ": "Yes, I have visited Ethiopia.",
    "አዎ ወደ ኢትዮጵያ መጥቼ አውቃለሁ ነገር ግን አንተ መጥተህ የምታውቅ አይመስለኝም ወንድሜ ግን መጥተህ ልታውቅ ትችላለህ": "Yes, I have visited Ethiopia, but I don't think you have, my brother. But you could visit sometime.",
    # Time of Day Greetings
    "እንደምን አደርክ": "Good morning.",
    "እንደምን አደርክ?": "Good morning, how did you wake up?",
    "እንደምን አደርሽ": "Good morning.",
    "እንደምን አደርሽ?": "Good morning, how did you wake up?",
    "እንደምን አደራችሁ": "Good morning everyone.",
    "እንደምን አደራችሁ?": "Good morning everyone.",
    "እንደምን ዋልክ": "Good afternoon.",
    "እንደምን ዋልክ?": "Good afternoon, how was your day?",
    "እንደምን ዋልሽ": "Good afternoon.",
    "እንደምን ዋልሽ?": "Good afternoon, how was your day?",
    "እንደምን ዋላችሁ": "Good afternoon everyone.",
    "እንደምን ዋላችሁ?": "Good afternoon everyone.",
    "እንደምን አመሸህ": "Good evening.",
    "እንደምን አመሸህ?": "Good evening.",
    "እንደምን አመሸሽ": "Good evening.",
    "እንደምን አመሸሽ?": "Good evening.",
    "እንደምን አመሻችሁ": "Good evening everyone.",
    "እንደምን አመሻችሁ?": "Good evening everyone.",
    "ደህና እደር": "Good night.",
    "ደህና እደሪ": "Good night.",
    "ደህና እደሩ": "Good night everyone.",
    "ሰላም እደር": "Good night.",
    "ሰላም እደሪ": "Good night.",
    "ሰላም እደሩ": "Good night everyone.",
    "በሰላም ዋልክ": "Good afternoon.",
    "በሰላም ዋልክ?": "Good afternoon, did you have a good day?",
    "በሰላም ዋልሽ": "Good afternoon.",
    "በሰላም ዋልሽ?": "Good afternoon, did you have a good day?",
    "በሰላም ዋላችሁ": "Good afternoon everyone.",
    "በሰላም ዋላችሁ?": "Good afternoon everyone.",
    "በሰላም ዋል": "Have a good day.",
    "በሰላም ግባ": "Have a safe trip home.",
    "በሰላም ግቢ": "Have a safe trip home.",
    "በሰላም ግቡ": "Have a safe trip home everyone.",
    "ደህና ሁን": "Goodbye.",
    "ደህና ሁን ወንድሜ": "Goodbye, my brother.",
    "ደህና ሁን ወንድሜ!": "Goodbye, my brother!",
    "ደህና ሁኚ": "Goodbye.",
    "ደህና ሁኚ እህቴ": "Goodbye, my sister.",
    "ደህና ሁኚ እህቴ!": "Goodbye, my sister!",
    "ደህና ሁኑ": "Goodbye everyone.",
    "ቻው": "Bye.",
    # Courtesies & Common Needs
    "አመሰግናለሁ": "Thank you.",
    "በጣም አመሰግናለሁ": "Thank you very much.",
    "አመሰግናለሁ ወንድሜ": "Thank you, my brother.",
    "ምንም አይደለም": "You're welcome.",
    "ይቅር": "Excuse me / I'm sorry.",
    "ይቅርታ": "Excuse me / I'm sorry.",
    "ይቅርታ አድርግልኝ": "Please forgive me / I apologize.",
    "እባክህ": "Please.",
    "እባክሽ": "Please.",
    "እባክዎ": "Please.",
    "እሺ": "Okay.",
    "እሺ አመሰግናለሁ": "Okay, thank you.",
    "አዎ": "Yes.",
    "አይ": "No.",
    "አይደለም": "No / It is not.",
    "አይደል": "Right? / Isn't that so?",
    "አይደል?": "Right? / Isn't that so?",
    "አይደል ወንድሜ": "Right, my brother?",
    "አይደል ወንድሜ?": "Right, my brother?",
    "ስምህ ማን ነው?": "What is your name?",
    "ስምህ ማን ነው": "What is your name?",
    "ስምሽ ማን ነው?": "What is your name?",
    "ስምሽ ማን ነው": "What is your name?",
    "ዋጋው ስንት ነው?": "How much does it cost?",
    "ዋጋው ስንት ነው": "How much does it cost?",
    "ስንት ነው?": "How much is it?",
    "ስንት ነው": "How much is it?",
    "የት ነው?": "Where is it?",
    "የት ነው": "Where is it?",
    "ሆስፒታል የየት ነው": "Where is the hospital?",
    "ሆስፒታል የት ነው": "Where is the hospital?",
    "ሆስፒታል የት ነው?": "Where is the hospital?",
    "መጸዳጃ ቤት የት ነው?": "Where is the restroom?",
    "መጸዳጃ ቤት የት ነው": "Where is the restroom?",
    "ውሃ እፈልጋለሁ": "I would like water.",
    "ውሃ መጠጣት እፈልጋለሁ": "I want to drink water.",
    "ምግብ እፈልጋለሁ": "I would like food.",
    "መርዳት ትችላለህ?": "Can you help me?",
    "መርዳት ትችላለህ": "Can you help me?",
    "እባክህ እርዳኝ": "Please help me.",
    "እባክህ እርዳኝ!": "Please help me!",
    "እባክሽ እርጂኝ": "Please help me.",
    "ቅናሽ አድርግልኝ": "Can you give me a discount?",
    "ቅናሽ አድርግልኝ?": "Can you give me a discount?",
    "ታክሲ የት ይገኛል": "Where can I find a taxi?",
    "ታክሲ የት ይገኛል?": "Where can I find a taxi?",
    "ምን ፈልገህ ነው": "What do you want?",
    "ምን ፈልገህ ነው?": "What do you want?",
    "የት ልሂድ": "Where should I go?",
    "የት ልሂድ?": "Where should I go?",
    "ዋጋው ውድ ነው": "The price is too expensive.",
    "በጣም ውድ ነው": "It is too expensive.",
}

# English to Amharic common conversational exact mappings
ENG_TO_AMH_EXACT = {
    "hello": "ሰላም",
    "hello!": "ሰላም!",
    "hi": "ሰላም",
    "hi!": "ሰላም!",
    "how are you": "እንዴት ነህ?",
    "how are you?": "እንዴት ነህ?",
    "how are you doing": "እንዴት ነህ?",
    "how are you doing?": "እንዴት ነህ?",
    "good morning": "እንደምን አደርክ",
    "good morning!": "እንደምን አደርክ!",
    "good afternoon": "እንደምን ዋልክ",
    "good afternoon!": "እንደምን ዋልክ!",
    "good evening": "እንደምን አመሸህ",
    "good evening!": "እንደምን አመሸህ!",
    "good night": "ደህና እደር",
    "good night!": "ደህና እደር!",
    "goodbye": "ደህና ሁን",
    "goodbye!": "ደህና ሁን!",
    "bye": "ቻው",
    "bye!": "ቻው!",
    "thank you": "አመሰግናለሁ",
    "thank you!": "አመሰግናለሁ!",
    "thank you very much": "በጣም አመሰግናለሁ",
    "thanks": "አመሰግናለሁ",
    "you're welcome": "ምንም አይደለም",
    "please": "እባክህ",
    "excuse me": "ይቅርታ",
    "sorry": "ይቅርታ",
    "yes": "አዎ",
    "yes!": "አዎ!",
    "no": "አይደለም",
    "no!": "አይደለም!",
    "i am fine": "ደህና ነኝ",
    "i'm fine": "ደህና ነኝ",
    "i am fine, thank you": "ደህና ነኝ አመሰግናለሁ",
    "what is your name": "ስምህ ማን ነው?",
    "what is your name?": "ስምህ ማን ነው?",
    "how much is it": "ስንት ነው?",
    "how much is it?": "ስንት ነው?",
    "how much is this": "ይሄ ዋጋው ስንት ነው?",
    "how much is this?": "ይሄ ዋጋው ስንት ነው?",
    "how much does it cost": "ዋጋው ስንት ነው?",
    "how much does it cost?": "ዋጋው ስንት ነው?",
    "what time is it": "ሰዓቱ ስንት ነው?",
    "what time is it?": "ሰዓቱ ስንት ነው?",
    "where is the hospital": "ሆስፒታል የት ነው?",
    "where is the hospital?": "ሆስፒታል የት ነው?",
    "where is the nearest hospital": "የቅርቡ ሆስፒታል የት ነው?",
    "where is the nearest hospital?": "የቅርቡ ሆስፒታል የት ነው?",
    "where is the clinic": "ክሊኒኩ የት ነው?",
    "where is the clinic?": "ክሊኒኩ የት ነው?",
    "where is the pharmacy": "ፋርማሲው የት ነው?",
    "where is the pharmacy?": "ፋርማሲው የት ነው?",
    "where is the hotel": "ሆቴሉ የት ነው?",
    "where is the hotel?": "ሆቴሉ የት ነው?",
    "where is the bank": "ባንኩ የት ነው?",
    "where is the bank?": "ባንኩ የት ነው?",
    "where is the airport": "ኤርፖርቱ የት ነው?",
    "where is the airport?": "ኤርፖርቱ የት ነው?",
    "where can i find an atm": "ኤቲኤም የት ማግኘት እችላለሁ?",
    "where can i find an atm?": "ኤቲኤም የት ማግኘት እችላለሁ?",
    "where is the restroom": "መጸዳጃ ቤት የት ነው?",
    "where is the restroom?": "መጸዳጃ ቤት የት ነው?",
    "where is the bathroom": "መጸዳጃ ቤት የት ነው?",
    "where is the bathroom?": "መጸዳጃ ቤት የት ነው?",
    "can you help me": "ልትረዳኝ ትችላለህ?",
    "can you help me?": "ልትረዳኝ ትችላለህ?",
    "please help me": "እባክህ እርዳኝ",
    "please help me!": "እባክህ እርዳኝ!",
    "i am hungry": "ርቦኛል",
    "i am hungry.": "ርቦኛል",
    "i'm hungry": "ርቦኛል",
    "i'm hungry.": "ርቦኛል",
    "i am thirsty": "ጠምቶኛል",
    "i am thirsty.": "ጠምቶኛል",
    "i'm thirsty": "ጠምቶኛል",
    "i'm thirsty.": "ጠምቶኛል",
    "i speak english": "እንግሊዝኛ እናገራለሁ",
    "i speak english.": "እንግሊዝኛ እናገራለሁ።",
    "i don't speak english": "እንግሊዝኛ አልናገርም",
    "i don't speak english.": "እንግሊዝኛ አልናገርም",
    "i don't speak amharic": "አማርኛ አልናገርም",
    "i don't speak amharic.": "አማርኛ አልናገርም",
    "call a taxi please": "እባክህ ታክሲ ጥራልኝ",
    "call a taxi please.": "እባክህ ታክሲ ጥራልኝ።",
    "call a taxi, please": "እባክህ ታክሲ ጥራልኝ",
    "call a taxi, please.": "እባክህ ታክሲ ጥራልኝ።",
    "can you give me a discount": "ቅናሽ ልታደርግልኝ ትችላለህ?",
    "can you give me a discount?": "ቅናሽ ልታደርግልኝ ትችላለህ?",
    "give me a discount": "ቅናሽ አድርግልኝ",
    "give me a discount?": "ቅናሽ አድርግልኝ",
    "where can i find a taxi": "ታክሲ የት ማግኘት እችላለሁ?",
    "where can i find a taxi?": "ታክሲ የት ማግኘት እችላለሁ?",
    "it is too expensive": "በጣም ውድ ነው",
    "it is too expensive.": "በጣም ውድ ነው።",
    "it's too expensive": "በጣም ውድ ነው",
    "what are you doing": "ምን እያደረክ ነው?",
    "what are you doing?": "ምን እያደረክ ነው?",
    "see you tomorrow": "ነገ እንገናኝ",
    "see you tomorrow!": "ነገ እንገናኝ!",
    "see you later": "በኋላ እንገናኝ",
    "goodbye my brother": "ደህና ሁን ወንድሜ",
    "goodbye my brother!": "ደህና ሁን ወንድሜ!",
    "goodbye, my brother": "ደህና ሁን ወንድሜ",
    "goodbye, my brother!": "ደህና ሁን ወንድሜ!",
}

# Post-processing fixes for English -> Amharic literal translation patterns
ENG_TO_AMH_POSTPROCESS = [
    (r"(?i)\bረሃብ አለኝ[።\.]?$", "ርቦኛል ።"),
    (r"(?i)\bእኔ እንግሊዝኛ ተናገርኩ[።\.]?$", "እንግሊዝኛ እናገራለሁ ።"),
    (r"(?i)\bአንድ ታክሲ ይደውሉ እባክህ[።\.]?$", "እባክህ ታክሲ ጥራልኝ ።"),
    (r"(?i)\bአንድ ታክሲ ይደውሉ[።\.]?$", "እባክህ ታክሲ ጥራልኝ ።"),
    (r"(?i)\bአይሆንም\s*[\.]?$", "አይደለም ።"),
]

# Post-processing fixes for NLLB literal mistranslation patterns
AMH_TO_ENG_POSTPROCESS = [
    # Literal "What is peace like?" from ሰላም እንዴት ና / ሰላም እንዴት ነህ
    (r"(?i)^(?:what is peace like|what's peace like)\??$", "Hello, how are you?"),
    (r"(?i)^(?:what is peace|what's peace)\??$", "Hello, how are you?"),
    (r"(?i)\bwhat is peace like\b", "how are you"),
    (r"(?i)\bwhat is peace\b", "how are you"),
    (r"(?i)^(?:is it peace|is peace)\??$", "Is everything good?"),
    (r"(?i)^(?:are you peace|are you peaceful)\??$", "Are you doing well?"),
    (r"(?i)^peace\s*-\s*what is it like\??$", "Hello, how are you?"),
    (r"(?i)^peace what is it like\??$", "Hello, how are you?"),
    (r"(?i)\bare you peace\b", "how are you"),
    (r"(?i)\bis it peace\b", "how are things"),
    (r"(?i)\bhave a good peace\b", "stay well"),
    (r"(?i)\bhow did you pass the night\b", "good morning"),
    (r"(?i)\bhow did you spend the day\b", "good afternoon"),

    # Literal "Peace be with/upon you" ecclesiastical formulas mapped to natural greetings
    (r"(?i)^\"?peace be (?:with|upon) you\"?\.?$", "Hello!"),
    (r"(?i)^\"?peace be (?:with|upon) you\"?,?\s*(?:my brother|bro)\.?$", "Hello, my brother!"),
    (r"(?i)^\"?peace be (?:with|upon) you\"?,?\s*(?:my sister)\.?$", "Hello, my sister!"),
    (r"(?i)^\"?peace to you\"?\.?$", "Hello!"),
    (r"(?i)^\"?peace to you\"?,?\s*(?:my brother|bro)\.?$", "Hello, my brother!"),
    (r"(?i)^peace be (?:with|upon) you,?\s*", "Hello, "),

    # Literal "You are / You're at peace" from ሰላም ነህ / ሰላም ነሽ / ሰላም ናችሁ
    (r"(?i)^you(?:'re| are) (?:at |the )?peace\.?$", "How are you?"),
    (r"(?i)^you(?:'re| are) (?:at |the )?peace,?\s*(?:my brother|bro)\.?$", "How are you, my brother?"),
    (r"(?i)^you(?:'re| are) (?:at |the )?peace,?\s*(?:my sister)\.?$", "How are you, my sister?"),
    (r"(?i)^how are you peace\.?$", "Hello, how are you?"),
    (r"(?i)^how does peace affect\.?$", "Hello, how are you?"),
    (r"(?i)^how peace is affected\.?$", "Hello, how are you?"),
    (r"(?i)^peace,?\s*how are you\??$", "Hello, how are you?"),
    (r"(?i)^peace is it\??$", "Hello, how are you?"),
    (r"(?i)^it is peace\.?$", "Hello, how are you?"),
    (r"(?i)^peace is my brother\.?$", "Hello, my brother."),
    (r"(?i)^peace,?\s*my (brother|sister|friend)\.?$", r"Hello, my \1."),
    (r"(?i)^peace\s*peace\.?$", "Hello!"),
    (r"(?i)^peace\.?$", "Hello."),

    # Natural brother/sister address greetings (keep as greetings, NOT goodbye)
    (r"(?i)^(how are you doing|how are you),?\s*(?:my brother|bro)\??$", "How are you, my brother?"),
    (r"(?i)^(how are you doing|how are you),?\s*(?:my sister)\??$", "How are you, my sister?"),
    (r"(?i)^(how are you doing|how are you)\??$", "How are you?"),
    (r"(?i)^(forgiveness|pardon)\??$", "Excuse me / I'm sorry"),
    (r"(?i)^no, my brother\??$", "Right, my brother?"),

    # Motion & Travel literalisms
    (r"(?i)^in peace,?\s*walk\.?$", "Have a safe trip / Walk in peace."),
    (r"(?i)^walk in peace\.?$", "Have a safe trip."),
    (r"(?i)\bwalk in peace\b", "have a safe trip"),

    # Spoken idioms & greetings
    (r"(?i)\bby your mother\??", "please"),
    (r"(?i)^it is peace!?\s*", "Hello! "),
    (r"(?i)\bpeace!\s*in what way\??", "Hello, how are you?"),
    (r"(?i)\b(?:hello!|hello,)?\s*in what way\??", "Hello, how are you?"),
    (r"(?i)^in what way\??$", "How are you?"),
    (r"(?i)\bhow is his country\??", "How is the country?"),
]

# Afaan Oromo common conversational exact mappings
ORM_TO_ENG_EXACT = {
    # Universal Greetings & Broadcast Anchor Formulas
    "harka fuune": "Greetings / Welcome.",
    "harka fuune!": "Greetings / Welcome!",
    "harka fuune akkam ooltan": "Greetings, good afternoon.",
    "harka fuune akkam ooltan?": "Greetings, good afternoon.",
    "harka fuune akkam ooltan kabajamtoota daawwattoota": "Greetings, good afternoon honored viewers.",
    "harka fuune akkam ooltan kabajamtoota daawwattoota.": "Greetings, good afternoon honored viewers.",
    "harka fuune akkam ooltan kabajamtoota daawwattoota keenya": "Greetings, good afternoon our honored viewers.",
    "harka fuune akkam ooltan kabajamtoota daawwattoota keenya.": "Greetings, good afternoon our honored viewers.",
    "harka fuune akkam bultan kabajamtoota daawwattoota": "Greetings, good morning honored viewers.",
    "harka fuune akkam jirtu kabajamtoota daawwattoota": "Greetings, how are you honored viewers.",
    "kabajamtoota daawwattoota": "Honored viewers",
    "kabajamtoota daawwattoota keenya": "Our honored viewers",
    "kabajamoo daawwattoota": "Honored viewers",
    "kabajamoo daawwattoota keenya": "Our honored viewers",
    "kabajamtoota dhaggeeffattoota": "Honored listeners",
    "kabajamtoota dhaggeeffattoota keenya": "Our honored listeners",
    "obn oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha": "Presenting this hour's OBN news is Mulatu.",
    "obn oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha.": "Presenting this hour's OBN news is Mulatu.",
    "oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha": "Presenting this hour's news is Mulatu.",
    "oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha.": "Presenting this hour's news is Mulatu.",
    "oduuwwan maddeen biyya keessaa fi alaa irraa arganne qabannee dhihaanneerra": "We have brought to you the news we gathered from domestic and foreign sources.",
    "oduuwwan maddeen biyya keessaa fi alaa irraa arganne qabannee dhihaanneerra.": "We have brought to you the news we gathered from domestic and foreign sources.",
    "hanga yeroo muraasaatti waliin turaa isiniin jenna, gara oduu ijootitti ceena": "We ask you to stay with us as we head to the main news.",
    "hanga yeroo muraasaatti waliin turaa isiniin jenna, gara oduu ijootitti ceena.": "We ask you to stay with us as we head to the main news.",
    "gara oduu ijootitti ceena": "We proceed to the main news.",
    "gara oduu ijootitti ceena.": "We proceed to the main news.",
    # Greetings & Courtesies
    "akkam": "Hello / How are you?",
    "akkam?": "Hello / How are you?",
    "akkam jirta": "Hello, how are you?",
    "akkam jirta?": "Hello, how are you?",
    "akkam jirtu": "Hello, how are you all?",
    "akkam jirtu?": "Hello, how are you all?",
    "akkam bulte": "Good morning.",
    "akkam bulte?": "Good morning, how did you sleep?",
    "akkam bultan": "Good morning everyone.",
    "akkam bultan?": "Good morning everyone.",
    "akkam bultani": "Good morning everyone.",
    "akkam bultani?": "Good morning everyone.",
    "akkam oolte": "Good afternoon.",
    "akkam oolte?": "Good afternoon, how was your day?",
    "akkam ooltan": "Good afternoon everyone.",
    "akkam ooltan?": "Good afternoon everyone.",
    "nagaan buli": "Good night.",
    "nagaan bulaa": "Good night everyone.",
    "nagaatti": "Goodbye.",
    "nagaa ta'i": "Goodbye.",
    "nagaa dhaa": "Is everything good?",
    "nagaa dhaa?": "Is everything good?",
    "fayyaa dhaa": "Are you doing well?",
    "fayyaa dhaa?": "Are you doing well?",
    "fayyaadhaa": "Are you doing well?",
    "fayyaadhaa?": "Are you doing well?",
    "fayyaa dha": "Are you doing well?",
    "fayyaa": "I am fine.",
    "ani fayyaa dha": "I am fine.",
    "ani nagaa dha": "I am fine.",
    "nagaa": "Peace / I am fine.",
    "galatoomaa": "Thank you.",
    "galatoomi": "Thank you.",
    "baay'ee galatoomaa": "Thank you very much.",
    "hedduu galatoomaa": "Thank you very much.",
    "maaloo": "Please.",
    "dhiifama": "Excuse me / I'm sorry.",
    "dhiifama naaf godhaa": "Please forgive me / I apologize.",
    "eyyee": "Yes.",
    "ee": "Yes.",
    "lakki": "No.",
    "miti": "It is not.",
    "akkam nagaa fayyumaa jirta": "Hello, how are you? Are you doing well?",
    "akkam nagaa fayyumaa jirta?": "Hello, how are you? Are you doing well?",
    "akkam nagaa fayyaa jirta": "Hello, how are you? Are you doing well?",
    "akkam nagaa fayyaa jirta?": "Hello, how are you? Are you doing well?",
    "nagaa fayyumaa jirta": "Are you doing well and healthy?",
    "nagaa fayyumaa jirta?": "Are you doing well and healthy?",
    "fayyumaa jirta": "Are you doing well?",
    "fayyumaa jirta?": "Are you doing well?",
    "fayyumaa": "I am well / Healthy",
    "baga nagaan dhufte": "Welcome.",
    "baga nagaan dhuftan": "Welcome everyone.",
    # Practical & Travel
    "maqaan kee eenyu": "What is your name?",
    "maqaan kee eenyu?": "What is your name?",
    "meeqa": "How much is it?",
    "meeqa?": "How much is it?",
    "gatiin isaa meeqa": "How much does it cost?",
    "gatiin isaa meeqa?": "How much does it cost?",
    "hospitaalichi eessa jira": "Where is the hospital?",
    "hospitaalichi eessa jira?": "Where is the hospital?",
    "hospitaala eessa jira": "Where is the hospital?",
    "hospitaala eessa jira?": "Where is the hospital?",
    "manni fincaanii eessa jira": "Where is the restroom?",
    "manni fincaanii eessa jira?": "Where is the restroom?",
    "bishaan barbaada": "I would like water.",
    "bishaan dhuguu barbaada": "I want to drink water.",
    "nyaata barbaada": "I would like food.",
    "na gargaari": "Please help me.",
    "na gargaaraa": "Please help me.",
    "gatii naaf hir'isi": "Can you give me a discount?",
    "gatii naaf hir'isi?": "Can you give me a discount?",
    "baay'ee qaalii dha": "It is too expensive.",
    "taaksii eessatti argadha": "Where can I find a taxi?",
    "taaksii eessatti argadha?": "Where can I find a taxi?",
}

# Tigrinya common conversational exact mappings
TIR_TO_ENG_EXACT = {
    # Universal Greetings & Broadcast Anchor Formulas
    "ጥዕና ይሃበለይ": "Hello",
    "ጥዕና ይሃበለይ!": "Hello!",
    "ጥዕና ይሃበለይ ከመይ ዲኹም": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ዲኹም?": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም?": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ዲኻ": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ዲኻ?": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ዲኺ": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ዲኺ?": "Hello, how are you?",
    "ጥዕና ይሃበለይ ከመይ ዲኹም ዝኸበርኩም ተመልከትትና": "Hello, how are you honored viewers.",
    "ጥዕና ይሃበለይ ከመይ ዲኹም ዝኸበርኩም ተዓዘብትና": "Hello, how are you honored viewers.",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም ዝኸበርኩም ተመልከትትና": "Hello, how are you honored viewers.",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም ዝኸበርኩም ተዓዘብትና": "Hello, how are you honored viewers.",
    "ጥዕና ይሃበለይ ከመይ ዲኹም ክቡራት ተመልከትትና": "Hello, how are you dear viewers.",
    "ጥዕና ይሃበለይ ከመይ ዲኹም ክቡራት ተዓዘብትና": "Hello, how are you dear viewers.",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም ክቡራት ተመልከትትና": "Hello, how are you dear viewers.",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም ክቡራት ተዓዘብትና": "Hello, how are you dear viewers.",
    "ጥዕና ይሃበለይ ከመይ ዲኹም ዝኸበርኩም ሰማዕትና": "Hello, how are you honored listeners.",
    "ዝኸበርኩም ተመልከትትና": "Honored viewers",
    "ዝኸበርኩም ተዓዘብትና": "Honored viewers",
    "ክቡራት ተመልከትትና": "Dear viewers",
    "ክቡራት ተዓዘብትና": "Dear viewers",
    "ዝኸበርኩም ሰማዕትና": "Honored listeners",
    "ክቡራት ሰማዕትና": "Dear listeners",
    "ክቡራትን ክቡራንን": "Ladies and gentlemen",
    # Greetings & Courtesies
    "ሰላም": "Hello",
    "ሰላም!": "Hello!",
    "ሰላም ሓወይ": "Hello, my brother.",
    "ሰላም ሓወይ!": "Hello, my brother!",
    "ሰላም ሓፍተይ": "Hello, my sister.",
    "ሰላም ሓፍተይ!": "Hello, my sister!",
    "ሰላም ከመይ ኣለኻ": "Hello, how are you?",
    "ሰላም ከመይ ኣለኻ?": "Hello, how are you?",
    "ሰላም ከመይ ኣለኻ ሓወይ": "Hello, how are you, my brother?",
    "ሰላም ከመይ ኣለኻ ሓወይ?": "Hello, how are you, my brother?",
    "ሰላም ከመይ ኣለኺ": "Hello, how are you?",
    "ሰላም ከመይ ኣለኺ?": "Hello, how are you?",
    "ሰላም ከመይ ኣለኺ ሓፍተይ": "Hello, how are you, my sister?",
    "ሰላም ከመይ ኣለኺ ሓፍተይ?": "Hello, how are you, my sister?",
    "ሰላም ከመይ ኣለኹም": "Hello, how are you all?",
    "ሰላም ከመይ ኣለኹም?": "Hello, how are you all?",
    "ከመይ ኣለኻ": "How are you?",
    "ከመይ ኣለኻ?": "How are you?",
    "ከመይ ኣለኻ ሓወይ": "How are you, my brother?",
    "ከመይ ኣለኻ ሓወይ?": "How are you, my brother?",
    "ከመይ ኣለኺ": "How are you?",
    "ከመይ ኣለኺ?": "How are you?",
    "ከመይ ኣለኺ ሓፍተይ": "How are you, my sister?",
    "ከመይ ኣለኺ ሓፍተይ?": "How are you, my sister?",
    "ከመይ ኣለኹም": "How are you all?",
    "ከመይ ኣለኹም?": "How are you all?",
    "ከመይ ሓዲርካ": "Good morning.",
    "ከመይ ሓዲርካ?": "Good morning, how did you spend the night?",
    "ከመይ ሓዲርኪ": "Good morning.",
    "ከመይ ሓዲርኪ?": "Good morning, how did you spend the night?",
    "ከመይ ሓዲርኩም": "Good morning everyone.",
    "ከመይ ሓዲርኩም?": "Good morning everyone.",
    "ከመይ ውዒልካ": "Good afternoon.",
    "ከመይ ውዒልካ?": "Good afternoon, how was your day?",
    "ከመይ ውዒልኪ": "Good afternoon.",
    "ከመይ ውዒልኪ?": "Good afternoon, how was your day?",
    "ከመይ ውዒልኩም": "Good afternoon everyone.",
    "ከመይ ውዒልኩም?": "Good afternoon everyone.",
    "ከመይ ኣምሲኻ": "Good evening.",
    "ከመይ ኣምሲኻ?": "Good evening.",
    "ከመይ ኣምሲኺ": "Good evening.",
    "ከመይ ኣምሲኺ?": "Good evening.",
    "ከመይ ኣምሲኹም": "Good evening everyone.",
    "ከመይ ኣምሲኹም?": "Good evening everyone.",
    "ደሓን ሕደር": "Good night.",
    "ደሓን ሕደሪ": "Good night.",
    "ደሓን ሕደሩ": "Good night everyone.",
    "ደሓን ኩን": "Goodbye.",
    "ደሓን ኩኒ": "Goodbye.",
    "ደሓን ኩኑ": "Goodbye everyone.",
    "ደሓንዶ": "Are you doing well?",
    "ደሓንዶ?": "Are you doing well?",
    "ደሓን ዲኻ": "Are you doing well?",
    "ደሓን ዲኻ?": "Are you doing well?",
    "ደሓን ዲኺ": "Are you doing well?",
    "ደሓን ዲኺ?": "Are you doing well?",
    "ደሓን ዲኹም": "Are you all doing well?",
    "ደሓን ዲኹም?": "Are you all doing well?",
    "ደሓን": "I am fine.",
    "ኣነ ደሓን እየ": "I am fine.",
    "እግዚኣብሔር ይመስገን": "Praise God, I am doing well.",
    "የቐንየለይ": "Thank you.",
    "ብጣዕሚ የቐንየለይ": "Thank you very much.",
    "ገንዘብካ": "You're welcome.",
    "ብሩህ መዓልቲ": "Have a good day.",
    "ይቕሬታ": "Excuse me / I'm sorry.",
    "ይቕሬታ ግበረለይ": "Please forgive me / I apologize.",
    "በጃኻ": "Please.",
    "በጃኺ": "Please.",
    "እወ": "Yes.",
    "ኣይፋልን": "No.",
    "ኣይኮነን": "No / It is not.",
    "እንቋዕ ብደሓን መጻእካ": "Welcome.",
    "እንቋዕ ብደሓን መጻእኩም": "Welcome everyone.",
    # Practical & Travel
    "ስምካ መን እዩ": "What is your name?",
    "ስምካ መን እዩ?": "What is your name?",
    "ስምኪ መን እዩ": "What is your name?",
    "ስምኪ መን እዩ?": "What is your name?",
    "ክንዲ ምንታይ እዩ": "How much is it?",
    "ክንዲ ምንታይ እዩ?": "How much is it?",
    "ዋጋኡ ክንዲ ምንታይ እዩ": "How much does it cost?",
    "ዋጋኡ ክንዲ ምንታይ እዩ?": "How much does it cost?",
    "ሆስፒታል ኣበይ ኣሎ": "Where is the hospital?",
    "ሆስፒታል ኣበይ ኣሎ?": "Where is the hospital?",
    "ሽቓቕ ኣበይ ኣሎ": "Where is the restroom?",
    "ሽቓቕ ኣበይ ኣሎ?": "Where is the restroom?",
    "ማይ እደሊ ኣለኹ": "I would like water.",
    "ምግቢ እደሊ ኣለኹ": "I would like food.",
    "ክትርድኣኒ ትኽእልዶ": "Can you help me?",
    "ክትርድኣኒ ትኽእልዶ?": "Can you help me?",
    "በጃኻ ሓግዘኒ": "Please help me.",
    "ዋጋ ኣጉድለለይ": "Can you give me a discount?",
    "ዋጋ ኣጉድለለይ?": "Can you give me a discount?",
    "ብጣዕሚ ክቡር እዩ": "It is too expensive.",
    "ታክሲ ኣበይ ክረክብ ይኽእል": "Where can I find a taxi?",
    "ታክሲ ኣበይ ክረክብ ይኽእል?": "Where can I find a taxi?",
}

# Somali common conversational exact mappings
SOM_TO_ENG_EXACT = {
    # Greetings & Courtesies
    "iska warran": "How are you?",
    "iska warran?": "How are you?",
    "iska warran walaal": "How are you, my brother?",
    "iska warran walaal?": "How are you, my brother?",
    "sidee tahay": "How are you?",
    "sidee tahay?": "How are you?",
    "sidee tahay walaal": "How are you, my brother?",
    "sidee tahay walaal?": "How are you, my brother?",
    "nabad walaal": "Hello, my brother.",
    "nabad walaal!": "Hello, my brother!",
    "sidee tihiin": "How are you all?",
    "sidee tihiin?": "How are you all?",
    "subax wanaagsan": "Good morning.",
    "galab wanaagsan": "Good afternoon.",
    "habeen wanaagsan": "Good night.",
    "nabad gelyo": "Goodbye.",
    "nabad miyaa": "Is everything peaceful?",
    "nabad miyaa?": "Is everything peaceful?",
    "waa nabad": "Everything is fine.",
    "waan fiicanahay": "I am fine.",
    "alxamdulilaah": "Praise be to God, I am fine.",
    "mahadsanid": "Thank you.",
    "aad baad u mahadsantahay": "Thank you very much.",
    "adaa mudan": "You're welcome.",
    "fadlan": "Please.",
    "raali noqo": "Excuse me / I'm sorry.",
    "iga raali noqo": "Excuse me / I'm sorry.",
    "haa": "Yes.",
    "maya": "No.",
    "soo dhawoow": "Welcome.",
    "soo dhowow": "Welcome.",
    # Practical & Travel
    "magacaa": "What is your name?",
    "magacaa?": "What is your name?",
    "magacaa maxaa la yiraahdaa": "What is your name?",
    "magacaa maxaa la yiraahdaa?": "What is your name?",
    "immisa weeye": "How much is it?",
    "immisa weeye?": "How much is it?",
    "waa immisa": "How much is it?",
    "waa immisa?": "How much is it?",
    "qiimuhu waa immisa": "How much does it cost?",
    "qiimuhu waa immisa?": "How much does it cost?",
    "xaggee bay ku taal cosbitaalku": "Where is the hospital?",
    "xaggee bay ku taal cosbitaalku?": "Where is the hospital?",
    "musqushu xaggee bay ku taal": "Where is the restroom?",
    "musqushu xaggee bay ku taal?": "Where is the restroom?",
    "biyo baan rabaa": "I would like water.",
    "cunto baan rabaa": "I would like food.",
    "ma i caawin kartaa": "Can you help me?",
    "ma i caawin kartaa?": "Can you help me?",
    "fadlan iga caawi": "Please help me.",
    "qiimaha iiga dhim": "Can you give me a discount?",
    "qiimaha iiga dhim?": "Can you give me a discount?",
    "aad bay qaali u tahay": "It is too expensive.",
    "xaggee ka heli karaa tagsi": "Where can I find a taxi?",
    "xaggee ka heli karaa tagsi?": "Where can I find a taxi?",
}

# English -> Afaan Oromo exact mappings
ENG_TO_ORM_EXACT = {
    "hello": "Akkam",
    "hello!": "Akkam!",
    "hello my brother": "Akkam obboleessa koo",
    "hello, my brother": "Akkam obboleessa koo",
    "hello, my brother!": "Akkam obboleessa koo!",
    "hello my sister": "Akkam obboleettii koo",
    "hello, my sister": "Akkam obboleettii koo",
    "hello, my sister!": "Akkam obboleettii koo!",
    "hi": "Akkam",
    "how are you": "Akkam jirta?",
    "how are you?": "Akkam jirta?",
    "how are you doing": "Akkam jirta?",
    "how are you doing?": "Akkam jirta?",
    "how are you my brother": "Akkam jirta obboleessa koo?",
    "how are you, my brother": "Akkam jirta obboleessa koo?",
    "how are you, my brother?": "Akkam jirta obboleessa koo?",
    "hello, how are you, my brother?": "Akkam jirta obboleessa koo?",
    "hello, how are you, my brother": "Akkam jirta obboleessa koo?",
    "how are you my sister": "Akkam jirta obboleettii koo?",
    "how are you, my sister": "Akkam jirta obboleettii koo?",
    "how are you, my sister?": "Akkam jirta obboleettii koo?",
    "hello, how are you, my sister?": "Akkam jirta obboleettii koo?",
    "hello, how are you, my sister": "Akkam jirta obboleettii koo?",
    "good morning": "Akkam bulte",
    "good morning!": "Akkam bulte!",
    "good afternoon": "Akkam oolte",
    "good afternoon!": "Akkam oolte!",
    "good night": "Nagaan buli",
    "good night!": "Nagaan buli!",
    "goodbye": "Nagaatti",
    "goodbye!": "Nagaatti!",
    "bye": "Nagaatti",
    "thank you": "Galatoomaa",
    "thank you!": "Galatoomaa!",
    "thank you very much": "Baay'ee galatoomaa",
    "you're welcome": "Rakkoo hin qabu",
    "please": "Maaloo",
    "excuse me": "Dhiifama",
    "sorry": "Dhiifama",
    "i am fine": "Fayyaa dha",
    "i'm fine": "Fayyaa dha",
    "i am fine, thank you": "Fayyaa dha, galatoomaa",
    "what is your name": "Maqaan kee eenyu?",
    "what is your name?": "Maqaan kee eenyu?",
    "how much is it": "Meeqa?",
    "how much is it?": "Meeqa?",
    "how much does it cost": "Gatiin isaa meeqa?",
    "how much does it cost?": "Gatiin isaa meeqa?",
    "where is the restroom": "Manni fincaanii eessa jira?",
    "where is the restroom?": "Manni fincaanii eessa jira?",
    "where is the bathroom": "Manni fincaanii eessa jira?",
    "where is the bathroom?": "Manni fincaanii eessa jira?",
    "where is the hospital": "Hospitaalichi eessa jira?",
    "where is the hospital?": "Hospitaalichi eessa jira?",
    "can you help me": "Na gargaaruu dandeessaa?",
    "can you help me?": "Na gargaaruu dandeessaa?",
    "please help me": "Maaloo na gargaaraa",
    "give me a discount": "Gatii naaf hir'isi",
    "can you give me a discount": "Gatii naaf hir'isi?",
    "where can i find a taxi": "Taaksii eessatti argadha?",
    "it is too expensive": "Baay'ee qaalii dha",
}

# English -> Tigrinya exact mappings
ENG_TO_TIR_EXACT = {
    "hello": "ሰላም",
    "hello!": "ሰላም!",
    "hi": "ሰላም",
    "how are you": "ከመይ ኣለኻ?",
    "how are you?": "ከመይ ኣለኻ?",
    "how are you doing": "ከመይ ኣለኻ?",
    "how are you doing?": "ከመይ ኣለኻ?",
    "good morning": "ከመይ ሓዲርካ",
    "good morning!": "ከመይ ሓዲርካ!",
    "good afternoon": "ከመይ ውዒልካ",
    "good afternoon!": "ከመይ ውዒልካ!",
    "good evening": "ከመይ ኣምሲኻ",
    "good evening!": "ከመይ ኣምሲኻ!",
    "good night": "ደሓን ሕደር",
    "good night!": "ደሓን ሕደር!",
    "goodbye": "ደሓን ኩን",
    "goodbye!": "ደሓን ኩን!",
    "bye": "ደሓን ኩን",
    "thank you": "የቐንየለይ",
    "thank you!": "የቐንየለይ!",
    "thank you very much": "ብጣዕሚ የቐንየለይ",
    "you're welcome": "ገንዘብካ",
    "please": "በጃኻ",
    "excuse me": "ይቕሬታ",
    "sorry": "ይቕሬታ",
    "i am fine": "ደሓን",
    "i'm fine": "ደሓን",
    "i am fine, thank you": "ደሓን እየ የቐንየለይ",
    "what is your name": "ስምካ መን እዩ?",
    "what is your name?": "ስምካ መን እዩ?",
    "how much is it": "ክንዲ ምንታይ እዩ?",
    "how much is it?": "ክንዲ ምንታይ እዩ?",
    "how much does it cost": "ዋጋኡ ክንዲ ምንታይ እዩ?",
    "how much does it cost?": "ዋጋኡ ክንዲ ምንታይ እዩ?",
    "where is the restroom": "ሽቓቕ ኣበይ ኣሎ?",
    "where is the restroom?": "ሽቓቕ ኣበይ ኣሎ?",
    "where is the bathroom": "ሽቓቕ ኣበይ ኣሎ?",
    "where is the bathroom?": "ሽቓቕ ኣበይ ኣሎ?",
    "where is the hospital": "ሆስፒታል ኣበይ ኣሎ?",
    "where is the hospital?": "ሆስፒታል ኣበይ ኣሎ?",
    "can you help me": "ክትርድኣኒ ትኽእልዶ?",
    "can you help me?": "ክትርድኣኒ ትኽእልዶ?",
    "please help me": "በጃኻ ሓግዘኒ",
    "give me a discount": "ዋጋ ኣጉድለለይ",
    "can you give me a discount": "ዋጋ ኣጉድለለይ?",
    "where can i find a taxi": "ታክሲ ኣበይ ክረክብ ይኽእል?",
    "it is too expensive": "ብጣዕሚ ክቡር እዩ",
}

# English -> Somali exact mappings
ENG_TO_SOM_EXACT = {
    "hello": "Iska warran",
    "hello!": "Iska warran!",
    "hi": "Iska warran",
    "how are you": "Sidee tahay?",
    "how are you?": "Sidee tahay?",
    "how are you doing": "Sidee tahay?",
    "how are you doing?": "Sidee tahay?",
    "good morning": "Subax wanaagsan",
    "good morning!": "Subax wanaagsan!",
    "good afternoon": "Galab wanaagsan",
    "good afternoon!": "Galab wanaagsan!",
    "good night": "Habeen wanaagsan",
    "good night!": "Habeen wanaagsan!",
    "goodbye": "Nabad gelyo",
    "goodbye!": "Nabad gelyo!",
    "bye": "Nabad gelyo",
    "thank you": "Mahadsanid",
    "thank you!": "Mahadsanid!",
    "thank you very much": "Aad baad u mahadsantahay",
    "you're welcome": "Adaa mudan",
    "please": "Fadlan",
    "excuse me": "Raali noqo",
    "sorry": "Raali noqo",
    "i am fine": "Waan fiicanahay",
    "i'm fine": "Waan fiicanahay",
    "i am fine, thank you": "Waan fiicanahay, mahadsanid",
    "what is your name": "Magacaa?",
    "what is your name?": "Magacaa?",
    "how much is it": "Immisa weeye?",
    "how much is it?": "Immisa weeye?",
    "how much does it cost": "Qiimuhu waa immisa?",
    "how much does it cost?": "Qiimuhu waa immisa?",
    "where is the restroom": "Musqushu xaggee bay ku taal?",
    "where is the restroom?": "Musqushu xaggee bay ku taal?",
    "where is the bathroom": "Musqushu xaggee bay ku taal?",
    "where is the bathroom?": "Musqushu xaggee bay ku taal?",
    "where is the hospital": "Xaggee bay ku taal cosbitaalku?",
    "where is the hospital?": "Xaggee bay ku taal cosbitaalku?",
    "can you help me": "Ma i caawin kartaa?",
    "can you help me?": "Ma i caawin kartaa?",
    "please help me": "Fadlan iga caawi",
    "give me a discount": "Qiimaha iiga dhim",
    "can you give me a discount": "Qiimaha iiga dhim?",
    "where can i find a taxi": "Xaggee ka heli karaa tagsi?",
    "it is too expensive": "Aad bay qaali u tahay",
}

# Afaan Oromo -> English post-processing fixes
ORM_TO_ENG_POSTPROCESS = [
    (r"(?i)^(is it peace|is peace)\??$", "Is everything good?"),
    (r"(?i)^(are you peace|are you peaceful)\??$", "How are you?"),
    (r"(?i)^in peace\??$", "Goodbye."),
    (r"(?i)\bhow did you pass the night\b", "good morning"),
    (r"(?i)\bhow did you spend the day\b", "good afternoon"),
    (r"(?i)^how is the existence\??$", "Hello, how are you?"),
    (r"(?i)^is health\??$", "Are you doing well?"),

    # Broadcast & Media disambiguation (daawwattoota = viewers, NOT tourists)
    (r"(?i)\bSuch\s+a\s+warm\s+welcome\s+from\s+the\s+tourists\s+of\s+this\s+time\s+is\s+especially\s+important\s+for\s+you\b",
     "Greetings, good afternoon honored viewers. This hour's news is presented to you"),
    (r"(?i)\bfrom\s+the\s+tourists\s+of\s+this\s+time\b", "to our viewers at this hour"),
    (r"(?i)\btourists\s+of\s+this\s+time\b", "viewers of this hour"),
    (r"(?i)\bwe'll\s+take\s+you\s+to\s+the\s+main\s+news\b", "we proceed to the main news"),
    (r"(?i)\btake\s+you\s+to\s+the\s+main\s+news\b", "head to the main news"),
]


# Tigrinya -> English post-processing fixes
TIR_TO_ENG_POSTPROCESS = [
    # Literal health translations for universal greeting (ጥዕና ይሃበለይ)
    (r"(?i)\b(?:in|with)\s+my\s+health\b", "Hello"),
    (r"(?i)\bwhere\s+(?:is\s+)?(?:your\s+)?health\b", "Hello"),
    (r"(?i)\bwhere\s+health\s+is\b", "Hello"),
    (r"(?i)\bgood\s+health,?\s+(?:see|watch|how)\s+(?:you\s+are\s+doing|how\s+you\s+are)\b", "Hello, how are you"),
    (r"(?i)^good\s+health,?\s*", "Hello, "),
    (r"(?i)^good\s+health\b", "Hello"),

    # Literal misinterpretation of ተመልከትትና / ተዓዘብትና ('our viewers') as 1st person verb
    (r"(?i)\bI'll\s+take\s+a\s+look(?:\s+at)?\b", "our viewers"),
    (r"(?i)\bwe'll\s+take\s+a\s+look(?:\s+at)?\b", "our viewers"),
    (r"(?i)\bwe\s+are\s+looking\s+at\b", "honored viewers"),
    (r"(?i)\bsee\s+how\s+you\s+are\s+doing\b", "how are you doing"),
    (r"(?i)\bwatch\s+how\s+you\s+are\s+doing\b", "how are you doing"),

    # Periphrastic broadcast verb formulas (ሒዝና ቀሪብና ኣለና)
    (r"(?i)\bwe\s+are\s+approaching\s+at\s+([0-9:]+\s*(?:a\.?m\.?|p\.?m\.?)?|\w+)\b", r"At \1, we present"),
    (r"(?i)\bwe\s+are\s+approaching\b", "we present"),
    (r"(?i)\bapproaching\s+at\b", "at"),
    (r"(?i)\bwe\s+have\s+held\s+and\s+presented\b", "we have brought to you"),
    (r"(?i)\bheld\s+and\s+presented\b", "presented"),

    # Time mistranslations (ፈረቓ = half past / 30 minutes)
    (r"(?i)\bjust\s+after\s+(\w+)\s+o'clock\b", r"at half past \1"),
    (r"(?i)\bjust\s+after\s+(\d+)\b", r"at \1:30"),

    # Standard greetings & courtesies
    (r"(?i)^(is it peace|is peace)\??$", "Is everything good?"),
    (r"(?i)^(are you peace|are you peaceful)\??$", "Are you doing well?"),
    (r"(?i)^be peaceful\??$", "Goodbye."),
    (r"(?i)\bhow did you spend the night\b", "good morning"),
    (r"(?i)\bhow did you spend the day\b", "good afternoon"),
]

# Somali -> English post-processing fixes
SOM_TO_ENG_POSTPROCESS = [
    (r"(?i)^report yourself\??$", "How are you?"),
    (r"(?i)^what is the report\??$", "How are you?"),
    (r"(?i)^enter peace\??$", "Goodbye."),
    (r"(?i)^(is it peace|is peace)\??$", "Is everything fine?"),
]

# Afaan Oromo -> Amharic exact colloquial mappings
ORM_TO_AMH_EXACT = {
    # Universal Greetings & Broadcast Anchor Formulas
    "harka fuune": "ሰላምታ አቅርበናል።",
    "harka fuune!": "ሰላምታ አቅርበናል።",
    "harka fuune akkam ooltan": "እንደምን ዋላችሁ።",
    "harka fuune akkam ooltan?": "እንደምን ዋላችሁ።",
    "harka fuune akkam ooltan kabajamtoota daawwattoota": "እንደምን ዋላችሁ ክቡራት ተመልካቾቻችን።",
    "harka fuune akkam ooltan kabajamtoota daawwattoota.": "እንደምን ዋላችሁ ክቡራት ተመልካቾቻችን።",
    "harka fuune akkam ooltan kabajamtoota daawwattoota keenya": "እንደምን ዋላችሁ ክቡራት ተመልካቾቻችን።",
    "harka fuune akkam ooltan kabajamtoota daawwattoota keenya.": "እንደምን ዋላችሁ ክቡራት ተመልካቾቻችን።",
    "harka fuune akkam bultan kabajamtoota daawwattoota": "እንደምን አደራችሁ ክቡራት ተመልካቾቻችን።",
    "harka fuune akkam jirtu kabajamtoota daawwattoota": "እንደምን ናችሁ ክቡራት ተመልካቾቻችን።",
    "kabajamtoota daawwattoota": "ክቡራት ተመልካቾች",
    "kabajamtoota daawwattoota keenya": "ክቡራት ተመልካቾቻችን",
    "kabajamoo daawwattoota": "ክቡራት ተመልካቾች",
    "kabajamoo daawwattoota keenya": "ክቡራት ተመልካቾቻችን",
    "kabajamtoota dhaggeeffattoota": "ክቡራት አድማጮች",
    "kabajamtoota dhaggeeffattoota keenya": "ክቡራት አድማጮቻችን",
    "obn oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha": "ይህ የኦቢኤን የሰዓቱ ዜና ሲሆን አቅራቢው ሙላቱ ነው።",
    "obn oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha.": "ይህ የኦቢኤን የሰዓቱ ዜና ሲሆን አቅራቢው ሙላቱ ነው።",
    "oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha": "ይህ የሰዓቱ ዜና ሲሆን አቅራቢው ሙላቱ ነው።",
    "oduu yeroo kanaa kan isiniif dhiyeessu mulaatuu dha.": "ይህ የሰዓቱ ዜና ሲሆን አቅራቢው ሙላቱ ነው።",
    "oduuwwan maddeen biyya keessaa fi alaa irraa arganne qabannee dhihaanneerra": "ከሀገር ውስጥና ከውጭ ምንጮች ያገኘናቸውን ዜናዎች ይዘን ቀርበናል።",
    "oduuwwan maddeen biyya keessaa fi alaa irraa arganne qabannee dhihaanneerra.": "ከሀገር ውስጥና ከውጭ ምንጮች ያገኘናቸውን ዜናዎች ይዘን ቀርበናል።",
    "hanga yeroo muraasaatti waliin turaa isiniin jenna, gara oduu ijootitti ceena": "አብራችሁን ቆዩ እያልን፣ ወደ ዋና ዋና ዜናዎች እናልፋለን።",
    "hanga yeroo muraasaatti waliin turaa isiniin jenna, gara oduu ijootitti ceena.": "አብራችሁን ቆዩ እያልን፣ ወደ ዋና ዋና ዜናዎች እናልፋለን።",
    "gara oduu ijootitti ceena": "ወደ ዋና ዋና ዜናዎች እናልፋለን።",
    "gara oduu ijootitti ceena.": "ወደ ዋና ዋና ዜናዎች እናልፋለን።",
    # Greetings & Courtesies
    "akkam": "ሰላም / እንዴት ነህ?",
    "akkam?": "ሰላም / እንዴት ነህ?",
    "akkam jirta": "እንዴት ነህ?",
    "akkam jirta?": "እንዴት ነህ?",
    "akkam jirtu": "እንዴት ናችሁ?",
    "akkam jirtu?": "እንዴት ናችሁ?",
    "akkam nagaa fayyumaa jirta": "እንዴት ነህ፣ ሰላም ነህ ደህና ነህ?",
    "akkam nagaa fayyumaa jirta?": "እንዴት ነህ፣ ሰላም ነህ ደህና ነህ?",
    "akkam nagaa fayyaa jirta": "እንዴት ነህ፣ ሰላም ነህ ደህና ነህ?",
    "akkam nagaa fayyaa jirta?": "እንዴት ነህ፣ ሰላም ነህ ደህና ነህ?",
    "nagaa fayyumaa jirta": "ሰላም ነህ ደህና ነህ?",
    "nagaa fayyumaa jirta?": "ሰላም ነህ ደህና ነህ?",
    "fayyumaa jirta": "ደህና ነህ?",
    "fayyumaa jirta?": "ደህና ነህ?",
    "fayyaa dhaa": "ደህና ነህ?",
    "fayyaa dhaa?": "ደህና ነህ?",
    "fayyaadhaa": "ደህና ነህ?",
    "fayyaadhaa?": "ደህና ነህ?",
    "fayyaa dha": "ደህና ነህ?",
    "fayyaa dha?": "ደህና ነህ?",
    "nagaa dhaa": "ሰላም ነው?",
    "nagaa dhaa?": "ሰላም ነው?",
    "nagaadhaa": "ሰላም ነው?",
    "nagaadhaa?": "ሰላም ነው?",
    "nagaa": "ሰላም",
    "fayyaa": "ደህና ነኝ",
    "fayyumaa": "ደህና ነኝ",
    "ani nagaadha": "እኔ ደህና ነኝ።",
    "ani nagaa dha": "እኔ ደህና ነኝ።",
    "ani fayyaadha": "እኔ ደህና ነኝ።",
    "ani fayyaa dha": "እኔ ደህና ነኝ።",
    "akkam bulte": "እንደምን አደርክ?",
    "akkam bulte?": "እንደምን አደርክ?",
    "akkam bultan": "እንደምን አደራችሁ?",
    "akkam bultan?": "እንደምን አደራችሁ?",
    "akkam bultani": "እንደምን አደራችሁ?",
    "akkam bultani?": "እንደምን አደራችሁ?",
    "akkam oolte": "እንደምን ዋልክ?",
    "akkam oolte?": "እንደምን ዋልክ?",
    "akkam ooltan": "እንደምን ዋላችሁ?",
    "akkam ooltan?": "እንደምን ዋላችሁ?",
    "nagaan buli": "ደህና እደር።",
    "nagaan bulaa": "ደህና እደሩ።",
    "nagaan ooli": "ደህና ዋል።",
    "nagaan oolaa": "ደህና ዋሉ።",
    "nagaatti": "ደህና ሁን።",
    "galatoomaa": "አመሰግናለሁ።",
    "galatoomi": "አመሰግናለሁ።",
    "baay'ee galatoomaa": "በጣም አመሰግናለሁ።",
    "baay'ee galatoomi": "በጣም አመሰግናለሁ።",
    "hedduu galatoomaa": "በጣም አመሰግናለሁ።",
    "maaloo": "እባክህ",
    "dhiifama": "ይቅርታ።",
    "dhiifama naaf godhaa": "ይቅርታ አድርጉልኝ።",
    "eyyee": "አዎ።",
    "ee": "አዎ።",
    "lakki": "አይደለም።",
    "miti": "አይደለም።",
    "rakkoo hin qabu": "ምንም ችግር የለም።",
    "baga nagaan dhufte": "እንኳን ደህና መጣህ።",
    "baga nagaan dhuftan": "እንኳን ደህና መጣችሁ።",
    "harka fuune": "ሰላምታ አቅርበናል።",
    "hospitaalli eessa jira": "ሆስፒታሉ የት ነው ያለው?",
    "hospitaalli eessa jira?": "ሆስፒታሉ የት ነው ያለው?",
    "hospitaalichi eessa jira": "ሆስፒታሉ የት ነው ያለው?",
    "hospitaalichi eessa jira?": "ሆስፒታሉ የት ነው ያለው?",
    "hospitaala eessa jira": "ሆስፒታሉ የት ነው ያለው?",
    "hospitaala eessa jira?": "ሆስፒታሉ የት ነው ያለው?",
    "manni fincaanii eessa jira": "መጸዳጃ ቤት የት ነው ያለው?",
    "manni fincaanii eessa jira?": "መጸዳጃ ቤት የት ነው ያለው?",
    "bishaan barbaada": "ውሃ እፈልጋለሁ።",
    "nyaata barbaada": "ምግብ እፈልጋለሁ።",
    "meeqa": "ስንት ነው?",
    "meeqa?": "ስንት ነው?",
    "gatiin isaa meeqa": "ዋጋው ስንት ነው?",
    "gatiin isaa meeqa?": "ዋጋው ስንት ነው?",
    "gatii naaf hir'isi": "ቅናሽ አድርግልኝ።",
    "gatii naaf hir'isi?": "ቅናሽ ታደርግልኛለህ?",
    "baay'ee qaalii dha": "በጣም ውድ ነው።",
    "na gargaaraa": "እባካችሁ እርዱኝ።",
    "na gargaari": "እባክህ እርዳኝ።",
    "taaksii eessatti argadha": "ታክሲ የት ይገኛል?",
    "taaksii eessatti argadha?": "ታክሲ የት ይገኛል?",
    "doktora barbaada": "ዶክተር እፈልጋለሁ።",
}

# Amharic -> Afaan Oromo exact colloquial mappings
AMH_TO_ORM_EXACT = {
    "ሰላም": "Akkam",
    "ሰላም ነው": "Nagaa dhaa?",
    "ሰላም ነው?": "Nagaa dhaa?",
    "እንዴት ነህ": "Akkam jirta?",
    "እንዴት ነህ?": "Akkam jirta?",
    "እንዴት ነሽ": "Akkam jirta?",
    "እንዴት ነሽ?": "Akkam jirta?",
    "እንዴት ናችሁ": "Akkam jirtu?",
    "እንዴት ናችሁ?": "Akkam jirtu?",
    "እንደምን አደርክ": "Akkam bulte?",
    "እንደምን አደርክ?": "Akkam bulte?",
    "እንደምን ዋልክ": "Akkam oolte?",
    "እንደምን ዋልክ?": "Akkam oolte?",
    "ደህና ነህ": "Fayyaa dhaa?",
    "ደህና ነህ?": "Fayyaa dhaa?",
    "ደህና ነኝ": "Ani nagaa dha.",
    "ደህና ነኝ አመሰግናለሁ": "Ani nagaa dha, galatoomi.",
    "አመሰግናለሁ": "Galatoomi.",
    "በጣም አመሰግናለሁ": "Baay'ee galatoomi.",
    "እባክህ": "Maaloo",
    "እባክዎ": "Maaloo",
    "ይቅርታ": "Dhiifama.",
    "አዎ": "Eeyyee.",
    "አይደለም": "Miti.",
    "ደህና እደር": "Nagaan buli.",
    "ደህና ዋል": "Nagaan ooli.",
    "ደህና ሁን": "Nagaatti.",
    "ሆስፒታሉ የት ነው": "Hospitaalichi eessa jira?",
    "ሆስፒታሉ የት ነው?": "Hospitaalichi eessa jira?",
    "ዋጋው ስንት ነው": "Gatiin isaa meeqa?",
    "ዋጋው ስንት ነው?": "Gatiin isaa meeqa?",
    "ቅናሽ አድርግልኝ": "Gatii naaf hir'isi.",
    "ቅናሽ አድርግልኝ?": "Gatii naaf hir'isi?",
    "በጣም ውድ ነው": "Baay'ee qaalii dha.",
    "ውሃ እፈልጋለሁ": "Bishaan barbaada.",
    "እባክህ እርዳኝ": "Maaloo na gargaari.",
    "ታክሲ የት ይገኛል": "Taaksii eessatti argadha?",
    "ታክሲ የት ይገኛል?": "Taaksii eessatti argadha?",
}

# Tigrinya -> Amharic exact colloquial mappings
TIR_TO_AMH_EXACT = {
    # Universal Greetings & Broadcast Anchor Formulas
    "ጥዕና ይሃበለይ": "ጤና ይስጥልኝ።",
    "ጥዕና ይሃበለይ!": "ጤና ይስጥልኝ!",
    "ጥዕና ይሃበለይ ከመይ ዲኹም": "ጤና ይስጥልኝ እንደምን ናችሁ?",
    "ጥዕና ይሃበለይ ከመይ ዲኹም?": "ጤና ይስጥልኝ እንደምን ናችሁ?",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም": "ጤና ይስጥልኝ እንደምን ናችሁ?",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም?": "ጤና ይስጥልኝ እንደምን ናችሁ?",
    "ጥዕና ይሃበለይ ከመይ ዲኹም ዝኸበርኩም ተመልከትትና": "ጤና ይስጥልኝ፣ ክቡራት ተመልካቾቻችን እንደምን ናችሁ።",
    "ጥዕና ይሃበለይ ከመይ ዲኹም ዝኸበርኩም ተዓዘብትና": "ጤና ይስጥልኝ፣ ክቡራት ተመልካቾቻችን እንደምን ናችሁ።",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም ዝኸበርኩም ተመልከትትና": "ጤና ይስጥልኝ፣ ክቡራት ተመልካቾቻችን እንደምን ናችሁ።",
    "ጥዕና ይሃበለይ ከመይ ኣለኹም ዝኸበርኩም ተዓዘብትና": "ጤና ይስጥልኝ፣ ክቡራት ተመልካቾቻችን እንደምን ናችሁ።",
    "ዝኸበርኩም ተመልከትትና": "ክቡራት ተመልካቾቻችን",
    "ዝኸበርኩም ተዓዘብትና": "ክቡራት ተመልካቾቻችን",
    "ዝኸበርኩም ሰማዕትና": "ክቡራት አድማጮቻችን",
    "ከመይ ኣለኻ": "እንዴት ነህ?",
    "ከመይ ኣለኻ?": "እንዴት ነህ?",
    "ከመይ ኣለኺ": "እንዴት ነሽ?",
    "ከመይ ኣለኺ?": "እንዴት ነሽ?",
    "ከመይ ኣለኹም": "እንዴት ናችሁ?",
    "ከመይ ኣለኹም?": "እንዴት ናችሁ?",
    "ደሓንዶ": "ደህና ነህ?",
    "ደሓንዶ?": "ደህና ነህ?",
    "ደሓን ዲኻ": "ደህና ነህ?",
    "ደሓን ዲኻ?": "ደህና ነህ?",
    "ደሓን ዲኺ": "ደህና ነሽ?",
    "ደሓን ዲኺ?": "ደህና ነሽ?",
    "ደሓን ዲኹም": "ደህና ናችሁ?",
    "ደሓን ዲኹም?": "ደህና ናችሁ?",
    "ደሓን እየ": "ደህና ነኝ።",
    "ሰላምዶ": "ሰላም ነው?",
    "ሰላምዶ?": "ሰላም ነው?",
    "ሰላም ዲኻ": "ሰላም ነህ?",
    "ሰላም ዲኻ?": "ሰላም ነህ?",
    "ከመይ ሓዲርካ": "እንደምን አደርክ?",
    "ከመይ ሓዲርካ?": "እንደምን አደርክ?",
    "ከመይ ሓዲርኪ": "እንደምን አደርሽ?",
    "ከመይ ሓዲርኪ?": "እንደምን አደርሽ?",
    "ከመይ ሓዲርኩም": "እንደምን አደራችሁ?",
    "ከመይ ሓዲርኩም?": "እንደምን አደራችሁ?",
    "ከመይ ውዒልካ": "እንደምን ዋልክ?",
    "ከመይ ውዒልካ?": "እንደምን ዋልክ?",
    "ከመይ ውዒልኪ": "እንደምን ዋልሽ?",
    "ከመይ ውዒልኪ?": "እንደምን ዋልሽ?",
    "ከመይ ውዒልኩም": "እንደምን ዋላችሁ?",
    "ከመይ ውዒልኩም?": "እንደምን ዋላችሁ?",
    "ደሓን ሕደር": "ደህና እደር።",
    "ደሓን ሕደሪ": "ደህና እደሪ።",
    "ደሓን ሕደሩ": "ደህና እደሩ።",
    "ደሓን ዋዕል": "ደህና ዋል።",
    "ደሓን ዋዕሊ": "ደህና ዋዪ።",
    "ደሓን ዋዕሉ": "ደህና ዋሉ።",
    "ደሓን ኩን": "ደህና ሁን።",
    "ደሓን ኩኒ": "ደህና ሁኚ።",
    "ደሓን ኩኑ": "ደህና ሁኑ።",
    "የቐንየለይ": "አመሰግናለሁ።",
    "የቐንየልና": "እናመሰግናለን።",
    "ብዙሕ የቐንየለይ": "በጣም አመሰግናለሁ።",
    "ይቕሬታ": "ይቅርታ።",
    "በጃኻ": "እባክህ።",
    "በጃኺ": "እባክሽ።",
    "በጃኹም": "እባክዎ።",
    "እወ": "አዎ።",
    "ኣይፋልን": "አይደለም።",
    "ጸገም የለን": "ምንም ችግር የለም።",
    "እንቋዕ ብደሓን መጻእካ": "እንኳን ደህና መጣህ።",
    "እንቋዕ ብደሓን መጻእኪ": "እንኳን ደህና መጣሽ።",
    "እንቋዕ ብደሓን መጻእኩም": "እንኳን ደህና መጣችሁ።",
    "ኣጆኻ": "አይዞህ / በርታ።",
    "ኣጆኺ": "አይዞሽ / በርቺ።",
    "ኣጆኹም": "አይዟችሁ / በርቱ።",
    "ሆስፒታል ኣበይ ኣሎ": "ሆስፒታሉ የት ነው ያለው?",
    "ሆስፒታል ኣበይ ኣሎ?": "ሆስፒታሉ የት ነው ያለው?",
    "ክንዲ ምንታይ እዩ": "ስንት ነው?",
    "ክንዲ ምንታይ እዩ?": "ስንት ነው?",
    "ዋጋኡ ክንዲ ምንታይ እዩ": "ዋጋው ስንት ነው?",
    "ዋጋኡ ክንዲ ምንታይ እዩ?": "ዋጋው ስንት ነው?",
    "ኣጉድለለይ": "ቅናሽ አድርግልኝ።",
    "ኣጉድለለይ?": "ቅናሽ ታደርግልኛለህ?",
    "ብዙሕ ክቡር እዩ": "በጣም ውድ ነው።",
    "ሓግዙኒ": "እባካችሁ እርዱኝ።",
    "ሓኪም እደሊ ኣለኹ": "ዶክተር እፈልጋለሁ።",
    "ታክሲ ኣበይ ይርከብ": "ታክሲ የት ይገኛል?",
    "ታክሲ ኣበይ ይርከብ?": "ታክሲ የት ይገኛል?",
}

# Amharic -> Tigrinya exact colloquial mappings
AMH_TO_TIR_EXACT = {
    "ሰላም": "ሰላም",
    "ሰላም ነው": "ሰላምዶ?",
    "ሰላም ነው?": "ሰላምዶ?",
    "እንዴት ነህ": "ከመይ ኣለኻ?",
    "እንዴት ነህ?": "ከመይ ኣለኻ?",
    "እንዴት ነሽ": "ከመይ ኣለኺ?",
    "እንዴት ነሽ?": "ከመይ ኣለኺ?",
    "እንዴት ናችሁ": "ከመይ ኣለኹም?",
    "እንዴት ናችሁ?": "ከመይ ኣለኹም?",
    "እንደምን አደርክ": "ከመይ ሓዲርካ?",
    "እንደምን አደርክ?": "ከመይ ሓዲርካ?",
    "ደህና ነህ": "ደሓን ዲኻ?",
    "ደህና ነህ?": "ደሓን ዲኻ?",
    "ደህና ነኝ": "ደሓን እየ።",
    "አመሰግናለሁ": "የቐንየለይ።",
    "በጣም አመሰግናለሁ": "ብዙሕ የቐንየለይ።",
    "እባክህ": "በጃኻ",
    "ይቅርታ": "ይቕሬታ።",
    "አዎ": "እወ።",
    "አይደለም": "ኣይፋልን።",
    "ሆስፒታሉ የት ነው": "ሆስፒታል ኣበይ ኣሎ?",
    "ሆስፒታሉ የት ነው?": "ሆስፒታል ኣበይ ኣሎ?",
    "ዋጋው ስንት ነው": "ዋጋኡ ክንዲ ምንታይ እዩ?",
    "ዋጋው ስንት ነው?": "ዋጋኡ ክንዲ ምንታይ እዩ?",
}

# Somali -> Amharic exact colloquial mappings
SOM_TO_AMH_EXACT = {
    "iska warran": "እንዴት ነህ?",
    "iska warran?": "እንዴት ነህ?",
    "sidee tahay": "እንዴት ነህ?",
    "sidee tahay?": "እንዴት ነህ?",
    "fiican": "ደህና ነኝ።",
    "waan fiicanahay": "እኔ ደህና ነኝ።",
    "subax wanaagsan": "እንደምን አደርክ።",
    "galab wanaagsan": "እንደምን ዋልክ።",
    "habeen wanaagsan": "ደህና እደር።",
    "nabad gelyo": "ደህና ሁን።",
    "mahadsanid": "አመሰግናለሁ።",
    "aad baad u mahadsantahay": "በጣም አመሰግናለሁ።",
    "fadlan": "እባክህ / እባክዎ።",
    "waayahay": "እሺ።",
    "haah": "አዎ።",
    "maya": "አይደለም።",
    "dhib ma leh": "ምንም ችግር የለም።",
    "soo dhawoow": "እንኳን ደህና መጣህ።",
    "cosbitaalku xaggee bay ku taal": "ሆስፒታሉ የት ነው ያለው?",
    "cosbitaalku xaggee bay ku taal?": "ሆስፒታሉ የት ነው ያለው?",
    "immisa weeye": "ስንት ነው?",
    "immisa weeye?": "ስንት ነው?",
    "qiimaha iiga dhim": "ቅናሽ አድርግልኝ።",
    "aad bay qaali u tahay": "በጣም ውድ ነው።",
    "fadlan iga caawi": "እባክህ እርዳኝ።",
    "dhakhtar baan rabaa": "ዶክተር እፈልጋለሁ።",
    "xaggee ka heli karaa tagsi": "ታክሲ የት ይገኛል?",
    "xaggee ka heli karaa tagsi?": "ታክሲ የት ይገኛል?",
}

# Amharic -> Somali exact colloquial mappings
AMH_TO_SOM_EXACT = {
    "ሰላም": "Nabad",
    "ሰላም ነው": "Ma nabad baa?",
    "ሰላም ነው?": "Ma nabad baa?",
    "እንዴት ነህ": "Sidee tahay?",
    "እንዴት ነህ?": "Sidee tahay?",
    "እንዴት ነሽ": "Sidee tahay?",
    "እንዴት ነሽ?": "Sidee tahay?",
    "እንደምን አደርክ": "Subax wanaagsan.",
    "ደህና ነህ": "Ma nabad baa?",
    "ደህና ነኝ": "Waan fiicanahay.",
    "አመሰግናለሁ": "Mahadsanid.",
    "እባክህ": "Fadlan",
    "ይቅርታ": "I caafi.",
    "አዎ": "Haah.",
    "አይደለም": "Maya.",
    "ደህና ሁን": "Nabad gelyo.",
    "ሆስፒታሉ የት ነው": "Cosbitaalku xaggee bay ku taal?",
    "ዋጋው ስንት ነው": "Immisa weeye?",
}

# Literal error post-processing when translating into Amharic
ORM_TO_AMH_POSTPROCESS = [
    (r"(?i)\bሰላማዊ መሆን የምትችለው እንዴት ነው\??", "እንዴት ነህ፣ ደህና ነህ?"),
    (r"(?i)\bሰላማዊ መሆን የምትችለው\??", "ደህና ነህ?"),
    (r"(?i)\bሰላማዊ ነህ\??", "ደህና ነህ?"),
    (r"(?i)^አንተም ሰላም ታገኛለህ[።\.]?$", "እንዴት ነህ፣ ደህና ነህ?"),
    (r"(?i)\bሰላም ያስገኛል\??", "ሰላም ነው?"),
    (r"(?i)^ትድናለህ[።\.]?$", "ደህና ነህ?"),
    (r"(?i)^አገዛዙ[።\.]?$", "እንደምን አደርክ?"),
    (r"(?i)\bእንዴት ታድያለች\??", "እንደምን ዋልክ?"),
    (r"(?i)\bሰላማዊ ነኝ[።\.]?$", "እኔ ደህና ነኝ።"),
    (r"(?i)\bጤንነት\??$", "ደህና ነህ?"),
]

TIR_TO_AMH_POSTPROCESS = [
    (r"(?i)\bቅናት ያሳየኛል[።\.]?$", "አመሰግናለሁ።"),
    (r"(?i)\bእንዴት ታድራለህ\??", "እንደምን አደርክ?"),
    (r"(?i)\bእንዴት ትውላለህ\??", "እንደምን ዋልክ?"),
]

SOM_TO_AMH_POSTPROCESS = [
    (r"(?i)\bእስቲ አስበው\??$", "እንዴት ነህ?"),
    (r"(?i)\bመልካም ጠዋት[።\.]?$", "እንደምን አደርክ።"),
    (r"(?i)\bእናመሰግናለን[።\.]?$", "አመሰግናለሁ።"),
]


def preprocess_for_translation(text: str, src_lang: str, tgt_lang: str) -> str:
    """Clean and normalize source text before feeding to translation."""
    if not text:
        return ""

    # Strip ASR language tag prefixes like [AMH], [ORM], [TIR]
    cleaned = re.sub(r"^\[[A-Za-z]+\]\s*", "", text).strip()

    # If translating English -> Amharic, standardize common landmark casing
    if src_lang in ("eng", "eng_Latn") and tgt_lang in ("amh", "amh_Ethi"):
        for pattern, amh_repl in ENG_TO_AMH_GLOSSARY.items():
            cleaned = re.sub(pattern, amh_repl, cleaned, flags=re.IGNORECASE)

    # If translating Amharic -> English, normalize spoken colloquial particles
    if src_lang in ("amh", "amh_Ethi") and tgt_lang in ("eng", "eng_Latn"):
        cleaned = re.sub(r"\bበናትህ\b", "እባክህ", cleaned)
        cleaned = re.sub(r"\bበናትሽ\b", "እባክሽ", cleaned)
        cleaned = re.sub(r"\bበናታችሁ\b", "እባካችሁ", cleaned)
        cleaned = re.sub(r"\bሀገሩ እንዴት ነው\b", "ይህ አገር እንዴት ነው", cleaned)

    return cleaned


def _lookup_table(table: dict[str, str], normalized: str, norm_lower: str, norm_clean: str, normalize_geez: bool = False) -> str | None:
    """Helper to check normalized, lower, clean, and optional homophone-normalized keys."""
    if normalized in table:
        return table[normalized]
    if norm_lower in table:
        return table[norm_lower]
    if norm_clean in table:
        return table[norm_clean]
    if normalize_geez:
        try:
            from ai_pipeline.speech_repair import SpeechRepair
            norm_homo = SpeechRepair.normalize_ethiopic_homophones(norm_clean)
            if norm_homo in table:
                return table[norm_homo]
        except Exception:
            pass
    return None


def check_exact_match(text: str, src_lang: str, tgt_lang: str) -> str | None:
    """Check if the text has a direct high-fidelity cultural translation."""
    normalized = text.strip()
    norm_lower = normalized.lower().rstrip(".!?፣።")
    norm_clean = re.sub(r"[\s!?,.:;፣።፧]+", " ", normalized).strip().lower()

    # Amharic <-> English
    if src_lang in ("amh", "amh_Ethi") and tgt_lang in ("eng", "eng_Latn"):
        res = _lookup_table(AMH_TO_ENG_EXACT, normalized, norm_lower, norm_clean, normalize_geez=True)
        if res:
            return res

    if src_lang in ("eng", "eng_Latn") and tgt_lang in ("amh", "amh_Ethi"):
        res = _lookup_table(ENG_TO_AMH_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    # Afaan Oromo <-> English
    if src_lang in ("orm", "gaz_Latn") and tgt_lang in ("eng", "eng_Latn"):
        res = _lookup_table(ORM_TO_ENG_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    if src_lang in ("eng", "eng_Latn") and tgt_lang in ("orm", "gaz_Latn"):
        res = _lookup_table(ENG_TO_ORM_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    # Tigrinya <-> English
    if src_lang in ("tir", "tir_Ethi") and tgt_lang in ("eng", "eng_Latn"):
        res = _lookup_table(TIR_TO_ENG_EXACT, normalized, norm_lower, norm_clean, normalize_geez=True)
        if res:
            return res

    if src_lang in ("eng", "eng_Latn") and tgt_lang in ("tir", "tir_Ethi"):
        res = _lookup_table(ENG_TO_TIR_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    # Somali <-> English
    if src_lang in ("som", "som_Latn") and tgt_lang in ("eng", "eng_Latn"):
        res = _lookup_table(SOM_TO_ENG_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    if src_lang in ("eng", "eng_Latn") and tgt_lang in ("som", "som_Latn"):
        res = _lookup_table(ENG_TO_SOM_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    # Afaan Oromo <-> Amharic (Domestic #1 Pair)
    if src_lang in ("orm", "gaz_Latn") and tgt_lang in ("amh", "amh_Ethi"):
        res = _lookup_table(ORM_TO_AMH_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    if src_lang in ("amh", "amh_Ethi") and tgt_lang in ("orm", "gaz_Latn"):
        res = _lookup_table(AMH_TO_ORM_EXACT, normalized, norm_lower, norm_clean, normalize_geez=True)
        if res:
            return res

    # Tigrinya <-> Amharic
    if src_lang in ("tir", "tir_Ethi") and tgt_lang in ("amh", "amh_Ethi"):
        res = _lookup_table(TIR_TO_AMH_EXACT, normalized, norm_lower, norm_clean, normalize_geez=True)
        if res:
            return res

    if src_lang in ("amh", "amh_Ethi") and tgt_lang in ("tir", "tir_Ethi"):
        res = _lookup_table(AMH_TO_TIR_EXACT, normalized, norm_lower, norm_clean, normalize_geez=True)
        if res:
            return res

    # Somali <-> Amharic
    if src_lang in ("som", "som_Latn") and tgt_lang in ("amh", "amh_Ethi"):
        res = _lookup_table(SOM_TO_AMH_EXACT, normalized, norm_lower, norm_clean)
        if res:
            return res

    if src_lang in ("amh", "amh_Ethi") and tgt_lang in ("som", "som_Latn"):
        res = _lookup_table(AMH_TO_SOM_EXACT, normalized, norm_lower, norm_clean, normalize_geez=True)
        if res:
            return res

    return None


def postprocess_translation(translated_text: str, src_lang: str, tgt_lang: str) -> str:
    """Post-process translation output to fix cultural/colloquial inaccuracies."""
    if not translated_text:
        return ""

    result = translated_text.strip()

    # If translating into Amharic: fix corrupted city names, entities, and NLLB literal errors
    if tgt_lang in ("amh", "amh_Ethi"):
        misspellings = {
            "ላ ሊቤዳ": "ላሊበላ",
            "ላሊቤዳ": "ላሊበላ",
            "ላሊቤላ": "ላሊበላ",
            "አክሴል": "አክሱም",
            "አክሰል": "አክሱም",
            "ባሃርዳ": "ባህር ዳር",
            "ባህርዳር": "ባህር ዳር",
            "ባሃር ዳ": "ባህር ዳር",
            "ባሃር ዳር": "ባህር ዳር",
            "አዲስአበባ": "አዲስ አበባ",
        }
        for wrong, correct in misspellings.items():
            result = result.replace(wrong, correct)

        if src_lang in ("orm", "gaz_Latn"):
            for pattern, replacement in ORM_TO_AMH_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        elif src_lang in ("tir", "tir_Ethi"):
            for pattern, replacement in TIR_TO_AMH_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        elif src_lang in ("som", "som_Latn"):
            for pattern, replacement in SOM_TO_AMH_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        elif src_lang in ("eng", "eng_Latn"):
            for pattern, replacement in ENG_TO_AMH_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # If translating into English: fix literal patterns
    if tgt_lang in ("eng", "eng_Latn"):
        if src_lang in ("amh", "amh_Ethi"):
            for pattern, replacement in AMH_TO_ENG_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        elif src_lang in ("orm", "gaz_Latn"):
            for pattern, replacement in ORM_TO_ENG_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        elif src_lang in ("tir", "tir_Ethi"):
            for pattern, replacement in TIR_TO_ENG_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        elif src_lang in ("som", "som_Latn"):
            for pattern, replacement in SOM_TO_ENG_POSTPROCESS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result.strip()
