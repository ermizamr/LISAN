import urllib.request
import re

urls = [
    "https://www.pinterest.com/pin/698480223505074275/",
    "https://www.pinterest.com/pin/25262447904041402/",
    "https://www.pinterest.com/pin/674554850473849382/"
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

for u in urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            m_img = re.search(r'<meta property="og:image" content="([^"]+)"', content)
            m_desc = re.search(r'<meta property="og:description" content="([^"]+)"', content)
            print("URL:", u)
            print("  Image:", m_img.group(1) if m_img else "None")
            print("  Desc:", m_desc.group(1) if m_desc else "None")
    except Exception as e:
        print("Error:", u, e)
