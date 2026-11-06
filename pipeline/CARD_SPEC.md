# Card spec

A card is the short write-up shown with each video on Oldskool TV. One card per prod, written from that prod's
fact sheet (`data/work/card_inputs/batch_NN.jsonl`). The same spec is the prompt for an API-based writer later.

## Output

One JSON object per line, in the same order as the input, written to `data/cards/batch_NN.cards.jsonl`:

```json
{"id": "dz6309",
 "summary": "Booze Design's three-disk-side C64 demo that won the C64 demo compo at X 2008: an unbroken run of parts joined by seamless transitions.",
 "why": "Still the yardstick for C64 demo design. Sceners describe it as growing on them with every watch as they notice how much is happening while it loads.",
 "highlights": ["seamless transitions", "Dane's soundtrack", "no loading pauses"],
 "topics": ["Technical showpiece", "Design & storytelling"],
 "quote": {"text": "Now, after having watched it countless times, I can safely say that I am blown away.", "user": "Stone", "date": "04.01.2012"},
 "basis": "comments"}
```

- **summary**: 1–2 sentences, at most 45 words. What it is and what you'll see: who made it, platform, kind
  of prod, and where it competed if it did.
- **why**: 1–2 sentences, at most 45 words. Why it's worth watching or what its standing in the scene is. With
  comments, say what sceners single out. Without them, lean on facts: compo wins, awards, being an early or
  notable example of something in the tags or notes.
- **highlights**: 0–4 short phrases (at most 6 words each) naming specific things on screen or notable about
  it. An empty list is better than guesses.
- **topics**: 1–3 from this fixed list, exactly as spelled:
  `Technical showpiece`, `Raster & colour tricks`, `Border & screen-mode tricks`, `3D & vectors`, `Sprites`,
  `Scrollers & typography`, `Pixel art & graphics`, `Music first`, `Design & storytelling`,
  `Humour & weirdness`, `Tiny intros`, `Text-mode art`, `Video & animation`, `Ports & tributes`.
  `Tiny intros` is for size-limited intros of 4K or less.
- **quote**: `null`, or one excerpt copied **exactly** from a `csdb_comments` entry: a contiguous substring of
  at most 200 characters, with the comment's `user` and `date`. Choose the line that best says why people love
  it. Never a criticism, an in-joke or a reply to another user. No quote when there are no comments, or when
  none is a good one.
- **basis**: `"comments"` if the card draws on CSDb comments; `"facts"` if only on the fact sheet;
  `"facts+knowledge"` if you also used background knowledge (see below).

## Rules

- **Don't invent.** Every claim must come from the fact sheet (title, credits, placings, awards, tags, Demozoo
  notes, video title, comments). Background knowledge is allowed only for well-documented facts you're sure of
  (for example, that a famous prod is a port of a famous PC demo). If you use it, set `basis` to
  `"facts+knowledge"`. Never guess effects from a title.
- Thin fact sheets get short, factual cards. That's fine.
- Tone: a knowledgeable friend recommending something. Plain words, British spelling, no hype ("stunning",
  "mind-blowing", "legendary", "masterpiece"), no exclamation marks, no vote counts.
- Name people and groups exactly as given. Don't explain what the demoscene is.
- Tags such as `8580`/`6581` (SID chip models), `pt3`, `sap` and `ay` are music formats or hardware. They're
  fine to use as facts but are rarely highlights.
