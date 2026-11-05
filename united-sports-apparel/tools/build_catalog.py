#!/usr/bin/env python3
"""Refresh the product data embedded in ../index.html from the live Shopify store.

Usage:  python3 tools/build_catalog.py            (fetches unitedsportsonline.com)
        python3 tools/build_catalog.py DATA_DIR   (reads saved JSON files instead)

The shop section renders from the JSON between the CATALOG markers in index.html.
Berrien County Parks staff items are left out of the public shop on purpose;
they are linked from the staff-stores section.
"""
import json
import pathlib
import re
import sys
import urllib.request

STORE = "https://unitedsportsonline.com"
FEEDS = {
    "all": "/products.json?limit=250",
    "frontpage": "/collections/frontpage/products.json?limit=250",
    "apparel": "/collections/apparel/products.json?limit=250",
    "bcp-maint": "/collections/berrien-county-parks-maintenance/products.json?limit=250",
    "bcp-mgr": "/collections/berrien-county-parks-managers/products.json?limit=250",
    "bcp": "/collections/berrien-county-parks/products.json?limit=250",
}
ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

CATS = {
    "gameday": r"football|soccer|basketball|\busa\b|face mask|game day|match day|bears|lancers|shamrocks",
    "tees": r"\bt[- ]?shirt|\btee\b|tank",
    "sweats": r"sweatshirt|hoodie|crewneck",
    "holiday": r"halloween|thanksgiving|father|mother|\bmom\b|\bmama\b|\bdad|grandpa|grill|4th of july|memorial day|spider|ghost|treat",
    "gifts": r"\bmug\b|candle|tote|sticker|apron|face mask",
}


def load(name, data_dir):
    if data_dir:
        return json.load(open(pathlib.Path(data_dir) / name))["products"]
    req = urllib.request.Request(STORE + FEEDS[name], headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))["products"]


def clean_title(t):
    t = t.replace("‑", "-")
    m = re.match(r'^T-Shirt\s*[—-]\s*"([^"]+)"', t)
    if m:
        t = re.sub(r"\s+", " ", m.group(1)).strip() + " T-Shirt"
    else:
        t = re.split(r"\s+[|—]\s+|,\s", t)[0].strip()
    t = re.sub(r"\bT Shirts?\b", "T-Shirt", t)
    t = re.sub(r"\bt-shirt\b", "T-Shirt", t)
    if t.islower() or t[0].isupper() and t[1:].islower():
        t = t[0].upper() + t[1:]
    return t.replace("I'm just here for the food funny T-Shirt", "I'm Just Here for the Food Funny T-Shirt")


def money(x):
    return ("%.2f" % x).rstrip("0").rstrip(".") if x == int(x) else "%.2f" % x


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else None
    allp = load("all", data_dir)
    order = [p["handle"] for p in load("frontpage", data_dir)] + [p["handle"] for p in load("apparel", data_dir)]
    staff = {p["handle"] for f in ("bcp-maint", "bcp-mgr", "bcp") for p in load(f, data_dir)}
    rank = {h: i for i, h in enumerate(dict.fromkeys(order))}

    items = []
    for i, p in enumerate(allp):
        if p["handle"] in staff or not p["images"]:
            continue
        if not any(v.get("available", True) for v in p["variants"]):
            continue
        prices = sorted({float(v["price"]) for v in p["variants"]})
        hay = " ".join([p["title"], p.get("product_type") or "", " ".join(p.get("tags") or [])]).lower()
        cats = [c for c, rx in CATS.items() if re.search(rx, hay)]
        imgs = [im["src"] for im in p["images"][:2]]
        items.append({
            "t": clean_title(p["title"]),
            "h": p["handle"],
            "p": money(prices[0]),
            "from": len(prices) > 1,
            "i": imgs,
            "c": cats,
            "_r": rank.get(p["handle"], 1000 + i),
        })
    items.sort(key=lambda x: x["_r"])
    for x in items:
        del x["_r"]

    blob = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = INDEX.read_text(encoding="utf-8")
    new, n = re.subn(
        r"(<script id=\"catalog\" type=\"application/json\">).*?(</script>)",
        lambda m: m.group(1) + blob + m.group(2),
        html,
        flags=re.S,
    )
    if n != 1:
        sys.exit("catalog script tag not found in index.html")
    INDEX.write_text(new, encoding="utf-8")
    print(f"wrote {len(items)} products to {INDEX}")


if __name__ == "__main__":
    main()
