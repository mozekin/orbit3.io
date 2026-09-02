#!/usr/bin/env python3
"""Submit orbit3.io URLs to IndexNow (Bing, Yandex, Naver, Seznam and other participating engines).
Run from the repo root after deploying a change:  python3 tools/indexnow.py [url ...]
With no arguments it submits every URL in sitemap.xml. The key file 923d2d5c7aaa7b3a42d87b965aba122c.txt must be live at the site root."""
import json, re, sys, urllib.request

SITE = "https://orbit3.io"
KEY = "923d2d5c7aaa7b3a42d87b965aba122c"

def main(argv):
    urls = argv[1:] or re.findall(r"<loc>(.*?)</loc>", open("sitemap.xml", encoding="utf-8").read())
    body = json.dumps({"host": "orbit3.io", "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow HTTP {r.status}: submitted {len(urls)} URL(s)")
    except urllib.error.HTTPError as e:
        print(f"IndexNow HTTP {e.code}: {e.read().decode(errors='replace')}")
        return 1
    for u in urls: print(" ", u)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
