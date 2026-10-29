import importlib.util, json, re, sys, ssl, urllib.parse, html
from pathlib import Path
ROOT = Path(r"E:/qoder工作区/rf-sonne.com/generatepress-child")
spec = importlib.util.spec_from_file_location("bs", ROOT / "bak/qa/blog_setup.py")
bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)

OUT = ROOT / "bak/2026-10-29-audit"
OUT.mkdir(parents=True, exist_ok=True)

try:
    bs.establish_bypass()
    print("bypass cookie set")
except Exception as e:
    print("bypass failed:", e)
st, _, body = bs.request("https://rf-sonne.com/robots.txt")
print("robots status", st, "len", len(body), "preview:", body[:80])

# sitemaps
urls = []
for sm in ["post-sitemap.xml", "page-sitemap.xml"]:
    st, _, b = bs.request(f"https://rf-sonne.com/{sm}")
    txt = b.decode("utf-8", "ignore")
    urls += re.findall(r"<loc>(.*?)</loc>", txt)
    print(sm, st, len(urls))
urls = [u.replace("&amp;", "&") for u in urls]

def strip(t):
    t = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<!--.*?-->", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()

def one(rx, t, flags=re.S | re.I):
    m = re.search(rx, t, flags)
    return m.group(1).strip() if m else ""

pages = {}
for u in urls:
    st, hdr, b = bs.request(u)
    t = b.decode("utf-8", "ignore")
    rec = {"url": u, "status": st, "bytes": len(b)}
    rec["title"] = html.unescape(one(r"<title[^>]*>(.*?)</title>", t))
    rec["desc"] = html.unescape(one(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', t)) or \
                  html.unescape(one(r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']', t))
    rec["robots"] = one(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'](.*?)["\']', t)
    rec["canonical"] = one(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\'](.*?)["\']', t)
    rec["ogtitle"] = one(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', t)
    rec["lang"] = one(r"<html[^>]+lang=[\"']([^\"']+)", t)
    # scope body to article/entry if possible
    m = re.search(r"(?is)<(article|main)[^>]*>(.*?)</\1>", t)
    main = m.group(2) if m else t
    rec["h1"] = [strip(x) for x in re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", main)]
    rec["h2"] = [strip(x) for x in re.findall(r"(?is)<h2[^>]*>(.*?)</h2>", main)]
    rec["h3"] = [strip(x) for x in re.findall(r"(?is)<h3[^>]*>(.*?)</h3>", main)]
    rec["words"] = len(strip(main).split())
    rec["full_words"] = len(strip(t).split())
    # jsonld
    lds = re.findall(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', t)
    types = []
    for ld in lds:
        try:
            d = json.loads(ld.strip())
        except Exception:
            types.append("PARSE_ERROR"); continue
        stack = d if isinstance(d, list) else [d]
        for s in stack:
            if isinstance(s, dict):
                if "@graph" in s:
                    stack += s["@graph"]
                tv = s.get("@type")
                if isinstance(tv, list): types += tv
                elif tv: types.append(tv)
    rec["schema"] = sorted(set(types))
    # faq detection
    rec["faqpage"] = any("FAQPage" in s for s in rec["schema"])
    rec["details"] = len(re.findall(r"(?is)<details", main))
    # emails / dates / author
    rec["author"] = one(r'(?is)class=["\'][^"\']*author[^"\']*["\'][^>]*>(.*?)<', main)
    rec["dates"] = re.findall(r'(?i)(?:datetime=["\']([^"\']+)|(?:Published|Updated)[^<]{0,40}?(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}))', t)[:6]
    # links
    links = []
    for attrs, label in re.findall(r'(?is)<a\s+([^>]*?)>(.*?)</a>', t):
        hm = re.search(r'href=["\']([^"\']+)["\']', attrs)
        if not hm: continue
        h = html.unescape(hm.group(1))
        links.append({"href": h, "text": strip(label)[:120], "cls": one(r'class=["\']([^"\']*)', attrs)})
    rec["links"] = links
    pages[u] = rec
    print(st, len(str(rec["words"])), u, "|", rec["title"][:60])

(OUT / "pages.json").write_text(json.dumps(pages, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved", len(pages))
