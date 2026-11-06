"""Write cards and topic labels with the Claude Message Batches API: one request per prod, both outputs at once.

    pip install anthropic                     # the only non-standard-library dependency in the pipeline
    python pipeline/make_card_inputs.py       # fact sheets for prods without a card
    python pipeline/write_with_api.py submit [--limit 50] [--model claude-opus-5-5] [--effort medium]
    python pipeline/write_with_api.py collect [BATCH_ID]   # waits for the batch, then writes the files
    python pipeline/validate_cards.py --merge && python pipeline/label_topics.py check

Each request gets CARD_SPEC.md and TOPICS.md as the (cached) system prompt, then the prod's three YouTube stills
(by URL) and its fact sheet. The reply is JSON constrained by a schema. Results go to the same files the subagents
wrote in the spike: data/cards/batch_NN.cards.jsonl and data/cards/topics_NN.jsonl, NN matching the input batch.
Prods that already have a card are never resubmitted, so `submit` after a partial run picks up only what's missing.
"""
import argparse, json, sys, time
from common import CARDS, ROOT, WORK, read_jsonl

PIPE = ROOT / "pipeline"
LOG = WORK / "api_batches.jsonl"
# $ per million tokens, standard rates; the Batches API charges half. Cache reads are 0.1x input.
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50)}

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "why": {"type": "string"},
        "highlights": {"type": "array", "items": {"type": "string"}},
        "quote": {"anyOf": [{"type": "null"}, {
            "type": "object",
            "properties": {"text": {"type": "string"}, "user": {"type": ["string", "null"]}, "date": {"type": "string"}},
            "required": ["text", "user", "date"], "additionalProperties": False}]},
        "basis": {"type": "string", "enum": ["comments", "facts", "facts+knowledge"]},
        "topics": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "string", "enum": ["3d", "effects", "pixel-art", "text-mode"]},
                           "evidence": {"type": "array", "items": {"type": "string"}}},
            "required": ["id", "evidence"], "additionalProperties": False}},
        "expanded": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "why", "highlights", "quote", "basis", "topics", "expanded"],
    "additionalProperties": False,
}


def client():
    """The SDK reads ANTHROPIC_API_KEY. On Windows a key saved with `setx` only reaches processes started after it,
    so fall back to the user's saved environment rather than making them restart their terminal."""
    import os, anthropic
    if not os.environ.get("ANTHROPIC_API_KEY") and sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                os.environ["ANTHROPIC_API_KEY"] = winreg.QueryValueEx(k, "ANTHROPIC_API_KEY")[0]
        except OSError:
            pass
    return anthropic.Anthropic()


def system_prompt():
    card = (PIPE / "CARD_SPEC.md").read_text(encoding="utf8")
    topics = (PIPE / "TOPICS.md").read_text(encoding="utf8").split("## Labelling")[0]
    return f"""You write the short write-ups and topic labels for Oldskool TV, a site of 8-bit demoscene videos worth
watching. For each prod you get three stills that YouTube took about 25%, 50% and 75% of the way through its video,
then its fact sheet as JSON. Reply with one JSON object holding both the card and the topic labels.

The card follows this spec. Ignore its "Output" file layout; the reply schema replaces it.

{card}

The topics follow this taxonomy. `tiny` is set in code from the prod type, so never return it. `tag_topics` in the
fact sheet are also applied in code; return them too if they hold. Cite frames as `frame:1`..`frame:3`, comments
as `comment:<user> <date>`, tags as `tag:<name>`, and `title`, `notes` or `knowledge` otherwise.

{topics}"""


def pending_sheets():
    done = {c["id"] for f in CARDS.glob("batch_*.cards.jsonl") for c in read_jsonl(f)}
    for f in sorted((WORK / "card_inputs").glob("batch_*.jsonl")):
        for s in read_jsonl(f):
            if s["id"] not in done:
                yield f.name[6:8], s


def stills(vid):
    """The stills YouTube actually has: a request whose image URL won't download fails outright."""
    import urllib.error, urllib.request
    from common import UA
    ok = []
    for n in (1, 2, 3):
        url = f"https://i.ytimg.com/vi/{vid}/hq{n}.jpg"
        try:
            urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=15)
            ok.append(url)
        except (urllib.error.URLError, TimeoutError):
            pass
    return ok


def request(s, model, effort, system):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    from label_topics import EXPANDED_TAGS, TAG_RULES
    sheet = dict(s, tag_topics=sorted({TAG_RULES[t] for t in s["tags"] if t in TAG_RULES}),
                 tag_expanded=sorted({EXPANDED_TAGS[t] for t in s["tags"] if t in EXPANDED_TAGS}))
    content = [{"type": "image", "source": {"type": "url", "url": u}} for u in stills(s["video"])]
    if len(content) < 3:
        sheet["stills_missing"] = "YouTube has no stills for some or all of this video; judge from the facts."
    content.append({"type": "text", "text": "Fact sheet:\n" + json.dumps(sheet, ensure_ascii=False, indent=1)})
    return Request(custom_id=s["id"], params=MessageCreateParamsNonStreaming(
        model=model, max_tokens=16000,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": content}]))


def submit(args):
    todo = list(pending_sheets())[:args.limit or None]
    if not todo:
        print("nothing to write: every fact sheet has a card (run make_card_inputs.py after growing the shortlist)")
        return
    system = system_prompt()
    batch = client().messages.batches.create(
        requests=[request(s, args.model, args.effort, system) for _, s in todo])
    with open(LOG, "a", encoding="utf8") as f:
        f.write(json.dumps(dict(id=batch.id, model=args.model, effort=args.effort, n=len(todo),
                                files={s["id"]: nn for nn, s in todo}, created=time.strftime("%Y-%m-%d %H:%M"))) + "\n")
    print(f"submitted {batch.id}: {len(todo)} prods with {args.model} at {args.effort} effort")


def write_merged(path, rows_by_id, order):
    old = {r["id"]: r for r in read_jsonl(path)} if path.exists() else {}
    old.update(rows_by_id)
    with open(path, "w", encoding="utf8") as f:
        for i in order:
            if i in old:
                f.write(json.dumps(old[i], ensure_ascii=False) + "\n")


def collect(args):
    api = client()
    log = read_jsonl(LOG)
    entry = next(e for e in reversed(log) if e["id"] == args.batch_id) if args.batch_id else log[-1]
    while (b := api.messages.batches.retrieve(entry["id"])).processing_status != "ended":
        c = b.request_counts
        print(f"{entry['id']}: {b.processing_status}, {c.processing} processing, {c.succeeded} done")
        time.sleep(60)
    cards, topics, failed = {}, {}, []
    tok = dict(input=0, cache_read=0, cache_write=0, output=0)
    for r in api.messages.batches.results(entry["id"]):
        res = r.result
        if res.type != "succeeded":
            failed.append(f"{r.custom_id}: {res.type}")
            continue
        m = res.message
        u = m.usage
        tok["input"] += u.input_tokens
        tok["cache_read"] += u.cache_read_input_tokens or 0
        tok["cache_write"] += u.cache_creation_input_tokens or 0
        tok["output"] += u.output_tokens
        if m.stop_reason != "end_turn":
            failed.append(f"{r.custom_id}: stop_reason {m.stop_reason}")
            continue
        out = json.loads(next(b.text for b in m.content if b.type == "text"))
        cards[r.custom_id] = dict(id=r.custom_id, **{k: out[k] for k in ("summary", "why", "highlights", "quote", "basis")})
        topics[r.custom_id] = dict(id=r.custom_id, topics=out["topics"], expanded=out["expanded"])
    for nn in sorted(set(entry["files"].values())):
        order = [s["id"] for s in read_jsonl(WORK / "card_inputs" / f"batch_{nn}.jsonl")]
        mine = [i for i, n in entry["files"].items() if n == nn]
        write_merged(CARDS / f"batch_{nn}.cards.jsonl", {i: cards[i] for i in mine if i in cards}, order)
        write_merged(CARDS / f"topics_{nn}.jsonl", {i: topics[i] for i in mine if i in topics}, order)
    pin, pout = PRICES.get(entry["model"], (0, 0))
    cost = 0.5 * (tok["input"] * pin + tok["cache_write"] * pin * 1.25 + tok["cache_read"] * pin * 0.1
                  + tok["output"] * pout) / 1e6
    print(f"{len(cards)} written, {len(failed)} failed; tokens {tok}; about ${cost:.2f} "
          f"(${cost / max(1, len(cards)):.4f} a prod)")
    for f in failed:
        print("  ", f)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("submit")
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--model", default="claude-opus-5-5")
    s.add_argument("--effort", default="medium", choices=["low", "medium", "high"])
    c = sub.add_parser("collect")
    c.add_argument("batch_id", nargs="?")
    args = ap.parse_args()
    {"submit": submit, "collect": collect}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
