"""Check shortlisted prods' YouTube videos with the public oEmbed endpoint (no API key) and cache the results.

    python pipeline/check_videos.py

Cache: data/cache/oembed.json  {video_id: {"ok": bool, "status": int, "title": ..., "channel": ...}}
Videos are tried in catalogue order (ids both sites agree on first) until one works.
"""
import json, time, urllib.error, urllib.request
from common import CACHE, WORK, UA, read_jsonl

PATH = CACHE / "oembed.json"


def check(vid):
    url = f"https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={vid}"
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20))
        return dict(ok=True, status=200, title=j.get("title"), channel=j.get("author_name"))
    except urllib.error.HTTPError as e:
        return dict(ok=False, status=e.code)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = json.loads(PATH.read_text(encoding="utf8")) if PATH.exists() else {}
    dead = none_ok = 0
    for c in read_jsonl(WORK / "catalog.jsonl"):
        if not c["shortlist"]:
            continue
        for vid in c["videos"]:
            if vid not in cache:
                cache[vid] = check(vid)
                time.sleep(0.3)
            if cache[vid]["ok"]:
                break
            dead += 1
        else:
            none_ok += 1
            print("no working video:", c["id"], c["title"])
    PATH.write_text(json.dumps(cache, indent=0, ensure_ascii=False), encoding="utf8")
    print(f"checked {len(cache)} videos; {dead} dead links skipped; {none_ok} prods with no working video")


if __name__ == "__main__":
    main()
