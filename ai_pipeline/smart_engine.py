"""Offline Smart Engine for Ethiopian Translator ("Lisan Intelligence").

Provides context-aware multi-turn reasoning, intent classification,
cultural idiom de-literalization, formality register control, and
intelligent follow-up suggestion chips — 100% on-device and memory-safe.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    GREETING = "greeting_courtesy"
    BARGAINING = "commerce_bargaining"
    DIRECTIONS = "navigation_directions"
    DINING = "dining_hospitality"
    MEDICAL = "emergency_medical"
    CIVIC_GOV = "civic_administration"
    BANKING = "banking_finance"
    EDUCATION = "education_school"
    LEGAL_POLICE = "legal_police"
    GENERAL = "general_conversation"


# ──────────────────────────────────────────────────────────────────
# 1. Cultural Idioms & Figurative Expressions De-literalizer
# ──────────────────────────────────────────────────────────────────
AMHARIC_IDIOMS: list[tuple[str, str]] = [
    # Encouragement, sympathy & comfort
    (r"\bአይዞህ\b", "Take heart / Stay strong"),
    (r"\bአይዞሽ\b", "Take heart / Stay strong"),
    (r"\bአይዟችሁ\b", "Take heart / Stay strong everyone"),
    (r"\bአትጨነቅ\b", "Don't worry"),
    (r"\bአትጨነቂ\b", "Don't worry"),
    (r"\bአትጨነቁ\b", "Don't worry everyone"),
    # Congratulations & blessings
    (r"\bእንኳን ደስ አለህ\b", "Congratulations!"),
    (r"\bእንኳን ደስ አለሽ\b", "Congratulations!"),
    (r"\bእንኳን ደስ አላችሁ\b", "Congratulations everyone!"),
    (r"\bእንኳን አደረሰህ\b", "Happy holiday / Season's greetings!"),
    (r"\bእንኳን አደረሰሽ\b", "Happy holiday / Season's greetings!"),
    (r"\bእንኳን አደረሳችሁ\b", "Happy holiday / Season's greetings to all!"),
    (r"\bእግዜር ይስጥልኝ\b", "Thank you very much / May God reward you"),
    (r"\bእግዚአብሔር ይስጥልኝ\b", "Thank you very much / May God reward you"),
    (r"\bመልካም ቀን\b", "Have a wonderful day"),
    (r"\bመልካም እድል\b", "Good luck"),
    (r"\bእሰይ\b", "Wonderful / Hooray"),
    # Colloquial idioms
    (r"\bሆዴ ባባ\b", "I was deeply moved with emotion"),
    (r"\bበቁም ነገር\b", "In all seriousness"),
    (r"\bእግር አውጣ ብዬ\b", "I ran as fast as I could"),
    (r"\bስራ ፈታሁ\b", "I am out of work / I am free"),
    (r"\bእንደምንም ብዬ\b", "Somehow / by any means necessary"),
    (r"\bምን አገባኝ\b", "None of my business"),
    (r"\bበቃ\b", "That is all / Enough"),
    (r"\bምንም አይደል\b", "Don't mention it / No problem"),
    (r"\bቸር ያሰማን\b", "May we hear good news"),
    # Medical & Clinic Empathy
    (r"\bእግዜር ይማርህ\b", "May God grant you health and recovery", "ፈጣሪ ይምሓርካ"),
    (r"\bእግዜር ይማርሽ\b", "May God grant you health and recovery", "ፈጣሪ ይምሓርኪ"),
    (r"\bእግዜር ይማራችሁ\b", "May God grant you health and recovery everyone", "ፈጣሪ ይምሓርኩም"),
    (r"\bእግዚአብሔር ይማርህ\b", "May God grant you health and recovery", "ፈጣሪ ይምሓርካ"),
    (r"\bእግዚአብሔር ይማርሽ\b", "May God grant you health and recovery", "ፈጣሪ ይምሓርኪ"),
    (r"\bእግዚአብሔር ይማራችሁ\b", "May God grant you health and recovery everyone", "ፈጣሪ ይምሓርኩም"),
    # Road & Transit Safety
    (r"\bመንገዱን ያቅናልህ\b", "Have a safe and smooth journey", "መንገዲ የቀንዓልካ።"),
    (r"\bመንገዱን ያቅናልሽ\b", "Have a safe and smooth journey", "መንገዲ የቀንዓልኪ።"),
    (r"\bመንገዱን ያቅናላችሁ\b", "Have a safe and smooth journey everyone", "መንገዲ የቀንዓልኩም።"),
    (r"\bመልካም ጉዞ\b", "Have a safe trip / Safe travels", "ቡሩኽ ጉዕዞ።"),
    (r"\bበሰላም ግባ\b", "Arrive safely / Safe return home", "ብደሓን እቶ።"),
    (r"\bበሰላም ግቢ\b", "Arrive safely / Safe return home", "ብደሓን እተዊ።"),
    (r"\bበሰላም ግቡ\b", "Arrive safely everyone / Safe return home", "ብደሓን እተዉ።"),
    # Cafe, Buna Culture & Hospitality
    (r"\bቡና ጠጡ\b", "Come join us for coffee / Welcome for coffee", "ቡን ስተዩ።"),
    (r"\bበረካ ሁኑ\b", "May you be blessed with abundance", "በረኻ ኩኑ።"),
    (r"\bእጅህ ይባረክ\b", "Blessed be your hands / Thank you for the delicious treat", "ኣእዳውካ ይባረኽ።"),
    (r"\bእጅሽ ይባረክ\b", "Blessed be your hands / Thank you for the delicious treat", "ኣእዳውኪ ይባረኽ።"),
    (r"\bእጃችሁ ይባረክ\b", "Blessed be your hands everyone / Thank you for the delicious treat", "ኣእዳውኩም ይባረኽ።"),
    # Market, Trade & Bargaining
    (r"\bይቁረጡት\b", "Give me your final rock-bottom price / Settle the price", "ቁረጸለይ።"),
    (r"\bበረከቱ ይግባህ\b", "May your trade and home be blessed with abundance", "በረኸት ይእተወልካ።"),
    (r"\bበረከቱ ይግባሽ\b", "May your trade and home be blessed with abundance", "በረኸት ይእተወልኪ።"),
    (r"\bገበያ ይቅናልህ\b", "May you have fruitful market sales", "ዕዳጋ የቀንዓልካ።"),
    (r"\bገበያ ይቅናሽ\b", "May you have fruitful market sales", "ዕዳጋ የቀንዓልኪ።"),
    (r"\bገበያ ይቅናላችሁ\b", "May you have fruitful market sales everyone", "ዕዳጋ የቀንዓልኩም።"),
    # Civic & Kebele Government Administration
    (r"\bጉዳይህ ይፈጸም\b", "May your administrative matter be successfully resolved", "ጉዳይካ ይፈጸም።"),
    (r"\bጉዳይሽ ይፈጸም\b", "May your administrative matter be successfully resolved", "ጉዳይኪ ይፈጸም።"),
    (r"\bጉዳያችሁ ይፈጸም\b", "May your administrative matter be successfully resolved everyone", "ጉዳይኩም ይፈጸም።"),
    (r"\bስራህ ይቅናህ\b", "May your work and official endeavors succeed", "ስራሕካ የቀንዓልካ።"),
    (r"\bስራሽ ይቅናሽ\b", "May your work and official endeavors succeed", "ስራሕኪ የቀንዓልኪ።"),
    (r"\bስራችሁ ይቅናችሁ\b", "May your work and official endeavors succeed everyone", "ስራሕኩም የቀንዓልኩም።"),
    # Banking, Wealth & Commerce Blessings
    (r"\bገንዘብህ ይባረክ\b", "May your wealth and finances be blessed", "ገንዘብካ ይባረኽ።"),
    (r"\bገንዘብሽ ይባረክ\b", "May your wealth and finances be blessed", "ገንዘብኪ ይባረኽ።"),
    (r"\bገንዘባችሁ ይባረክ\b", "May your wealth and finances be blessed everyone", "ገንዘብኩም ይባረኽ።"),
    (r"\bበረከት ይኑረው\b", "May it have enduring blessing and prosperity", "በረኸት ይሃልዎ።"),
    # Education, Academia & Wisdom
    (r"\bትምህርትህ ያብራህ\b", "May your education illuminate your future", "ትምህርትኻ የብርሃልካ።"),
    (r"\bትምህርትሽ ያብራሽ\b", "May your education illuminate your future", "ትምህርትኺ የብርሃልኪ።"),
    (r"\bትምህርታችሁ ያብራችሁ\b", "May your education illuminate your future everyone", "ትምህርትኹም የብርሃልኩም።"),
    (r"\bእውቀት ይክፈትህ\b", "May wisdom and knowledge open your mind", "ፍልጠት ይኽፈተልካ።"),
    # Legal, Justice & Truth Resolution
    (r"\bእውነትና ፍትህ ያሸንፋል\b", "Truth and justice shall prevail", "ሓቅን ፍትሕን ይስዕር።"),
    (r"\bእውነት ያሸንፋል\b", "The truth will prevail", "ሓቂ ትወጽእ እያ።"),
    (r"\bፍትህ ይሰፍናል\b", "Justice will be served", "ፍትሒ ይነግስ።"),
    (r"\bዳኝነት ይቅናህ\b", "May you find fair justice and resolution", "ፍትሒ ይርከበልካ።"),
]

OROMO_IDIOMS: list[tuple[str, str, str]] = [
    (r"\bharka fuune\b", "Greetings / Welcome", "ሰላምታ አቅርበናል።"),
    (r"\bbaga nagaan dhufte\b", "Welcome! Glad you arrived safely", "እንኳን ደህና መጣህ።"),
    (r"\bbaga nagaan dhuftan\b", "Welcome everyone! Glad you arrived safely", "እንኳን ደህና መጣችሁ።"),
    (r"\brakkoo hin qabu\b", "No problem / Don't worry at all", "ምንም ችግር የለም።"),
    (r"\bfayyaa qabaadhu\b", "Stay healthy and take care", "ጤና ይኑርህ፣ ደህና ሁን።"),
    (r"\bnagaan oolaa\b", "Have a peaceful and wonderful day", "መልካም ቀን ይሁንላችሁ።"),
    (r"\babdii hin kutatin\b", "Don't lose hope / Take courage", "ተስፋ አትቁረጥ / አይዞህ።"),
    (r"\bwanti hundi gaarii dha\b", "Everything is going well", "ሁሉም ነገር ጥሩ ነው።"),
    # Medical & Clinic Empathy
    (r"\bfayyuu kee haa ta'u\b", "May you have a speedy recovery", "እግዜር ይማርህ።"),
    (r"\bfayyuun keessan haa ta'u\b", "May you have a speedy recovery everyone", "እግዜር ይማራችሁ።"),
    (r"\brabbiyyuu si haa fayyisu\b", "May God heal you and restore your health", "እግዚአብሔር ጤናህን ይመልስልህ።"),
    # Road & Transit Safety
    (r"\bnagaan deemi\b", "Safe travels / Go in peace", "መንገዱን ያቅናልህ / በሰላም ሂድ።"),
    (r"\bnagaan deemaa\b", "Safe travels everyone / Go in peace", "መንገዱን ያቅናላችሁ / በሰላም ሂዱ።"),
    (r"\bkaraa nagaa\b", "Safe journey / Travel safely", "መልካም ጉዞ።"),
    (r"\bbaga nagaan geesse\b", "Glad you arrived safely", "እንኳን በሰላም ደረስክ።"),
    (r"\bbaga nagaan geessan\b", "Glad you arrived safely everyone", "እንኳን በሰላም ደረሳችሁ።"),
    # Cafe, Buna Culture & Hospitality
    (r"\bbuna dhugaa\b", "Come join us for coffee / Welcome for coffee", "ቡና ጠጡ።"),
    (r"\bharki kee haa eebbifamu\b", "Blessed be your hands / Thank you for the brew", "እጅህ ይባረክ።"),
    (r"\bharki keessan haa eebbifamu\b", "Blessed be your hands everyone / Thank you for the brew", "እጃችሁ ይባረክ።"),
    (r"\beebba bunaa\b", "Coffee blessing and fellowship", "የቡና በረከት።"),
    # Market, Trade & Bargaining
    (r"\bgatii dhumaa natti himi\b", "Tell me your final rock-bottom price", "የመጨረሻ ዋጋ ንገረኝ / ይቁረጡት።"),
    (r"\bgabaan haa tolu\b", "May you have fruitful market sales", "ገበያ ይቅናልህ።"),
    (r"\beebbi daldalaa siif haa baay'atu\b", "May your trade and business be abundantly blessed", "በረከቱ ይግባህ።"),
    # Civic & Kebele Government Administration
    (r"\bdhimmi kee haa xumuramu\b", "May your administrative matter be successfully resolved", "ጉዳይህ ይፈጸም።"),
    (r"\bdhimmi keessan haa xumuramu\b", "May your administrative matter be successfully resolved everyone", "ጉዳያችሁ ይፈጸም።"),
    (r"\bhojiin siif haa milkaa'u\b", "May your work and endeavors succeed smoothly", "ስራህ ይቅናህ።"),
    # Banking, Wealth & Finance
    (r"\bmaallaqni kee haa eebbifamu\b", "May your money and wealth be blessed", "ገንዘብህ ይባረክ።"),
    (r"\bmaallaqni keessan haa eebbifamu\b", "May your money and wealth be blessed everyone", "ገንዘባችሁ ይባረክ።"),
    (r"\beebbi maallaqaa siif haa baay'atu\b", "May your finances be abundantly blessed", "በረከት ይኑረው።"),
    # Education, Academia & Wisdom
    (r"\bbarumsi kee siif haa ifu\b", "May your education illuminate your future", "ትምህርትህ ያብራህ።"),
    (r"\bbarumsi keessan siif haa ifu\b", "May your education illuminate your future everyone", "ትምህርታችሁ ያብራችሁ።"),
    (r"\bbeekkumsi siif haa bal'atu\b", "May wisdom and knowledge expand within you", "እውቀት ይክፈትህ።"),
    # Legal, Justice & Truth Resolution
    (r"\bdhugaa fi haqi ni injifata\b", "Truth and justice shall prevail", "እውነትና ፍትህ ያሸንፋል።"),
    (r"\bdhugaan ni baha\b", "The truth will come out and prevail", "እውነት ያሸንፋል።"),
    (r"\bhaqi siif haa murtaa'u\b", "May justice be fairly decided for you", "ዳኝነት ይቅናህ / ፍትህ ይሰፍናል።"),
]

TIGRINYA_IDIOMS: list[tuple[str, str, str]] = [
    # Broadcast & Media Introductions
    (r"\bጥዕና\s+ይሃበለይ\s+ከመይ\s+(?:ዲኹም|ኣለኹም)\s+(?:ዝኸበርኩም|ክቡራት)\s+(?:ተመልከትትና|ተዓዘብትና)\b",
     "Hello, how are you honored viewers.",
     "ጤና ይስጥልኝ፣ ክቡራት ተመልካቾቻችን እንደምን ናችሁ።"),
    (r"\bጥዕና\s+ይሃበለይ\s+ከመይ\s+(?:ዲኹም|ኣለኹም)\s+(?:ዝኸበርኩም|ክቡራት)\s+ሰማዕትና\b",
     "Hello, how are you honored listeners.",
     "ጤና ይስጥልኝ፣ ክቡራት አድማጮቻችን እንደምን ናችሁ።"),
    (r"\bጥዕና\s+ይሃበለይ\s+ከመይ\s+(?:ዲኹም|ኣለኹም)\b",
     "Hello, how are you all?",
     "ጤና ይስጥልኝ፣ እንደምን ናችሁ?"),
    (r"\bጥዕና\s+ይሃበለይ\b",
     "Hello / Greetings",
     "ጤና ይስጥልኝ።"),
    (r"\b(?:ዝኸበርኩም|ክቡራት)\s+(?:ተመልከትትና|ተዓዘብትና)\b",
     "Honored viewers",
     "ክቡራት ተመልካቾቻችን"),
    (r"\b(?:ዝኸበርኩም|ክቡራት)\s+ሰማዕትና\b",
     "Honored listeners",
     "ክቡራት አድማጮቻችን"),
    # Courtesies & Comfort
    (r"\bእንቋዕ ብደሓን መጻእካ\b", "Welcome! Glad you arrived safely", "እንኳን ደህና መጣህ።"),
    (r"\bእንቋዕ ብደሓን መጻእኪ\b", "Welcome! Glad you arrived safely", "እንኳን ደህና መጣሽ።"),
    (r"\bእንቋዕ ብደሓን መጻእኩም\b", "Welcome everyone! Glad you arrived safely", "እንኳን ደህና መጣችሁ።"),
    (r"\bኣጆኻ\b", "Stay strong / Take courage", "አይዞህ / በርታ።"),
    (r"\bኣጆኺ\b", "Stay strong / Take courage", "አይዞሽ / በርቺ።"),
    (r"\bኣጆኹም\b", "Stay strong everyone", "አይዟችሁ / በርቱ።"),
    (r"\bእግዚኣብሔር ይሃበለይ\b", "May God reward you / Thank you so much", "እግዚአብሔር ይስጥልኝ።"),
    (r"\bጸገም የለን\b", "No problem / Don't mention it", "ምንም ችግር የለም።"),
    (r"\bቡሩኽ መዓልቲ\b", "Have a blessed day", "የተባረከ ቀን ይሁንልህ።"),
    (r"\bኣይትጨነቕ\b", "Don't worry", "አትጨነቅ።"),
    # Medical & Clinic Empathy
    (r"\bፈጣሪ ይምሓርካ\b", "May God grant you health and recovery", "እግዜር ይማርህ።"),
    (r"\bፈጣሪ ይምሓርኪ\b", "May God grant you health and recovery", "እግዜር ይማርሽ።"),
    (r"\bፈጣሪ ይምሓርኩም\b", "May God grant you health and recovery everyone", "እግዜር ይማራችሁ።"),
    (r"\bእግዚኣብሔር ይምሓርካ\b", "May God grant you health and recovery", "እግዜር ይማርህ።"),
    # Road & Transit Safety
    (r"\bደሓን ኪድ\b", "Safe travels / Go safely", "በሰላም ሂድ።"),
    (r"\bደሓን ኪዲ\b", "Safe travels / Go safely", "በሰላም ሂጂ።"),
    (r"\bደሓን ኪዱ\b", "Safe travels everyone / Go safely", "በሰላም ሂዱ።"),
    (r"\bቡሩኽ ጉዕዞ\b", "Blessed journey / Safe travels", "መልካም ጉዞ።"),
    (r"\bብደሓን እቶ\b", "Arrive safely / Safe return home", "በሰላም ግባ።"),
    (r"\bብደሓን እተዊ\b", "Arrive safely / Safe return home", "በሰላም ግቢ።"),
    (r"\bብደሓን እተዉ\b", "Arrive safely everyone / Safe return home", "በሰላም ግቡ።"),
    # Cafe, Buna Culture & Hospitality
    (r"\bቡን ስተዩ\b", "Come join us for coffee / Welcome for coffee", "ቡና ጠጡ።"),
    (r"\bኣእዳውካ ይባረኽ\b", "Blessed be your hands / Thank you for the delicious treat", "እጅህ ይባረክ።"),
    (r"\bኣእዳውኪ ይባረኽ\b", "Blessed be your hands / Thank you for the delicious treat", "እጅሽ ይባረክ።"),
    (r"\bኣእዳውኩም ይባረኽ\b", "Blessed be your hands everyone / Thank you for the feast", "እጃችሁ ይባረክ።"),
    (r"\bበረኻ ኩኑ\b", "May you be blessed with abundance", "በረካ ሁኑ።"),
    # Market, Trade & Bargaining
    (r"\bቁረጸለይ\b", "Give me your final rock-bottom price / Settle the price", "ይቁረጡት።"),
    (r"\bዕዳጋ የቀንዓልካ\b", "May you have fruitful market sales", "ገበያ ይቅናልህ።"),
    (r"\bዕዳጋ የቀንዓልኪ\b", "May you have fruitful market sales", "ገበያ ይቅናሽ።"),
    (r"\bዕዳጋ የቀንዓልኩም\b", "May you have fruitful market sales everyone", "ገበያ ይቅናላችሁ።"),
    (r"\bበረኸት ይእተወልካ\b", "May your trade and home be blessed with abundance", "በረከቱ ይግባህ።"),
    # Civic & Kebele Government Administration
    (r"\bጉዳይካ ይፈጸም\b", "May your administrative matter be successfully resolved", "ጉዳይህ ይፈጸም።"),
    (r"\bጉዳይኪ ይፈጸም\b", "May your administrative matter be successfully resolved", "ጉዳይሽ ይፈጸም።"),
    (r"\bጉዳይኩም ይፈጸም\b", "May your administrative matter be successfully resolved everyone", "ጉዳያችሁ ይፈጸም።"),
    (r"\bስራሕካ የቀንዓልካ\b", "May your work and official endeavors succeed", "ስራህ ይቅናህ።"),
    # Banking, Wealth & Finance
    (r"\bገንዘብካ ይባረኽ\b", "May your money and wealth be blessed", "ገንዘብህ ይባረክ።"),
    (r"\bገንዘብኪ ይባረኽ\b", "May your money and wealth be blessed", "ገንዘብሽ ይባረክ።"),
    (r"\bገንዘብኩም ይባረኽ\b", "May your money and wealth be blessed everyone", "ገንዘባችሁ ይባረክ።"),
    (r"\bበረኸት ይሃልዎ\b", "May it have enduring blessing and prosperity", "በረከት ይኑረው።"),
    # Education, Academia & Wisdom
    (r"\bትምህርትኻ የብርሃልካ\b", "May your education illuminate your future", "ትምህርትህ ያብራህ።"),
    (r"\bትምህርትኺ የብርሃልኪ\b", "May your education illuminate your future", "ትምህርትሽ ያብራሽ።"),
    (r"\bትምህርትኹም የብርሃልኩም\b", "May your education illuminate your future everyone", "ትምህርታችሁ ያብራችሁ።"),
    (r"\bፍልጠት ይኽፈተልካ\b", "May wisdom and knowledge open your mind", "እውቀት ይክፈትህ።"),
    # Legal, Justice & Truth Resolution
    (r"\bሓቅን ፍትሕን ይስዕር\b", "Truth and justice shall prevail", "እውነትና ፍትህ ያሸንፋል።"),
    (r"\bሓቂ ትወጽእ እያ\b", "The truth will prevail", "እውነት ያሸንፋል።"),
    (r"\bፍትሒ ይነግስ\b", "Justice will be served", "ፍትህ ይሰፍናል።"),
    (r"\bፍትሒ ይርከበልካ\b", "May justice be found for you", "ዳኝነት ይቅናህ።"),
]

SOMALI_IDIOMS: list[tuple[str, str, str]] = [
    (r"\bsoo dhawoow\b", "Welcome!", "እንኳን ደህና መጣህ።"),
    (r"\bsoo dhowow\b", "Welcome!", "እንኳን ደህና መጣህ።"),
    (r"\bdhib ma leh\b", "No problem / Don't worry", "ምንም ችግር የለም።"),
    (r"\bha walwalin\b", "Don't worry", "አትጨነቅ።"),
    (r"\bnasiib wacan\b", "Good luck!", "መልካም እድል!"),
    (r"\bmaalin wanaagsan\b", "Have a wonderful day", "መልካም ቀን።"),
    # Medical & Clinic Empathy
    (r"\balla ha ku caafiyo\b", "May God grant you health and recovery", "እግዜር ይማርህ።"),
    (r"\bilahay ha ku baxsiiyo\b", "May God heal you and grant you relief", "እግዚአብሔር ጤና ይስጥህ።"),
    # Road & Transit Safety
    (r"\bsafaro wanaagsan\b", "Have a safe and pleasant journey", "መልካም ጉዞ።"),
    (r"\bnabad ku tag\b", "Go in peace / Safe travels", "በሰላም ሂድ።"),
    (r"\bnabad ku gaar\b", "Arrive safely", "በሰላም ግባ።"),
    # Cafe, Buna Culture & Hospitality
    (r"\bbun cabba\b", "Come join us for coffee / Welcome for coffee", "ቡና ጠጡ።"),
    (r"\bgacmahaaga ha barakoobeen\b", "Blessed be your hands / Thank you for the delicious treat", "እጅህ ይባረክ።"),
    (r"\bbarakooba\b", "Be blessed and prosper", "የተባረክ ሁን።"),
    # Market, Trade & Bargaining
    (r"\bqiimaha ugu dambeeya ii sheeg\b", "Tell me your final rock-bottom price", "የመጨረሻ ዋጋ ንገረኝ / ይቁረጡት።"),
    (r"\bsuuqu ha kuu barakoobo\b", "May your market trade be blessed and prosperous", "ገበያ ይቅናልህ / በረከቱ ይግባህ።"),
    (r"\biibsasho wacan\b", "Happy shopping and good trade", "መልካም ገበያ።"),
    # Civic & Kebele Government Administration
    (r"\barrintaadu ha fulo\b", "May your official matter be successfully accomplished", "ጉዳይህ ይፈጸም።"),
    (r"\bshaqadu ha kuu hagaagto\b", "May your work proceed smoothly", "ስራህ ይቅናህ።"),
    # Banking, Wealth & Finance
    (r"\blacagtaadu ha barakoowdo\b", "May your money and finances be blessed", "ገንዘብህ ይባረክ።"),
    (r"\blacagtiina ha barakoowdo\b", "May your money and finances be blessed everyone", "ገንዘባችሁ ይባረክ።"),
    (r"\bbarako ha kuu lahaato\b", "May it have enduring blessing and prosperity", "በረከት ይኑረው።"),
    # Education, Academia & Wisdom
    (r"\bwaxbarashadaadu ha kuu iftiinto\b", "May your education illuminate your path", "ትምህርትህ ያብራህ።"),
    (r"\bwaxbarashadiinnu ha idiin iftiinto\b", "May your education illuminate your path everyone", "ትምህርታችሁ ያብራችሁ።"),
    (r"\bcilmi iyo barako ha kuu kordho\b", "May wisdom and knowledge increase upon you", "እውቀት ይክፈትህ።"),
    # Legal, Justice & Truth Resolution
    (r"\brunta iyo caddaaladdu way guulaysan doontaa\b", "Truth and justice shall prevail", "እውነትና ፍትህ ያሸንፋል።"),
    (r"\bcaddaaladdu way shaqaynaysaa\b", "Justice will be done", "ፍትህ ይሰፍናል።"),
    (r"\bxaqa ha laguu garto\b", "May your rightful justice be upheld", "ዳኝነት ይቅናህ።"),
]


class CulturalIdiomEngine:
    """Matches and replaces cultural figures of speech with true semantic equivalents."""

    @classmethod
    def match_cultural_idiom(cls, text: str, src_lang: str, tgt_lang: str = "eng") -> str | None:
        if not text:
            return None
        cleaned = text.strip()
        stripped = re.sub(r"[.!?፣።፧\s]+$", "", cleaned)
        is_target_amh = tgt_lang in ("amh", "amh_Ethi")
        is_target_tir = tgt_lang in ("tir", "tir_Ethi")

        idiom_tables = {
            ("amh", "amh_Ethi"): AMHARIC_IDIOMS,
            ("orm", "gaz_Latn"): OROMO_IDIOMS,
            ("tir", "tir_Ethi"): TIGRINYA_IDIOMS,
            ("som", "som_Latn"): SOMALI_IDIOMS,
        }

        # Defer compound multi-clause sentences to the pipeline's clause-level translator
        multi_clauses = [c.strip() for c in re.split(r'(?<=[.?!።፧!])\s+', cleaned) if c.strip()]
        if len(multi_clauses) > 1:
            return None

        text_words = len(stripped.split())
        for keys, table in idiom_tables.items():
            if src_lang in keys:
                for entry in table:
                    pattern = entry[0]
                    clean_pat = pattern.removeprefix("(?i)")
                    pat_words = len(re.sub(r"[^\w\s]", "", clean_pat).split())
                    # Only match if the utterance is primarily the idiom
                    if text_words <= max(pat_words + 3, 5):
                        if (re.search(clean_pat, cleaned, flags=re.IGNORECASE) or
                                re.search(clean_pat, stripped, flags=re.IGNORECASE)):
                            if is_target_amh and len(entry) >= 3 and src_lang not in ("amh", "amh_Ethi"):
                                return entry[2]
                            if is_target_tir and len(entry) >= 3 and src_lang in ("amh", "amh_Ethi"):
                                return entry[2]
                            return entry[1]
                break

        return None


# ──────────────────────────────────────────────────────────────────
# 2. Intent Classifier
# ──────────────────────────────────────────────────────────────────
class IntentClassifier:
    """Fast rule-based domain and dialogue intent classifier."""

    INTENT_KEYWORDS: dict[IntentType, list[str]] = {
        IntentType.GREETING: [
            "hello", "hi", "how are you", "good morning", "good evening", "goodbye", "bye", "thanks", "thank you",
            "ሰላም", "እንዴት", "እንደምን", "ደህና", "ቻው", "አመሰግናለሁ", "አመሰግናለው",
            "akkam", "nagaa", "fayyaa", "fayyumaa", "fayyummaa", "jirta", "jirtu", "bulte", "oolte", "galatoomi", "galatoomaa",
            "ከመይ", "ደሓን", "የቐንየለይ", "ብሩህ", "ጥዕና", "ጥዕና ይሃበለይ",
            "iska warran", "sidee", "subax", "nabad", "mahadsanid",
        ],
        IntentType.BARGAINING: [
            "how much", "cost", "price", "expensive", "discount", "cheap", "birr", "pay", "money", "dollar",
            "market", "bazaar", "stall", "kilo", "kilogram", "quintal", "weigh", "scale", "final price", "change",
            "cash", "receipt", "total", "seller", "buyer", "vendor", "merchant", "wholesale", "retail", "teff", "onions", "garlic", "berbere", "tomatoes", "potatoes", "produce",
            "ስንት", "ዋጋ", "ብር", "ውድ", "ቅናሽ", "ክፈል", "ገንዘብ",
            "ገበያ", "መርካቶ", "ሱቅ", "ኪሎ", "ኪሎግራም", "ኩንታል", "መዘን", "ሚዛን", "የመጨረሻ ዋጋ", "ይቁረጡት", "መልስ", "ጥሬ ገንዘብ", "ደረሰኝ", "ነጋዴ", "ጠቅላላ", "ጤፍ", "ሽንኩርት", "ነጭ ሽንኩርት", "በርበሬ", "ቲማቲም", "ድንች", "እህል", "አትክልት",
            "meeqa", "gatii", "qaalii", "hir'isi",
            "gabaa", "suuqii", "kiiloo", "kiilogiraama", "kuntaala", "madaali", "madaallii", "gatii dhumaa", "murteessi", "deebii", "maallaqa", "maallaqa callaa", "nagahee", "daldalaa", "waliigala", "xaafii", "qullubbii", "barbarree", "timaatima", "kuduraa",
            "ክንዲ ምንታይ", "ዋጋ", "ቅርሺ", "ክቡር", "ኣጉድለለይ",
            "ዕዳጋ", "ዱኳን", "ኪሎ", "ኪሎግራም", "ኩንታል", "ሚዘን", "ሚዛን", "ናይ መወዳእታ ዋጋ", "ቁረጸለይ", "መልሲ", "ጥረ ገንዘብ", "ቅብሊት", "ነጋዳይ", "ሓፈሻዊ", "ጣፍ", "ሽጉርቲ", "በርበረ", "ቲማቲም", "ኣሕምልቲ",
            "immisa", "qiimo", "qaali", "dhim",
            "suuq", "dukaan", "kiilo", "kiiloogaraam", "kiintaal", "miisaan", "qiimaha ugu dambeeya", "go'ee", "baaqi", "lacag", "lacag cadaan", "rasiid", "ganacsade", "wadarta", "teff", "basal", "toonta", "basbaas", "yaanyo", "qudaar",
        ],
        IntentType.DIRECTIONS: [
            "where", "how to get", "far", "near", "left", "right", "straight", "taxi", "bus", "station", "hotel", "airport",
            "road", "street", "highway", "avenue", "traffic light", "roundabout", "intersection", "turn left", "turn right",
            "go straight", "drop me off", "bus stop", "gas station", "fuel", "petrol", "bajaj", "minibus", "fare", "crossroad", "bridge", "distance", "which direction",
            "የት", "ሩቅ", "ቅርብ", "ቀኝ", "ግራ", "ቀጥታ", "ታክሲ", "አውቶቡስ", "ሆቴል", "ኤርፖርት",
            "መንገድ", "ጎዳና", "አውራ ጎዳና", "አደባባይ", "መታጠፊያ", "ትራፊክ መብራት", "መብራት", "ድልድይ", "ማደያ", "ነዳጅ", "የነዳጅ ማደያ", "አውቶቡስ ተራ", "ባጃጅ", "ሚኒባስ", "ረዳት", "ወደ ግራ", "ወደ ቀኝ", "ቀጥ ብለህ", "አውርደኝ", "አቁም", "ታሪፍ", "የት አካባቢ", "ይርቃል", "ርቀት", "መንገዱ",
            "eessa", "fagoo", "dhihoo", "mirga", "bitaa", "taaksii", "hoteela",
            "karaa", "daandii", "goolbii", "addabaabaayii", "ibsaa tiraafikii", "riqicha", "buufata boba'aa", "buufata", "buufata konkolaataa", "baajaajii", "miiniibaasii", "gargaaraa", "gara bitaatti", "gara mirgaatti", "qajeeli", "asitti na buusi", "na buusi", "dhaabi", "hangam fagaata", "karaa kami", "fageenya", "kaffaltii", "boba'aa",
            "ኣበይ", "ርሑቕ", "ቐረባ", "የማን", "ጸጋም", "ታክሲ", "ሆቴል",
            "መንገዲ", "ጐደና", "መቐየሪ", "ኣደባባይ", "መብራህቲ ትራፊክ", "ድልድል", "መዕደሊ ነዳዲ", "መደበር ኣውቶቡስ", "መደበር", "ባጃጅ", "ሚኒባስ", "ረዳኢ", "ናብ ጸጋም", "ናብ የማን", "ቀጥ ኢልካ", "ኣውርደኒ", "ኣብዚኣ ኣውርደኒ", "ደው በል", "ክንደይ ይርሕቕ", "በየናይ መንገዲ", "ርሕቐት", "ታሪፍ", "ነዳዲ",
            "xaggee", "dhow", "fog", "midig", "bidix", "tagsi", "huteel",
            "waddo", "jid", "waddada", "jidka", "goolad", "wareegto", "laydhka", "laydhka taraafikada", "buundo", "kaalinta shidaalka", "istaanka", "istaanka basaska", "bajaaj", "mataanaha", "darawal", "midig u leexo", "bidix u leexo", "toos u soco", "igu deji", "halkan igu deji", "jooji", "intee bay jirtaa", "xaggee loo maraa", "masaafada", "shidaal",
        ],
        IntentType.DINING: [
            "food", "water", "drink", "eat", "coffee", "tea", "menu", "restaurant", "injera", "shiro", "doro", "bill",
            "cafe", "waiter", "waitress", "macchiato", "jebena", "clay pot", "sugar", "without sugar", "popcorn", "roasted barley",
            "snack", "breakfast", "lunch", "dinner", "fasting food", "bread", "juice", "sweet", "flavor", "order", "cup",
            "ምግብ", "ውሃ", "መጠጥ", "ቡና", "ሻይ", "ሬስቶራንት", "እንጀራ", "ሽሮ", "ዶሮ", "ሒሳብ",
            "ካፌ", "አስተናጋጅ", "ማኪያቶ", "ጀበና", "ጀበና ቡና", "አቦል", "ቶና", "በረካ", "ስኳር", "ያለ ስኳር",
            "ፈንድሻ", "ቆሎ", "ሳምቡሳ", "ቁርስ", "ምሳ", "እራት", "የጾም", "የፍስክ", "ዳቦ", "ጁስ", "ጠጡ", "ብሉ", "ጠረጴዛ", "ሲኒ",
            "nyaata", "bishaan", "dhugii", "dhugaatii", "buna", "shaayee", "injiiraa",
            "kaaffee", "keessummeessituu", "keessummeessaa", "maakiyaatoo", "jabanaa", "buna jabanaa", "abol",
            "sukkaara", "fandishaa", "qollo", "sambuusa", "ciree", "laaqana", "irbaata", "soomaa", "daabboo", "cuunfaa", "dhugaa", "nyaadhaa", "teessoo", "fiinjaan", "herrega",
            "ምግቢ", "ማይ", "ቡን", "ሻሂ", "እንጀራ", "ሒሳብ",
            "ካፈ", "ኣሳላይ", "ማክያቶ", "ጀበና", "ጀበና ቡን", "ኣቦል", "ሽኮር", "ብዘይ ሽኮር",
            "ፈንዲሻ", "ቖሎ", "ሳምቡሳ", "ቁርሲ", "ምሳሕ", "ድራር", "ናይ ጾም", "ባኒ", "ጁስ", "ስተዩ", "ብልዑ", "ሰሌዳ", "ፊንጃን",
            "cunto", "biyo", "cab", "cabbitaan", "bun", "shaah", "biil",
            "kafeega", "mudlab", "maakiyaato", "jabana", "sonkor", "sonkor la'aan", "salool", "sambuus", "quraac", "qado", "casho", "soonka", "rooti", "casiir", "cabba", "cuna", "miis", "koob", "biilka",
        ],
        IntentType.MEDICAL: [
            "hospital", "doctor", "medicine", "pharmacy", "sick", "pain", "hurt", "emergency", "ambulance", "help",
            "physician", "nurse", "prescription", "blood pressure", "blood test", "fever", "temperature", "dizziness", "infection", "headache", "chest pain", "injection", "tablet", "clinic", "laboratory", "malaria",
            "ሆስፒታል", "ሐኪም", "ዶክተር", "የጤና ባለሙያ", "መድሃኒት", "መድኃኒት", "ፋርማሲ", "ህመም", "በሽታ", "ታምሜያለሁ", "ደም ግፊት", "ትኩሳት", "ማዞር", "ጨጓራ", "መርፌ", "ምርመራ", "የደም ምርመራ", "ክሊኒክ", "አምቡላንስ", "እርዳታ", "እርዳኝ", "ላቦራቶሪ", "ወባ", "ኪኒን", "ያመኛል", "ያመዎታል", "ደረቴን", "ራሴን", "ሆዴን",
            "hospitaala", "doktora", "ogeessa fayyaa", "qoricha", "dhukkuba", "dhukkubbii", "dhibee", "dhiibbaa dhiigaa", "ho'a qaamaa", "qandhoo", "garaa kaasaa", "hafura", "lafee", "fayyaa", "kiliniikii", "qorannoo", "cirracha", "gargaarsa", "kiniina", "laaboraatoorii", "busaa", "na dhukkuba", "si dhukkuba",
            "ሆስፒታል", "ሓኪም", "ዶክተር", "መድሃኒት", "ፋርማሲ", "ሕሙም", "ሕማም", "ረስኒ", "ጸቕጢ ደም", "መርፍእ", "መርመራ", "ናይ ደም መርመራ", "ክሊኒክ", "ኣምቡላንስ", "ሓግዘኒ", "ላቦራቶሪ", "ዓሶ", "ኪኒን", "የሕምመኒ", "የሕምም", "ኣፍ-ልበይ", "ኣፍ-ልቢ", "ርእሰይ", "ኸብደይ",
            "cosbitaal", "dhakhtar", "kalkaaliye", "dawo", "farmashiye", "xanuun", "cudur", "bukaankay", "cadaadiska", "cadaadiska dhiigga", "dhiig", "dhiigga", "dhiiggaaga", "qandho", "wareer", "calool xanuun", "cirbad", "baaris", "baaritaanka", "baaritaanka dhiigga", "rugta caafimaadka", "amubalaas", "caawin", "kaniini", "shaybaar", "duumo", "i xanuunaya", "xanuunaysaa", "cabbiraa",
        ],
        IntentType.CIVIC_GOV: [
            "kebele", "woreda", "municipality", "resident id", "id card", "proof of residence", "official seal",
            "stamp", "signature", "vital events", "birth certificate", "marriage certificate", "queue number",
            "officer", "registration", "administration", "public service", "document verification", "kebele office", "application form", "residence",
            "municipal", "service fee", "biometric", "resident identification", "expired resident",
            "ቀበሌ", "ወረዳ", "አስተዳደር", "መታወቂያ", "የነዋሪነት ማረጋገጫ", "ማህተም", "ፊርማ", "የልደት ምስክር ወረቀት",
            "የጋብቻ ምስክር ወረቀት", "የሰነድ ማረጋገጫ", "የሰልፍ ቁጥር", "ቢሮ", "ፀሐፊ", "የቀበሌ መታወቂያ", "የቀበሌ ቢሮ", "ማመልከቻ", "የነዋሪነት", "የልደት", "ፋይዳ",
            "ማዘጋጃ ቤት", "የማዘጋጃ ቤት", "አገልግሎት",
            "ganda", "aanaa", "bulchiinsa", "waraqaa eenyummaa", "eenyummaa", "ragaa jireenyaa", "chaappaa",
            "mallattoo", "ragaa dhalootaa", "ragaa gaa'elaa", "eeyyama", "dabaree", "waajjira", "barreessaa", "iyyannoo", "fayidaa", "waajjira gandaa",
            "mana qopheessaa", "tajaajila", "tajaajila mana qopheessaa",
            "ቀበሌ", "ወረዳ", "ምምሕዳር", "መንነት ወረቐት", "መረጋገጺ መንበሪ", "ማሕተም", "ፊርማ", "ናይ ልደት ምስክር ወረቐት",
            "ናይ መርዓ ምስክር ወረቐት", "ምስክርነት", "ናይ ተራ ቍጽሪ", "ቤት ጽሕፈት", "ጸሓፊ", "መልከቲ", "ፋይዳ", "ናይ ቀበሌ",
            "ማዘጋጃ ቤት", "ናይ ምምሕዳር", "ኣገልግሎት",
            "xaafadda", "degmada", "maamulka", "kaarka aqoonsiga", "aqoonsiga", "caddeynta degganaanshaha",
            "shaabadda", "saxiixa", "shahaadada dhalashada", "shahaadada guurka", "xafiiska", "safka", "karraaniga", "fayda", "xafiiska xaafadda", "codsi",
            "dawladda hoose", "adeegga", "adeegga dawladda hoose",
        ],
        IntentType.BANKING: [
            "bank", "teller", "branch", "deposit", "withdraw", "withdrawal", "transfer", "bank transfer",
            "account number", "passbook", "bankbook", "atm", "atm card", "credit card", "debit card",
            "mobile banking", "telebirr", "cbe birr", "cbebirr", "transaction fee", "pin code",
            "balance inquiry", "check balance", "account balance", "remittance", "foreign exchange",
            "forex", "cash deposit", "swift", "bank slip", "bank counter", "interest rate",
            "savings", "savings account", "deposit cash", "counter",
            "ባንክ", "ቴለር", "ቅርንጫፍ", "ተቀማጭ", "ወጪ", "ማስተላለፍ", "የባንክ ዝውውር", "ሒሳብ ቁጥር", "ሂሳብ ቁጥር",
            "የባንክ ደብተር", "ደብተር", "ኤቲኤም", "የኤቲኤም ካርድ", "ሞባይል ባንኪንግ", "ቴሌብር", "ሲቢኢ ብር",
            "የግብይት ክፍያ", "ፒን ቁጥር", "ቀሪ ሂሳብ", "የሂሳብ መግለጫ", "ሐዋላ", "ሀዋላ", "ምንዛሬ", "የውጭ ምንዛሬ",
            "የባንክ ሰነድ", "የባንክ መስኮት", "ተቀማጭ ገንዘብ", "ቁጠባ", "ቁጠባ ሂሳብ", "ጥሬ ገንዘብ", "ማስገባት", "ማውጣት", "ማሽን",
            "baankii", "teellara", "damee", "damee baankii", "galchuu", "baasuu", "daddabarsuu",
            "lakkoofsa herregaa", "dabalata baankii", "eetiyeemii", "kaardii eetiyeemii",
            "moobaayil baankingi", "teeleebirr", "siibii'ii birr", "kaffaltii daddabarsaa",
            "koodii piinii", "haftee herregaa", "ibsa herregaa", "hawaalaa", "jijjiirraa sharafaa",
            "sharaf", "waraqaa baankii", "foddaa baankii", "qusannaa", "herrega qusannaa", "herrega", "callaa", "maallaqa callaa", "dabalata", "kaardii", "maashina",
            "ባንክ", "ተሌር", "ጨንፈር", "ጨንፈር ባንክ", "ተቐማጢ", "ወጻኢ", "ምምሕልላፍ", "ናይ ባንክ ምምሕልላፍ",
            "ቍጽሪ ሕሳብ", "ደብተር ባንክ", "ኤቲኤም", "ካርድ ኤቲኤም", "ሞባይል ባንኪንግ", "ቴሌብር", "ሲቢኢ ብር",
            "ክፍሊት ኣገልግሎት", "ፒን ኮድ", "ተረፍ ሕሳብ", "መግለጺ ሕሳብ", "ሓዋላ", "ሸርፊ", "ናይ ወጻኢ ሸርፊ",
            "ፎርም ባንክ", "መስኮት ባንክ", "ቁጠባ", "ናይ ቁጠባ ሕሳብ", "ሕሳብ", "ጥረ ገንዘብ", "ምእታው", "ምውጻእ", "ማሽን",
            "bangiga", "laanta", "lacag dhigasho", "lacag bixin", "lacag qaadasho", "wareejin",
            "wareejinta bangiga", "lambarka akoonka", "buugga bangiga", "atm", "kaarka atm-ka",
            "bangiga mobaylka", "telebirr", "cbe birr", "khidmadda xawaaladda", "pin code",
            "haraaga xisaabta", "bayaanka xisaabta", "xawaalad", "sarrif", "sarrifka lacagaha qalaad",
            "foomka bangiga", "daaqadda bangiga", "kaydka", "akoonka kaydka", "akoon", "lacag caddaan ah", "ku shubo", "mishiinka",
        ],
        IntentType.EDUCATION: [
            "school", "university", "campus", "registrar", "tuition", "tuition fee", "semester", "transcript", "transcripts",
            "diploma", "degree", "degrees", "grade report", "grade", "grades", "department", "student id", "dorm", "dormitory", "dormitories", "dormitory room",
            "exam", "exams", "examination", "examinations", "admission", "admitted", "enrollment", "certificate", "teacher", "teachers", "student", "students", "class", "classes",
            "library", "lecture", "faculty", "academic", "course", "courses", "curriculum", "graduation",
            "ትምህርት ቤት", "ዩኒቨርሲቲ", "ግቢ", "ሬጅስትራር", "የትምህርት ክፍያ", "ሴሚስተር", "ትራንስክሪፕት", "የትራንስክሪፕት",
            "ዲፕሎማ", "ዲግሪ", "የዲግሪ", "ውጤት", "የትምህርት ክፍል", "የተማሪ መታወቂያ", "ዶርም", "ፈተና", "ምዝገባ",
            "ሰርተፊኬት", "ምስክር ወረቀት", "የምስክር ወረቀት", "መምህር", "ተማሪ", "ክፍል", "ቤተ መጻሕፍት", "ምረቃ", "ትምህርት",
            "mana barumsaa", "yuunivarsiitii", "mooraa", "rejistiraara", "kaffaltii barumsaa", "samiisteera",
            "tiraanskiriiptii", "dippiloomaa", "digirii", "qabxii", "kutaalee", "waraqaa eenyummaa barataa",
            "doormii", "qormaata", "galmee", "waraqaa ragaa", "barsiisaa", "barataa", "kutaa", "mana kitaabaa", "eebba", "barumsa",
            "ቤት ትምህርቲ", "ዩኒቨርሲቲ", "ግቢ", "ሬጅስትራር", "ክፍሊት ትምህርቲ", "ሰሚስተር", "ትራንስክሪፕት", "ናይ ትራንስክሪፕት",
            "ዲፕሎማ", "ዲግሪ", "ናይ ዲግሪ", "ውጽኢት", "ክፍሊ", "መንነት ወረቐት ተማሂሮ", "ዶርም", "ፈተና", "ምዝገባ",
            "ምስክር ወረቐት", "መምህር", "ተማሃራይ", "ቤተ መጻሕፍቲ", "ምረቓ", "ትምህርቲ",
            "dugsi", "jaamacad", "xarunta jaamacadda", "diiwaangeliyaha", "lacagta waxbarashada", "simistar",
            "shahaadada natiijooyinka", "transcript", "diploma", "shahaadada jaamacadda", "natiijada",
            "waaxda", "kaarka ardayga", "hoyga ardayda", "hoyga", "imtixaan", "imtixaanka", "jadwalka",
            "jadwalka imtixaanka", "qolalka imtixaanka", "diiwaangelin", "shahaado",
            "macallin", "arday", "fasal", "maktabadda", "qalinjabinta", "waxbarasho", "waxbarashada",
            "xafiiska diiwaangeliyaha", "kharash-wadaagga",
            "biiroo rejistiraaraa", "rejistiraaraa", "barumsaa", "waraqaa qulqullinaa", "baasii qooddachuu", "add-drop", "sagantaa qormaata", "sagantaa qormaataa",
            "የሬጅስትራር ቢሮ", "የትምህርት", "ክሊራንስ", "ኮስት ሼሪንግ", "አድ-ድሮፕ", "የፈተና", "የጊዜ ሰሌዳ", "የፈተና ፕሮግራም",
            "ቤት ጽሕፈት ሬጅስትራር", "ናይ ትምህርቲ", "ኮስት ሸሪንግ", "ኣድ-ድሮፕ", "ናይ ፈተና", "ናይ ግዜ ሰሌዳ",
            "registrar's office", "tuition payment", "cost-sharing", "timetable", "exam schedule", "examination timetable",
        ],
        IntentType.LEGAL_POLICE: [
            "police", "police station", "police officer", "officer", "crime", "theft", "stolen", "thief", "robbery",
            "assault", "attacked", "victim", "suspect", "witness", "testimony", "statement", "complaint",
            "formal complaint", "investigation", "investigator", "criminal", "dispute", "lawsuit", "court",
            "lawyer", "attorney", "bail", "evidence", "handcuff", "case file", "accused",
            "crime report", "formal crime report", "burglarized", "broken into", "theft complaint",
            "ፖሊስ", "ፖሊስ ጣቢያ", "ጣቢያ", "ወንጀል", "የወንጀል", "ስርቆት", "ሌባ", "ተሰረቀ", "ጥቃት", "የደረሰብኝ ጥቃት",
            "ምስክር", "ቃል መስጠት", "ቃል", "አቤቱታ", "የወንጀል አቤቱታ", "የስርቆት አቤቱታ", "ምርመራ", "መርማሪ", "መርማሪ ፖሊስ", "ክስ", "የክስ መዝገብ",
            "ፍርድ ቤት", "ጠበቃ", "ተጠርጣሪ", "ተጎጂ", "ዋስትና", "ማስረጃ", "አለመግባባት", "ጸጥታ",
            "poolisii", "buufata poolisii", "saara", "yakka", "yakkaa", "hanna", "hattummaa", "hatame", "hatameef", "hatameera", "hataman", "haleellaa",
            "miidhamaa", "shakkamaa", "ragaa", "ragaa baatuu", "ibsa", "ibsa seeraa", "komii", "iyyannoo yakkaa", "qorannoo",
            "qorataa", "himannaa", "galmee himannaa", "mana murtii", "abukaatoo", "wabiidhaan", "wal dhabdee",
            "ፖሊስ", "መደበር ፖሊስ", "ጣብያ ፖሊስ", "ገበን", "ናይ ገበን", "ስርቂ", "ሰራቒ", "ተሰሪቑ", "ተሰሪቖም", "መጥቃዕቲ",
            "ግዳይ", "ተጠርጣሪ", "ምስክር", "ቃል ምሃብ", "ቃል", "ጥርዓን", "ናይ ገበን ጥርዓን", "መርመራ", "መርማሪ", "መርማሪ ፖሊስ",
            "ክሲ", "መዝገብ ክሲ", "ቤት ፍርዲ", "ጠበቓ", "ዋሕስ", "መርትዖ", "ዘይምርድዳእ",
            "boolis", "booliska", "saldhigga booliska", "saldhig", "dambi", "dambiga", "dambiyeed", "cabasho dambiyeed", "xatooyo", "tuug",
            "la xaday", "la jabsaday", "weerar", "dhibane", "eedeysane", "markhaati", "qoraal sharci ah", "cabasho",
            "baaritaan", "baare", "baareha", "sarkaal baare", "sarkaalka baareha dambiyada", "dambiyada", "dacwad", "diwaanka dacwadda", "maxkamad", "qareen",
            "dammaanad", "caddayn", "muran", "lambarka galka",
        ],
    }

    @classmethod
    def classify(cls, text: str) -> IntentType:
        if not text:
            return IntentType.GENERAL

        normalized = text.lower()
        scores: dict[IntentType, int] = {intent: 0 for intent in IntentType}

        for intent, keywords in cls.INTENT_KEYWORDS.items():
            for kw in keywords:
                # Word-boundary check matching Latin words and Ge'ez words with optional proclitics/enclitics
                pattern = r"(?:\b|^|\s|[የለበከን])" + re.escape(kw.lower()) + r"(?:\b|$|\s|[!?,.:;፣።፧ንውምቴ])"
                if re.search(pattern, normalized):
                    scores[intent] += 1

        # If a substantive domain intent is present alongside a courteous opening greeting (e.g., "Akkam jirtu, ..."),
        # prioritize the operative substantive domain intent
        non_greeting_scores = {k: v for k, v in scores.items() if k != IntentType.GREETING}
        best_substantive = max(non_greeting_scores, key=non_greeting_scores.get)  # type: ignore
        if non_greeting_scores[best_substantive] > 0:
            if non_greeting_scores[best_substantive] >= scores[IntentType.GREETING] or scores[IntentType.GREETING] <= 2:
                return best_substantive

        best_intent = max(scores, key=scores.get)  # type: ignore
        return best_intent if scores[best_intent] > 0 else IntentType.GENERAL


# ──────────────────────────────────────────────────────────────────
# 3. Formality & Register Controller
# ──────────────────────────────────────────────────────────────────
class FormalityController:
    """Adapts translation phrasing between honorific/polite and familiar/casual registers."""

    @classmethod
    def apply_formality(cls, text: str, tgt_lang: str, formality: str) -> str:
        if not text or formality not in ("polite", "formal"):
            return text

        result = text
        # If targeting Amharic: elevate familiar 'ነህ/ነሽ' to honorific 'እርስዎ / ኖት'
        if tgt_lang in ("amh", "amh_Ethi"):
            result = re.sub(r"\bእንዴት ነህ\b", "እንዴት ኖት", result)
            result = re.sub(r"\bእንዴት ነሽ\b", "እንዴት ኖት", result)
            result = re.sub(r"\bደህና ነህ\b", "ደህና ኖት", result)
            result = re.sub(r"\bደህና ነሽ\b", "ደህና ኖት", result)
            result = re.sub(r"\bእባክህ\b", "እባክዎ", result)
            result = re.sub(r"\bእባክሽ\b", "እባክዎ", result)
            result = re.sub(r"\bአመሰግናለሁ\b", "እጅግ አድርጌ አመሰግናለሁ", result)

        # If targeting Tigrinya: elevate familiar to plural/honorific 'ኣለኹም'
        elif tgt_lang in ("tir", "tir_Ethi"):
            result = re.sub(r"\bከመይ ኣለኻ\b", "ከመይ ኣለኹም", result)
            result = re.sub(r"\bከመይ ኣለኺ\b", "ከመይ ኣለኹም", result)
            result = re.sub(r"\bደሓን ዲኻ\b", "ደሓን ዲኹም", result)
            result = re.sub(r"\bደሓን ዲኺ\b", "ደሓን ዲኹም", result)
            result = re.sub(r"\bበጃኻ\b", "በጃኹም", result)
            result = re.sub(r"\bበጃኺ\b", "በጃኹም", result)

        return result


# ──────────────────────────────────────────────────────────────────
# 4. Multi-Turn Context Manager
# ──────────────────────────────────────────────────────────────────
@dataclass
class ConversationTurn:
    turn_id: int
    src_lang: str
    tgt_lang: str
    source_text: str
    translated_text: str
    intent: IntentType
    timestamp: float = field(default_factory=time.time)


class SmartContextManager:
    """Tracks dialogue history and resolves contextual ellipsis."""

    _sessions: dict[str, list[ConversationTurn]] = {}

    @classmethod
    def get_history(cls, session_id: str) -> list[ConversationTurn]:
        return cls._sessions.get(session_id, [])

    @classmethod
    def add_turn(
        cls,
        session_id: str,
        src_lang: str,
        tgt_lang: str,
        source_text: str,
        translated_text: str,
        intent: IntentType,
    ) -> None:
        if session_id not in cls._sessions:
            cls._sessions[session_id] = []
        turns = cls._sessions[session_id]
        turns.append(
            ConversationTurn(
                turn_id=len(turns) + 1,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                source_text=source_text,
                translated_text=translated_text,
                intent=intent,
            )
        )
        # Keep maximum 10 recent turns to preserve memory
        if len(turns) > 10:
            cls._sessions[session_id] = turns[-10:]

    @classmethod
    def resolve_contextual_ellipsis(cls, text: str, src_lang: str, session_id: str | None) -> str:
        """Resolve short queries (e.g. 'Where is it?', 'How much?') using recent entities."""
        if not session_id or session_id not in cls._sessions:
            return text

        history = cls._sessions[session_id]
        if not history:
            return text

        last_turn = history[-1]
        resolved = text.strip()

        # Entity extraction from previous turn (e.g., taxi, hospital, hotel)
        prev_text = (last_turn.source_text + " " + last_turn.translated_text).lower()

        entity = None
        if "hospital" in prev_text or "ሆስፒታል" in prev_text or "hospitaala" in prev_text:
            entity = ("hospital", "ሆስፒታል", "hospitaalichi", "ሆስፒታል")
        elif "taxi" in prev_text or "ታክሲ" in prev_text or "taaksii" in prev_text:
            entity = ("taxi", "ታክሲ", "taaksii", "ታክሲ")
        elif "hotel" in prev_text or "ሆቴል" in prev_text:
            entity = ("hotel", "ሆቴል", "hoteela", "ሆቴል")
        elif "water" in prev_text or "ውሃ" in prev_text or "bishaan" in prev_text:
            entity = ("water", "ውሃ", "bishaan", "ማይ")

        if entity:
            # If user asks "Where is it?" -> "Where is the [entity]?"
            if resolved.lower() in ("where is it", "where is it?", "where is that", "where?"):
                resolved = f"Where is the {entity[0]}?"
            elif resolved in ("የት ነው", "የት ነው?", "የት"):
                resolved = f"{entity[1]} የት ነው?"
            elif resolved.lower() in ("eessa jira", "eessa jira?", "eessa?"):
                resolved = f"{entity[2]} eessa jira?"
            elif resolved in ("ኣበይ ኣሎ", "ኣበይ ኣሎ?", "ኣበይ"):
                resolved = f"{entity[3]} ኣበይ ኣሎ?"

            # If user asks "How much?" -> "How much is the [entity]?"
            elif resolved.lower() in ("how much", "how much?", "how much is it", "how much is it?"):
                resolved = f"How much is the {entity[0]}?"
            elif resolved in ("ስንት ነው", "ስንት ነው?", "ስንት"):
                resolved = f"የ{entity[1]} ዋጋ ስንት ነው?"

        return resolved


# ──────────────────────────────────────────────────────────────────
# 5. Smart Quick-Reply Suggestions Engine
# ──────────────────────────────────────────────────────────────────
class SmartSuggestionsEngine:
    """Generates relevant contextual reply chips for the other speaker."""

    SUGGESTIONS_MAP: dict[IntentType, dict[str, list[dict[str, str]]]] = {
        IntentType.GREETING: {
            "amh": [
                {"text": "ደህና ነኝ አመሰግናለሁ", "translation": "I am fine, thank you."},
                {"text": "አንተስ እንዴት ነህ?", "translation": "And how are you?"},
                {"text": "ስላገኘሁህ ደስ ብሎኛል", "translation": "Nice to meet you."},
            ],
            "eng": [
                {"text": "I'm doing well, thank you!", "translation": "ደህና ነኝ አመሰግናለሁ!"},
                {"text": "How are you doing today?", "translation": "ዛሬ እንዴት ነህ?"},
                {"text": "Nice to meet you!", "translation": "ስላገኘሁህ ደስ ብሎኛል!"},
            ],
            "orm": [
                {"text": "Fayyaa dha, galatoomi.", "translation": "I am fine, thank you."},
                {"text": "Akkam jirta ati?", "translation": "And how are you?"},
                {"text": "Si arguun koo gammachuu dha.", "translation": "Nice to meet you."},
            ],
            "tir": [
                {"text": "ደሓን እየ የቐንየለይ።", "translation": "I am fine, thank you."},
                {"text": "ንስኻኸ ከመይ ኣለኻ?", "translation": "And how are you?"},
                {"text": "ምስራኸብና ደስ ኢሉኒ።", "translation": "Nice to meet you."},
            ],
            "som": [
                {"text": "Waan fiicanahay, mahadsanid.", "translation": "I am fine, thank you."},
                {"text": "Adiguna sidee tahay?", "translation": "And how are you?"},
                {"text": "Waan ku faraxsanahay la kulankaaga.", "translation": "Nice to meet you."},
            ],
        },
        IntentType.BARGAINING: {
            "amh": [
                {"text": "የመጨረሻ ዋጋህ ስንት ነው? ይቁረጡት", "translation": "What is your rock-bottom price? Cut to the chase."},
                {"text": "ሁለት ኪሎ መዝነህ ስጠኝ", "translation": "Please weigh and give me two kilograms."},
                {"text": "ብዙ ከገዛሁ ቅናሽ ታደርጋለህ?", "translation": "Will you discount if I buy in bulk?"},
                {"text": "እሺ እወስደዋለሁ፣ መልሴን ስጠኝ", "translation": "Okay I'll take it, please give me my change."},
            ],
            "eng": [
                {"text": "What is your absolute final price? Let's settle it.", "translation": "የመጨረሻ ዋጋህ ስንት ነው? እንቁረጠው።"},
                {"text": "Please weigh two kilograms for me.", "translation": "እባክህ ሁለት ኪሎ መዝነህ ስጠኝ።"},
                {"text": "Can you give me a discount if I take several items?", "translation": "ብዙ ከወሰድኩ ቅናሽ ልታደርግልኝ ትችላለህ?"},
                {"text": "Deal, I will take it! Here is the cash.", "translation": "ተስማምቻለሁ፣ እወስደዋለሁ! ገንዘቡ ይኸውልህ።"},
            ],
            "orm": [
                {"text": "Gatii dhumaa meeqaan naaf goota? Mee murteessi.", "translation": "What is your final price? Settle it."},
                {"text": "Kiiloo lama madaaltee naaf kenni mee.", "translation": "Please weigh and give me two kilograms."},
                {"text": "Yoo hedduminaan bite gatii naaf hir'iftaa?", "translation": "Will you give me a discount if I buy in quantity?"},
                {"text": "Tole nan fudhadha, deebii koo naaf kenni.", "translation": "Okay I will take it, give me my change."},
            ],
            "tir": [
                {"text": "ናይ መወዳእታ ዋጋ ክንዲ ምንታይ እዩ? ቁረጸለይ።", "translation": "What is your final price? Settle it."},
                {"text": "ክልተ ኪሎ ሚዚንካ ሃበኒ በጃኻ።", "translation": "Please weigh and give me two kilograms."},
                {"text": "ብዙሕ እንተዓዲገ ዋጋ ተጉድለለይዶ?", "translation": "Will you give me a discount if I buy a lot?"},
                {"text": "ሕራይ ክወስዶ እየ፣ መልሰይ ሃበኒ።", "translation": "Okay I will take it, give me my change."},
            ],
            "som": [
                {"text": "Waa imisa qiimaha ugu dambeeya? Go'ee.", "translation": "What is your final price? Settle it."},
                {"text": "Fadlan laba kiilo ii miis.", "translation": "Please weigh two kilograms for me."},
                {"text": "Haddii aan wax badan gato ma ii dhimaysaa?", "translation": "Will you give me a discount if I buy a lot?"},
                {"text": "Haye waan qaadanayaa, baaqigayga i sii.", "translation": "Okay I will take it, give me my change."},
            ],
        },
        IntentType.DIRECTIONS: {
            "amh": [
                {"text": "እዚህ ጋር አውርደኝ እባክህ", "translation": "Please drop me off here."},
                {"text": "ወደ ቀኝ ወይስ ወደ ግራ ልታጠፍ?", "translation": "Should I turn right or left?"},
                {"text": "በእግር ስንት ደቂቃ ይወስዳል?", "translation": "How many minutes does it take on foot?"},
                {"text": "ታሪፉ ስንት ብር ነው?", "translation": "How much is the fare?"},
            ],
            "eng": [
                {"text": "Please drop me off right here.", "translation": "እባክህ እዚህ ጋር አውርደኝ።"},
                {"text": "Should I turn left or right at the corner?", "translation": "መታጠፊያው ላይ ወደ ግራ ወይስ ወደ ቀኝ ልታጠፍ?"},
                {"text": "How many minutes will it take on foot?", "translation": "በእግር ስንት ደቂቃ ይወስዳል?"},
                {"text": "What is the standard fare for this trip?", "translation": "የዚህ ጉዞ መደበኛ ታሪፍ ስንት ነው?"},
            ],
            "orm": [
                {"text": "Asumaan na buusi maaloo.", "translation": "Please drop me off here."},
                {"text": "Gara mirgaatti moo gara bitaatti maqa?", "translation": "Should I turn right or left?"},
                {"text": "Miilaan daqiiqaa meeqa fudhata?", "translation": "How many minutes does it take on foot?"},
                {"text": "Kaffaltiin taaksichaa meeqa?", "translation": "How much is the fare?"},
            ],
            "tir": [
                {"text": "ኣብዚኣ ኣውርደኒ በጃኻ።", "translation": "Please drop me off here."},
                {"text": "ናብ የማን ወይስ ናብ ጸጋም ክጥወቕ?", "translation": "Should I turn right or left?"},
                {"text": "ብእግሪ ክንደይ ደቒቕ ይወስድ?", "translation": "How many minutes does it take on foot?"},
                {"text": "ናይ ጉዕዞ ታሪፍ ክንዲ ምንታይ እዩ?", "translation": "How much is the fare?"},
            ],
            "som": [
                {"text": "Fadlan halkan igu deji.", "translation": "Please drop me off here."},
                {"text": "Miyaan bidix u leexdaa mise midig?", "translation": "Should I turn left or right?"},
                {"text": "Lug ahaan imisa daqiiqo ayay qaadanaysaa?", "translation": "How many minutes does it take on foot?"},
                {"text": "Waa imisa lacagta gaarigu?", "translation": "How much is the fare?"},
            ],
        },
        IntentType.DINING: {
            "amh": [
                {"text": "አንድ ጀበና ቡና እና ፈንድሻ አምጣልኝ", "translation": "Bring me one clay-pot coffee and popcorn."},
                {"text": "ያለ ስኳር ማኪያቶ እፈልጋለሁ", "translation": "I would like a macchiato without sugar."},
                {"text": "የጾም ምግብ ምን አለ?", "translation": "What fasting food do you have available?"},
                {"text": "እባክህ ሒሳቡን አምጣልኝ", "translation": "Please bring me the bill."},
            ],
            "eng": [
                {"text": "I would like one traditional pot coffee and popcorn.", "translation": "አንድ ጀበና ቡና እና ፈንድሻ እፈልጋለሁ።"},
                {"text": "Could I get a macchiato without sugar?", "translation": "ያለ ስኳር ማኪያቶ ማግኘት እችላለሁ?"},
                {"text": "What fasting or vegetarian dishes do you have?", "translation": "ምን የጾም ወይም የአትክልት ምግቦች አሏችሁ?"},
                {"text": "Could you please bring us the bill?", "translation": "እባክህ ሒሳቡን ልታመጣልን ትችላለህ?"},
            ],
            "orm": [
                {"text": "Buna jabanaa tokkoo fi fandishaa naaf fidi.", "translation": "Bring me one clay-pot coffee and popcorn."},
                {"text": "Sukkaara malee maakiyaatoo nan barbaada.", "translation": "I want a macchiato without sugar."},
                {"text": "Nyaata soomaa maal qabdu?", "translation": "What fasting food do you have?"},
                {"text": "Maaloo herrega naaf fidi.", "translation": "Please bring me the bill."},
            ],
            "tir": [
                {"text": "ሓደ ጀበና ቡንን ፈንዲሻን ኣምጽኣለይ።", "translation": "Bring me one clay-pot coffee and popcorn."},
                {"text": "ብዘይ ሽኮር ማክያቶ እደሊ ኣለኹ።", "translation": "I would like a macchiato without sugar."},
                {"text": "ናይ ጾም ምግቢ እንታይ ኣሎ?", "translation": "What fasting food do you have?"},
                {"text": "በጃኻ ሒሳብ ኣምጽኣለይ።", "translation": "Please bring me the bill."},
            ],
            "som": [
                {"text": "Hal jabana oo bun ah iyo salool ii keen.", "translation": "Bring me one clay-pot coffee and popcorn."},
                {"text": "Waxaan rabaa maakiyaato sonkor la'aan ah.", "translation": "I want a macchiato without sugar."},
                {"text": "Cunto caynkee ah oo soon ah ayaad haysaan?", "translation": "What fasting food do you have?"},
                {"text": "Fadlan biilka ii keen.", "translation": "Please bring me the bill."},
            ],
        },
        IntentType.MEDICAL: {
            "amh": [
                {"text": "የት አካባቢ ነው የሚያመዎት?", "translation": "Where is the pain located?"},
                {"text": "መድኃኒቱን ከምግብ በኋላ ይውሰዱ", "translation": "Take the medicine after meals."},
                {"text": "የደም ግፊት ምርመራ እናደርጋለን", "translation": "We will check your blood pressure."},
                {"text": "አስቸኳይ ሐኪም ጥሩልኝ", "translation": "Please call a doctor immediately."},
            ],
            "eng": [
                {"text": "Where does it hurt the most?", "translation": "የት አካባቢ በይበልጥ ያመዎታል?"},
                {"text": "Take this medicine after meals.", "translation": "ይህን መድኃኒት ከምግብ በኋላ ይውሰዱ።"},
                {"text": "We need to check your blood pressure.", "translation": "የደም ግፊትዎን መለካት አለብን።"},
                {"text": "Please call a doctor immediately.", "translation": "እባክዎ በአስቸኳይ ሐኪም ጥሩ።"},
            ],
            "orm": [
                {"text": "Bakka kamtu caalaatti si dhukkuba?", "translation": "Where does it hurt the most?"},
                {"text": "Qoricha kana nyaata booda fudhadhu.", "translation": "Take this medicine after meals."},
                {"text": "Dhiibbaa dhiigaa kee safaruu qabna.", "translation": "We must check your blood pressure."},
                {"text": "Dafaa ogeessa fayyaa naaf waamaa.", "translation": "Please call a doctor immediately."},
            ],
            "tir": [
                {"text": "ኣየናይ ቦታ እዩ ዝያዳ ዘሕምመካ?", "translation": "Where does it hurt the most?"},
                {"text": "እዚ መድሃኒት ድሕሪ ምግቢ ውሰዶ።", "translation": "Take this medicine after meals."},
                {"text": "ጸቕጢ ደምካ ክንልክዖ ኣለና።", "translation": "We must check your blood pressure."},
                {"text": "ቀልጢፍኩም ሓኪም ጸውዑለይ።", "translation": "Please call a doctor immediately."},
            ],
            "som": [
                {"text": "Xaggee ayaa ugu daran xanuunku?", "translation": "Where does it hurt the most?"},
                {"text": "Daawadan qaado cuntada kadib.", "translation": "Take this medicine after meals."},
                {"text": "Waa inaan cabbirnaa cadaadiska dhiiggaaga.", "translation": "We must measure your blood pressure."},
                {"text": "Fadlan degdeg iigu wac dhakhtarka.", "translation": "Please call the doctor immediately."},
            ],
        },
        IntentType.CIVIC_GOV: {
            "amh": [
                {"text": "የመታወቂያ እድሳት ማመልከቻ እፈልጋለሁ", "translation": "I would like an application for ID renewal."},
                {"text": "ማህተም የሚደረገው በየትኛው ቢሮ ነው?", "translation": "Which office stamps and seals the document?"},
                {"text": "የነዋሪነት ማረጋገጫ ወረቀት ይኸውልዎት", "translation": "Here is my proof of residence document."},
                {"text": "የሰልፍ ቁጥሬ ስንት ነው?", "translation": "What is my queue ticket number?"},
            ],
            "eng": [
                {"text": "I would like to apply for an ID card renewal.", "translation": "የመታወቂያ እድሳት ማመልከቻ እፈልጋለሁ።"},
                {"text": "Which room handles official document stamping?", "translation": "ማህተም የሚደረገው በየትኛው ክፍል ነው?"},
                {"text": "Here is my official proof of residence.", "translation": "የነዋሪነት ማረጋገጫ ወረቀቴ ይኸውልዎት።"},
                {"text": "Where do I take a queue ticket number?", "translation": "የሰልፍ ቁጥር ከየት ነው የምወስደው?"},
            ],
            "orm": [
                {"text": "Iyyannoo haaromsa waraqaa eenyummaa nan barbaada.", "translation": "I want an ID renewal application."},
                {"text": "Kutaan chaappaa dha'u kami?", "translation": "Which room does the official stamping?"},
                {"text": "Waraqaan ragaa jireenyaa koo kunooti.", "translation": "Here is my proof of residence."},
                {"text": "Lakkofsi dabaree koo meeqa?", "translation": "What is my queue number?"},
            ],
            "tir": [
                {"text": "ናይ መንነት ወረቐት ሕዳሰ መልከቲ እደሊ ኣለኹ።", "translation": "I want an ID renewal application."},
                {"text": "ማሕተም ዝግበረሉ ክፍሊ ኣየናይ እዩ?", "translation": "Which room does the official stamping?"},
                {"text": "ናይ መንበሪ መረጋገጺ ወረቐተይ እንሆልኩም።", "translation": "Here is my proof of residence."},
                {"text": "ናይ ተራ ቍጽረይ ክንዲ ምንታይ እዩ?", "translation": "What is my queue number?"},
            ],
            "som": [
                {"text": "Waxaan rabaa codsiga cusboonaysiinta kaarka aqoonsiga.", "translation": "I want an ID renewal application."},
                {"text": "Qolkee baa lagu dhuftaa shaabadda?", "translation": "Which room does the official stamping?"},
                {"text": "Kani waa warqaddii caddeynta degganaanshaha.", "translation": "Here is my proof of residence."},
                {"text": "Waa imisa lambarka safkaygu?", "translation": "What is my queue number?"},
            ],
        },
        IntentType.BANKING: {
            "amh": [
                {"text": "በቴሌብር ወይም በሲቢኢ ብር ማስተላለፍ እችላለሁ?", "translation": "Can I transfer via Telebirr or CBE Birr?"},
                {"text": "ወደ ሒሳቤ ገንዘብ ማስገባት እፈልጋለሁ", "translation": "I want to deposit money into my account."},
                {"text": "እባክዎን ቀሪ ሂሳቤን ያረጋግጡልኝ", "translation": "Please check my account balance."},
                {"text": "የኤቲኤም ካርዴ ተውጧል፣ ምን ማድረግ አለብኝ?", "translation": "My ATM card was captured, what should I do?"},
            ],
            "eng": [
                {"text": "Can I transfer funds via Telebirr or CBE Birr?", "translation": "በቴሌብር ወይም በሲቢኢ ብር ማስተላለፍ እችላለሁ?"},
                {"text": "I would like to deposit cash into my savings account.", "translation": "ወደ ቁጠባ ሂሳቤ ገንዘብ ማስገባት እፈልጋለሁ።"},
                {"text": "Could you please check my remaining account balance?", "translation": "እባክዎን ቀሪ የሂሳብ መጠኔን ሊያረጋግጡልኝ ይችላሉ?"},
                {"text": "My ATM card was swallowed by the machine, please help.", "translation": "የኤቲኤም ካርዴ በማሽኑ ተውጧል፣ እባክዎን ይርዱኝ።"},
            ],
            "orm": [
                {"text": "Teeleebirrii yookiin Siibii'ii Birriin daddabarsuu danda'aa?", "translation": "Can I transfer via Telebirr or CBE Birr?"},
                {"text": "Herrega koo keessatti maallaqa galchuu barbaada.", "translation": "I want to deposit money into my account."},
                {"text": "Maaloo haftee herrega kootii naaf mirkaneessaa.", "translation": "Please verify my account balance."},
                {"text": "Kaardiin eetiyeemii koo maashiniin qabameera, maal gochuu qaba?", "translation": "My ATM card was captured, what should I do?"},
            ],
            "tir": [
                {"text": "ብቴሌብር ወይስ ብሲቢኢ ብር ከመሓላልፍ እኽእልዶ?", "translation": "Can I transfer via Telebirr or CBE Birr?"},
                {"text": "ናብ ቍጽሪ ሕሳበይ ገንዘብ ከእቱ እደሊ ኣለኹ።", "translation": "I want to deposit money into my account."},
                {"text": "በጃኹም ተረፍ ሕሳበይ ኣረጋግጹለይ።", "translation": "Please verify my account balance."},
                {"text": "ካርድ ኤቲኤመይ ተወሓጢኒ፣ እንታይ ክገብር ኣለኒ?", "translation": "My ATM card was swallowed, what should I do?"},
            ],
            "som": [
                {"text": "Ma ku wareejin karaa Telebirr ama CBE Birr?", "translation": "Can I transfer via Telebirr or CBE Birr?"},
                {"text": "Waxaan rabaa inaan lacag ku shubo akoonkayga.", "translation": "I want to deposit money into my account."},
                {"text": "Fadlan ii xaqiiji haraaga xisaabtayda.", "translation": "Please verify my account balance."},
                {"text": "Kaarkaygii ATM-ka ayaa mishiinku liqay, maxaan sameeyaa?", "translation": "My ATM card was captured, what should I do?"},
            ],
        },
        IntentType.EDUCATION: {
            "amh": [
                {"text": "የኦፊሴላዊ ትራንስክሪፕት ጥያቄ ማመልከቻ እፈልጋለሁ", "translation": "I would like to apply for an official transcript."},
                {"text": "የትምህርት ክፍያ በባንክ ተከፍሏል", "translation": "The tuition fee has been paid via the bank."},
                {"text": "የፈተና ፕሮግራም የት ይለጠፋል?", "translation": "Where will the examination schedule be posted?"},
                {"text": "የዶርም ምደባዬን ማወቅ እፈልጋለሁ", "translation": "I need to check my dormitory room assignment."},
            ],
            "eng": [
                {"text": "I would like to apply for an official transcript.", "translation": "የኦፊሴላዊ ትራንስክሪፕት ጥያቄ ማመልከቻ እፈልጋለሁ።"},
                {"text": "The tuition fee has been paid via the bank.", "translation": "የትምህርት ክፍያ በባንክ ተከፍሏል።"},
                {"text": "Where will the examination schedule be posted?", "translation": "የፈተና ፕሮግራም የት ይለጠፋል?"},
                {"text": "I need to check my dormitory room assignment.", "translation": "የዶርም ምደባዬን ማወቅ እፈልጋለሁ።"},
            ],
            "orm": [
                {"text": "Iyyannoo tiraanskiriiptii ifaa nan barbaada.", "translation": "I want an official transcript application."},
                {"text": "Kaffaltiin barumsaa baankiin kaffalameera.", "translation": "Tuition fee was paid through the bank."},
                {"text": "Sagantaan qormaataa eessatti maxxanfama?", "translation": "Where is the exam schedule posted?"},
                {"text": "Ramaddii doormii kootii beekuu nan barbaada.", "translation": "I want to know my dorm assignment."},
            ],
            "tir": [
                {"text": "ናይ ወግዓዊ ትራንስክሪፕት ሕቶ መመልከቲ እደሊ ኣለኹ።", "translation": "I want an official transcript application."},
                {"text": "ክፍሊት ትምህርቲ ብባንኪ ተኸፊሉ እዩ።", "translation": "Tuition fee was paid through the bank."},
                {"text": "ናይ ፈተና መደብ ኣበይ ይልጠፍ?", "translation": "Where is the exam schedule posted?"},
                {"text": "ናይ ዶርም ምደባይ ክፈልጥ እደሊ ኣለኹ።", "translation": "I want to know my dorm assignment."},
            ],
            "som": [
                {"text": "Waxaan rabaa codsiga rasmiga ah ee shahaadada natiijooyinka (transcript).", "translation": "I want an official transcript application."},
                {"text": "Lacagtii waxbarashada waxaa lagu bixiyay bangiga.", "translation": "Tuition fee was paid through the bank."},
                {"text": "Jadwalka imtixaanka xaggee lagu dhajiyaa?", "translation": "Where is the exam schedule posted?"},
                {"text": "Waxaan rabaa inaan ogaado qolka hoygayga jaamacadda.", "translation": "I want to know my dorm room assignment."},
            ],
        },
        IntentType.LEGAL_POLICE: {
            "amh": [
                {"text": "የስርቆት አቤቱታ ማስመዝገብ እፈልጋለሁ", "translation": "I would like to file a formal theft complaint."},
                {"text": "በደረሰብኝ ጥቃት ላይ ቃል መስጠት እፈልጋለሁ", "translation": "I want to give an official statement regarding an assault."},
                {"text": "መርማሪ ፖሊስ ማነጋገር እችላለሁ?", "translation": "Can I speak directly with the investigating officer?"},
                {"text": "የክስ መዝገብ ቁጥሬ ስንት ነው?", "translation": "What is my official case file number?"},
            ],
            "eng": [
                {"text": "I would like to file a formal theft complaint.", "translation": "የስርቆት አቤቱታ ማስመዝገብ እፈልጋለሁ።"},
                {"text": "I want to give an official statement regarding an assault.", "translation": "በደረሰብኝ ጥቃት ላይ ቃል መስጠት እፈልጋለሁ።"},
                {"text": "Can I speak directly with the investigating officer?", "translation": "መርማሪ ፖሊስ ማነጋገር እችላለሁ?"},
                {"text": "What is my official case file number?", "translation": "የክስ መዝገብ ቁጥሬ ስንት ነው?"},
            ],
            "orm": [
                {"text": "Iyyannoo yakkasaa hanna galmeessisuun barbaada.", "translation": "I want to register a theft complaint."},
                {"text": "Haleellaa na irratti raawwatameef ibsa kennuun barbaada.", "translation": "I want to give a statement on an assault."},
                {"text": "Poolisii qorataa qunnamuu danda'aa?", "translation": "Can I contact the investigator?"},
                {"text": "Lakkofsi galmee himannaa kootii meeqa?", "translation": "What is my case file number?"},
            ],
            "tir": [
                {"text": "ናይ ስርቂ ጥርዓን ከምዝግብ እደሊ ኣለኹ።", "translation": "I want to register a theft complaint."},
                {"text": "ኣብ ልዕለይ ብዝበጽሐ መጥቃዕቲ ቃል ክህብ እደሊ ኣለኹ።", "translation": "I want to give a statement on an assault."},
                {"text": "መርማሪ ፖሊስ ክረክብ እኽእልዶ?", "translation": "Can I speak with the investigator?"},
                {"text": "ናይ ክሰይ መዝገብ ቍጽሪ ክንዲ ምንታይ እዩ?", "translation": "What is my case file number?"},
            ],
            "som": [
                {"text": "Waxaan rabaa inaan diiwaangeliyo cabasho xatooyo.", "translation": "I want to register a theft complaint."},
                {"text": "Waxaan rabaa inaan bixiyo markhaatiga weerar laygu qaaday.", "translation": "I want to give a statement on an assault."},
                {"text": "Ma la hadli karaa sarkaal baare boolis ah?", "translation": "Can I speak with the police investigator?"},
                {"text": "Waa imisa lambarka diiwaanka dacwaddayda?", "translation": "What is my case file number?"},
            ],
        },
        IntentType.GENERAL: {
            "amh": [
                {"text": "እሺ አመሰግናለሁ", "translation": "Okay, thank you."},
                {"text": "አልገባኝም፣ በድጋሚ ንገረኝ", "translation": "I didn't understand, please repeat."},
                {"text": "አዎ እፈልጋለሁ", "translation": "Yes, I would like that."},
            ],
            "eng": [
                {"text": "Okay, thank you very much.", "translation": "እሺ፣ በጣም አመሰግናለሁ።"},
                {"text": "Could you please repeat that?", "translation": "እባክህ ልትደግምልኝ ትችላለህ?"},
                {"text": "Understood, sounds good!", "translation": "ገብቶኛል፣ ጥሩ ነው!"},
            ],
            "orm": [
                {"text": "Tole, galatoomi.", "translation": "Okay, thank you."},
                {"text": "Naaf hin galle, naaf irra deebi'i.", "translation": "I didn't understand, please repeat."},
                {"text": "Eyyee nan barbaada.", "translation": "Yes, I want that."},
            ],
            "tir": [
                {"text": "ሕራይ የቐንየለይ።", "translation": "Okay, thank you."},
                {"text": "ኣይተረድኣንን፣ ደጊምካ ንገረኒ።", "translation": "I didn't understand, please repeat."},
                {"text": "እወ እደሊ ኣለኹ።", "translation": "Yes, I want that."},
            ],
            "som": [
                {"text": "Haye, mahadsanid.", "translation": "Okay, thank you."},
                {"text": "Ma fahmin, fadlan ku celi.", "translation": "I didn't understand, please repeat."},
                {"text": "Haa waan rabaa.", "translation": "Yes, I want that."},
            ],
        },
    }

    @classmethod
    def get_suggestions(cls, intent: IntentType, tgt_lang: str) -> list[dict[str, str]]:
        """Return 3 smart quick-reply suggestion chips for the target speaker."""
        lang_key = "eng"
        if tgt_lang in ("amh", "amh_Ethi"):
            lang_key = "amh"
        elif tgt_lang in ("orm", "gaz_Latn"):
            lang_key = "orm"
        elif tgt_lang in ("tir", "tir_Ethi"):
            lang_key = "tir"
        elif tgt_lang in ("som", "som_Latn"):
            lang_key = "som"

        intent_map = cls.SUGGESTIONS_MAP.get(intent, cls.SUGGESTIONS_MAP[IntentType.GENERAL])
        return intent_map.get(lang_key, intent_map["eng"])


# ──────────────────────────────────────────────────────────────────
# 6. Unified Smart Translation Agent
# ──────────────────────────────────────────────────────────────────
@dataclass
class SmartTranslationResult:
    source_text: str
    translated_text: str
    src_lang: str
    tgt_lang: str
    intent: IntentType
    formality: str
    suggested_replies: list[dict[str, str]]
    was_idiom_match: bool = False
    context_resolved: bool = False
    confidence: float = 0.90
    is_tm_match: bool = False
    entities_preserved: list[str] = field(default_factory=list)
    warning: str | None = None


class SmartEngine:
    """Orchestrates multi-turn context, intent reasoning, idioms, and quick-replies."""

    @classmethod
    def process_and_translate(
        cls,
        text: str,
        src_lang: str,
        tgt_lang: str,
        session_id: str | None = None,
        formality: str = "auto",
        nmt_translator_func: Any = None,
    ) -> SmartTranslationResult:
        if not text or not text.strip():
            return SmartTranslationResult(
                source_text="",
                translated_text="",
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                intent=IntentType.GENERAL,
                formality=formality,
                suggested_replies=[],
            )

        raw_input = text.strip()
        try:
            from ai_pipeline.speech_repair import repair_stt_transcription
            raw_input = repair_stt_transcription(raw_input, src_lang)
        except Exception:
            pass

        # Step 1: Contextual Ellipsis Resolution
        context_resolved_text = SmartContextManager.resolve_contextual_ellipsis(
            raw_input, src_lang, session_id
        )
        was_context_resolved = context_resolved_text != raw_input

        # Step 2: Intent Classification
        intent = IntentClassifier.classify(context_resolved_text)

        # Step 3: Cultural Idiom De-literalization Check
        translated = CulturalIdiomEngine.match_cultural_idiom(context_resolved_text, src_lang, tgt_lang)
        was_idiom = translated is not None

        confidence = 0.98 if was_idiom else 0.85
        is_tm_match = was_idiom
        entities_preserved: list[str] = []
        warning: str | None = None

        # Step 4: If not an idiom, execute pipeline translation with guard evaluation
        if not translated:
            if nmt_translator_func is not None:
                trans_res = nmt_translator_func(context_resolved_text, src_lang, tgt_lang)
                if isinstance(trans_res, dict):
                    translated = trans_res.get("translated_text", "")
                    confidence = trans_res.get("confidence", 0.85)
                    is_tm_match = trans_res.get("is_tm_match", False)
                    entities_preserved = trans_res.get("entities_preserved", [])
                    warning = trans_res.get("warning", None)
                elif isinstance(trans_res, tuple) and len(trans_res) >= 2:
                    translated = trans_res[0]
                    guard_info = trans_res[1]
                    if hasattr(guard_info, "confidence"):
                        confidence = guard_info.confidence
                        is_tm_match = guard_info.is_tm_hit
                        warning = guard_info.warning
                    if len(trans_res) >= 3 and isinstance(trans_res[2], list):
                        entities_preserved = trans_res[2]
                else:
                    translated = str(trans_res)
                    try:
                        from ai_pipeline.hallucination_guard import HallucinationGuard
                        guard_res = HallucinationGuard.evaluate(
                            context_resolved_text, translated, src_lang, tgt_lang
                        )
                        confidence = guard_res.confidence
                        is_tm_match = guard_res.is_tm_hit
                        warning = guard_res.warning
                        translated = guard_res.clean_translation
                    except Exception:
                        pass
            else:
                from ai_pipeline.pipeline import TranslatorPipeline
                translated = context_resolved_text

        # Step 5: Formality / Register Adjustment
        translated = FormalityController.apply_formality(translated, tgt_lang, formality)

        # Step 6: Generate Smart Follow-Up Suggestions for the interlocutor
        suggested_replies = SmartSuggestionsEngine.get_suggestions(intent, tgt_lang)

        # Step 7: Record Turn in Context History
        if session_id:
            SmartContextManager.add_turn(
                session_id=session_id,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                source_text=raw_input,
                translated_text=translated,
                intent=intent,
            )

        return SmartTranslationResult(
            source_text=context_resolved_text,
            translated_text=translated,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            intent=intent,
            formality=formality,
            suggested_replies=suggested_replies,
            was_idiom_match=was_idiom,
            context_resolved=was_context_resolved,
            confidence=round(confidence, 2),
            is_tm_match=is_tm_match,
            entities_preserved=entities_preserved,
            warning=warning,
        )
