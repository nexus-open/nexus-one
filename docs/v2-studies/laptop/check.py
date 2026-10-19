#!/usr/bin/env python3
"""Static sanity check for nexus_os_desktop.html.
1. Every element id referenced from JS (getElementById / $('...')) must exist as id="...".
2. No external references: no http:// or https:// anywhere in the file.
Static only - this does NOT execute the page in a browser.
Prints PASS or FAIL. Exit code 0 on PASS, 1 on FAIL.
"""
import re, sys
from html.parser import HTMLParser
from pathlib import Path

path = Path(__file__).with_name("nexus_os_desktop.html")
src = path.read_text(encoding="utf-8")

class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.defined = set()
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id" and v:
                self.defined.add(v)

p = Ids()
p.feed(src)

# JS id references: getElementById('x') / getElementById("x") / $('x') / $("x")
refs = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)", src))
refs |= set(re.findall(r"\$\(\s*['\"]([^'\"]+)['\"]\s*\)", src))

missing = sorted(refs - p.defined)
ext = [m for m in re.findall(r"https?://[^\s\"'<>]+", src, re.I)]

ok = True
if missing:
    ok = False
    print("FAIL: JS references ids that do not exist:", missing)
else:
    print(f"OK: all {len(refs)} JS-referenced ids exist in the HTML.")
if ext:
    ok = False
    print("FAIL: external references found:", ext)
else:
    print("OK: no http/https external references.")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
