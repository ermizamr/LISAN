import json
import urllib.request

def post(text, src="amh", tgt="eng"):
    req = urllib.request.Request(
        "http://127.0.0.1:8000/translate/text",
        data=json.dumps({"text": text, "src": src, "tgt": tgt}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read())

cases = [
    ("ሰላም እንዴት ነው", "amh", "eng"),
    ("ሳላም", "amh", "eng"),
    ("ሆስፒታል የት", "amh", "eng"),
    ("ሰላም ሰላም እንዴት ነህ ሀ ሀ", "amh", "eng"),
    ("ወደ ኢትዮጵያ መትታቃለህ በሆነ አጋጣሚ መተልታቅ ትችላለህ", "amh", "eng"),
    ("ውሃ መጠጣት እፈልጋለሁ", "amh", "eng"),
    ("akkam jirtu", "orm", "eng"),
    ("ከመይ ኣለኻ", "tir", "eng"),
    ("iska warran", "som", "eng"),
]

print("=" * 60)
print("Testing Live HTTP Server Translation (/translate/text)")
print("=" * 60)
for text, src, tgt in cases:
    res = post(text, src, tgt)
    print(f"[{src}->{tgt}] '{text}'\n  ==> '{res['translated_text']}' ({res['latency_seconds']}s)\n")
