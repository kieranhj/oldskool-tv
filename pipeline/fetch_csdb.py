"""Fetch CSDb releases for shortlisted C64 prods (1 request per second) and cache the raw XML.

    python pipeline/fetch_csdb.py

Cache: data/cache/csdb/<release id>.xml. Already-cached releases are not refetched.
parse() turns a cached release into {rating, comments: [{user, date, text}]}.
"""
import re, html, time, urllib.request, xml.etree.ElementTree as ET
from common import CACHE, WORK, UA, read_jsonl

DIR = CACHE / "csdb"


def fix_cp1252(text):
    """CSDb serves some comments with Windows-1252 punctuation that arrives as C1 control characters ( for ’)."""
    return re.sub("[-]", lambda m: bytes([ord(m.group())]).decode("cp1252", errors="ignore"), text)


def parse(release_id):
    path = DIR / f"{release_id}.xml"
    if not path.exists():
        return None
    rel = ET.parse(path).getroot().find("Release")
    if rel is None:
        return None
    comments = []
    for grp in rel.findall("Comments"):
        for c in grp.findall("UserComment"):
            user = c.find("CSDbUser")
            comments.append(dict(user=(user.findtext("Handle") or user.findtext("Login")) if user is not None else None,
                                 date=c.findtext("Date"), text=fix_cp1252(html.unescape(c.findtext("Text") or "")).strip()))
    return dict(rating=rel.findtext("Rating"), comments=comments)


def main():
    DIR.mkdir(parents=True, exist_ok=True)
    todo = [c["csdb"] for c in read_jsonl(WORK / "catalog.jsonl")
            if c["shortlist"] and c["csdb"] and not (DIR / f"{c['csdb']}.xml").exists()]
    print(f"fetching {len(todo)} CSDb releases")
    for rid in todo:
        url = f"https://csdb.dk/webservice/?type=release&id={rid}"
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            (DIR / f"{rid}.xml").write_bytes(data)
        except Exception as e:
            print("error", rid, e)
        time.sleep(1)
    print("done")


if __name__ == "__main__":
    main()
