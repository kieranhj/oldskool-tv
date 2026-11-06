"""Check a random sample of YouTube ids with the public oEmbed endpoint (no key). Usage: python yt_alive.py pouet8.jsonl n"""
import json, sys, random, time, urllib.request, urllib.error, collections
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf8")]
random.seed(1); s = random.sample(rows, int(sys.argv[2]))
res = collections.Counter(); chans = collections.Counter()
for r in s:
    vid = r["youtube"][0]
    try:
        j = json.load(urllib.request.urlopen(f"https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={vid}", timeout=20))
        res["ok"] += 1; chans[j.get("author_name")] += 1
    except urllib.error.HTTPError as e:
        res[f"http {e.code}"] += 1
    time.sleep(0.3)
print(dict(res)); print("top channels:", chans.most_common(15))
