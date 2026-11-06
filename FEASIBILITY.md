# Oldskool TV: feasibility study and plan

*6 November 2026.*

The idea: a [HackerTube](https://hackertube.org/about)-style site for 8-bit demoscene videos. HackerTube's model is
"the YouTube videos Hacker News keeps telling each other to watch". Ours is "the 8-bit prods the scene keeps
coming back to, as videos", with each one explained, browsable by platform and era, and linked back to Pouet,
Demozoo and (where we can) to an emulator that runs the real thing.

Scope agreed so far: **8-bit platforms only**, **classics to watch** rather than a full archive, a new repo and
domain if it gets that far.

## Short answer

**It's feasible, and Pouet comments are a nice-to-have, not a requirement.**

- About **11,200 8-bit prods have a YouTube video** across Pouet and Demozoo, roughly twice the size of all of
  HackerTube. A classics shortlist would be 1,500–3,000 of them.
- Everything we need for **ranking** is in public bulk dumps that need no scraping: Pouet's weekly dump and its
  weekly archive back to July 2019, and Demozoo's nightly SQL export. Demozoo already mirrors Pouet's vote
  counts and cross-links 99% of the 8-bit Pouet prods.
- What Pouet comments add is the **"why sceners love it" text** on each video card. Without them, the C64 (half
  the set) can use CSDb's comments, which are open and better written. The other platforms would get cards built
  from facts (credits, compo, effects, tags) rather than quotes from the scene.
- Only **about 6% of YouTube links are dead**.

## What I measured

The scripts are in `feasibility/` and the data was downloaded to a temporary folder. The numbers come from
Pouet's dump of 4 Nov 2026 and Demozoo's export of 6 Nov 2026.

### Sources

| Source | Access | What it gives us |
|---|---|---|
| Pouet weekly dump (`data.pouet.net`) | Open, 15 MB gzip, weekly archive back to **2019-07-25** (380 dumps) | Prods, platforms, types, groups, thumbs up/pig/down, coups de coeur, popularity, compo placings, awards, download links incl. YouTube, Demozoo/CSDb ids. **No comments.** |
| Pouet API (`api.pouet.net/v1`) | Open, no key, no stated rate limit | `prod/comments/?id=` returns every comment with its thumb rating and date |
| Demozoo nightly export (`data.demozoo.org/demozoo-export.sql.gz`) | Open, 200 MB pg_dump, parsed without Postgres by `demozoo_load.py` | Productions, platforms, types, credits, groups, 160k compo placings, awards nominations (Meteoriks etc.), 770k external links (37.6k YouTube), tags, 11k comments, screenshots, **a mirror of Pouet's vote counts**, and in-browser emulator configs |
| Demozoo API | **Now needs an API key** (403 "Authentication credentials were not provided"); the website also blocks automated fetches | Not needed: the dump has everything |
| CSDb web service (`csdb.dk/webservice`) | Open XML, one release per request, no stated terms or limits | C64 releases with rating, credits and **user comments** |

### The 8-bit slice

The 8-bit platforms are those with an 8-bit CPU (6502, Z80, 6809, 8080 families); the lists are in
`feasibility/common.py`. Amiga, ST, Archimedes, BK-0010 and Apple IIgs are left out.

| | Pouet | Demozoo |
|---|---|---|
| 8-bit prods | 29,506 | 49,433 (plus 41k music and graphics entries) |
| …with a YouTube link | **8,328** | **8,814** |
| Cross-linked | 8,215 of the 8,328 are on Demozoo | 6,944 of the 8,814 link to a Pouet prod |
| **Union with a video** | **≈ 11,200 distinct prods** | |

Prods with a video, by platform (Demozoo counts):

| Platform | With video | | Platform | With video |
|---|---:|---|---|---:|
| C64 | 4,163 | | Atari VCS | 145 |
| Atari 8-bit | 1,602 | | C16/Plus4 | 131 |
| ZX Spectrum | 1,506 | | ZX Enhanced | 100 |
| Amstrad CPC (+Plus) | 239 | | MSX | 83 |
| Apple II | 148 | | Lynx, VIC-20, GBC, NES… | under 100 each |

The BBC Micro has 35 (Demozoo) or 30 (Pouet).

By type: demos 4.2k, intros 0.9k, cracktros 0.7k, 256-byte intros 0.6k, 4k 0.3k, 1k 0.2k, and also musicdisks,
invitations, slideshows and a long tail of 32–128-byte intros.

Pouet vote depth for 8-bit prods with a video:

| Votes | ≥1 | ≥5 | ≥10 | ≥25 | ≥50 | ≥100 |
|---|---:|---:|---:|---:|---:|---:|
| Prods | 7,725 | 4,702 | 2,872 | 1,006 | 333 | 71 |

Other signals: 5,687 have compo placings (Demozoo), 4,364 link to CSDb, 3,608 are tagged on Demozoo, 195 have Pouet
coups de coeur, and 147 have award nominations.

### Pouet comments (sample of 200 prods, 40 from each vote band, fetched at 1 request per second)

| Votes | Comments per prod (median) | Substantive ones, ≥40 chars (median) |
|---|---:|---:|
| 0–4 | 2 | 0 |
| 5–9 | 7 | 2 |
| 10–24 | 15.5 | 6 |
| 25–49 | 37.5 | 16.5 |
| 50+ | 83.5 | 34 |

- 6,209 comments in the sample. The median length is 31 characters and 43% are 40 characters or longer.
- 82% carry a thumbs up, 16% are neutral and 2% a thumbs down.
- Comments are spread over time: 142 of the 196 prods with comments had them in 3 or more different months. That
  means HackerTube's "recommended in N separate months" rule carries straight over.
- Estimated total for the 8-bit set with videos: **about 105k comments from 8.3k requests (2.3 hours at
  1 request per second)**. A shortlist of prods with 5+ votes needs 4.7k requests (1.3 hours) and covers about
  99k comments.
- The quality is good. On *melange* (4th Dimension and Light Future, ZX Spectrum, 2000), the comments name the
  coder, the musician and the effects, call it "one of the few true milestone demos on zx", and debate whether its
  graphics were copied. That is exactly the material a card needs.

### CSDb comments (sample of 40 C64 releases that have a video)

- The median is 4.5 user comments per release and the mean 10.7. 9 of the 40 have none, and 20 have five or more.
- Comments are longer than Pouet's (median 81 characters). They include memories, technique notes and some
  noise such as bug reports and politics.
- 20 of the 40 have a CSDb rating. CSDb itself doesn't list YouTube links; those come from Pouet and Demozoo.

### YouTube links (oEmbed check on 300 random prods)

- 281 work, 18 return 404 (gone) and 1 returns 401 (private or not embeddable). That is **about 6% to drop or
  replace**.
- Most videos come from a handful of channels: Demoscene 'n' Stuff, C64!, "Commodore 64 / Amiga Demos in 4K",
  RetroDemoScene, Demoscene TV and so on. That's useful for preferring good captures.

### A first ranking without comments (`rank_sketch.py`)

The score combines the thumbs-up share (a Wilson lower bound, so a handful of votes can't top the chart), the
number of thumbs up, thumbs up gained since July 2019, coups de coeur and top-3 compo placings. It already looks
sensible:

- **Overall:** Edge of Disgrace, Batman Forever, Ghost NOP, ganzfeld, Rewind 2, Coma Light 13, Freespin, unspoken,
  E2iRA, Desert Dream, and so on.
- **BBC Micro:** Evil Influences, NOVA Online Invite, beeb-niccc, Beep!, Twisted Brain.
- **Still loved:** 2,460 of the 5,353 pre-2019 prods have gained votes since 2019, 164 of them by 5 or more.
  Leading are Drunk Chessboard, Mathematica, Second Reality 64 and others.

It has two biases to fix:

1. **Pouet under-represents old C64 classics.** The C64 scene votes on CSDb, so the score needs CSDb's rating and
   vote count for C64 prods.
2. **Votes gained since 2019 favour recent releases**, because every vote they have is new. The fix is to measure
   it only for prods released before the window, or as a share of votes per year since release.

## What if we can't use Pouet comments?

The ranking, browsing and video pages are unaffected. What we lose is the "voice of the scene" on each card.
Replacements, from best to weakest:

1. **CSDb comments for the C64** (about 40% of the set): open, and better written than Pouet's. About 4.4k
   requests at 1 per second, which is 1.2 hours.
2. **Facts instead of quotes for everyone else.** Claude writes the card from credits, the party and compo result,
   the type and size class, Demozoo tags (many name effects or modes: petscii, interlaced, IFLI, 2SID…), Demozoo
   notes (only 528 prods) and the YouTube title and description. The cards would read more like encyclopaedia
   entries than "why HN likes it". Accuracy is fine, but there's less personality.
3. **Demozoo's own comments:** only 2,021 comments on 1,487 8-bit prods. Too thin to rely on.
4. **Untested:** YouTube's own comments through the Data API (the free quota is enough), and Claude describing
   frames from the video so the card says what's on screen. HackerTube's config mentions `frames_source:
   youtube`, so Karpathy may do something similar.
5. **Platform databases** for other machines, such as ZXArt for the Spectrum. Not checked; ZXArt's API page didn't
   load.

A note on the Pouet API: `prod/comments/` is a public, documented endpoint with no key. A one-off crawl of 4,700
prods at 1 request per second, with an honest User-Agent, then a weekly top-up, is ordinary API use and not the
dump request Gargaj has turned down before. The bigger question is **showing** comment quotes on our site. That's
a courtesy and permission question whichever way we fetch them, so it may be worth asking about display rather
than fetching. The decision is yours. The plan below runs either way.

## Plan

### Phase 0: spike (a few days)
- **Hosting:** a new GitHub repo with Pages (`<you>.github.io/oldskool-tv`) is exactly as fast as a subfolder of
  bitshifters.github.io, and avoids mixing a data site into the group site. A custom domain is a `CNAME` file
  away later. Recommendation: a new repo from day one.
- Build the pipeline end to end on the **top ~300 prods**. Write cards with the fallback recipe (no Pouet
  comments), plus CSDb comments for the C64. Build a static site with a home page, a watch page and platform
  browsing.

### Phase 1: data pipeline (Python, SQLite, rebuilt weekly)
1. **Ingest:** the Pouet weekly dump, one archived Pouet dump per year since 2019 (for vote history), and the
   Demozoo nightly export (`demozoo_load.py`, keeping only the tables we need).
2. **Merge** on Pouet id: Demozoo's `PouetProduction` links plus the Demozoo ids in Pouet's dump. The 8-bit sets
   already match for 99% of prods.
3. **Pick the video:** take the union of YouTube ids, check each with oEmbed and drop dead ones. Prefer the link
   both sites agree on, then known capture channels. Optionally fetch duration and views from the YouTube Data
   API: one call per 50 videos, about 230 calls for the whole set.
4. **Score and shortlist:** the Wilson score, CSDb rating for the C64, coups de coeur, compo placing, awards, and
   votes still arriving since 2019 (adjusted for release age). Keep one cut per platform so the C64 doesn't crowd
   out the Oric. **Target 1,500–3,000 videos.**
5. **Comments** (if we go ahead): Pouet for the shortlist and CSDb for its C64 entries, fetched slowly and cached,
   then topped up weekly for new comments only.

### Phase 2: cards and topics (Claude)
- **Per comment:** a stance label (recommend, strong recommend, critique, joke or chat, technical note) and a
  quote. About 100k short comments is a few million input tokens. Use a small model through the Batch API, run
  a 200-prod sample first to check quality and cost, and price it against current rates before the full run.
- **Per prod:** a summary, "why the scene loves it", highlights (effects and techniques), the kind of prod (demo,
  intro size class, cracktro…), whether it has aged well, and an era.
- **Topics:** platform × era × size class × effects and style (from Demozoo tags plus Claude's tags).
- **Embeddings:** bge-small, 384 dimensions, as HackerTube uses. For 3k videos that's about 1.2 MB at int8, small
  enough for search that runs entirely in the browser.

### Phase 3: static site
- **Home rows:** All-time classics, Still loved (votes still arriving years later), Hidden gems (high approval,
  few YouTube views), New classics, and a row per platform.
- **Watch page:** the YouTube embed, the card, quotes linked back to Pouet and CSDb, credits, the party and
  placing, and a **Run it for real** button. Demozoo already has 2,559 in-browser JSSpeccy configs for the
  Spectrum. Use bbc.xania.org for the BBC and add other emulators where it's easy.
- **Compo playlists** (e.g. "Revision 2024 Oldskool Demo, in finishing order"), group and scener pages, and
  semantic search.
- Likes, watch later and history kept in localStorage, with no accounts, as HackerTube does.
- A weekly GitHub Actions job rebuilds the JSON and redeploys.

### Phase 4: polish and launch
- Credits and licence page: credit Pouet, Demozoo and CSDb, and don't redistribute YouTube metadata (as
  HackerTube does).
- Decide on a domain. Optionally publish the cards and topics as a downloadable dataset, like HackerTube does.

## Open questions

1. **Licences:** none of the three sites states a data licence, and Demozoo's GitHub source has no LICENCE
   file either. Kieran knows Demozoo's author, Matt Westcott, and will ask him before hosting properly. If we
   keep any comment quotes, ask Pouet and CSDb about displaying them.
2. **Pouet comments:** crawl the public API slowly, ask about display first, or go without them (CSDb plus the
   fact-based fallback)?
3. **What counts as 8-bit:** include the Atari Lynx, PC Engine (8-bit CPUs, but console-like) and calculators?
   Currently yes, yes and no.
4. **Which types count:** cracktros, musicdisks and slideshows dilute "demos to watch". Perhaps separate rows
   rather than leaving them out.

## Files

- `feasibility/common.py`: 8-bit platform lists for Pouet and Demozoo, and the YouTube id regex.
- `feasibility/pouet_8bit.py`: sizes the 8-bit slice of the Pouet dump and writes `pouet8.jsonl`.
- `feasibility/demozoo_load.py`: Demozoo pg_dump to SQLite (selected tables, no Postgres needed).
- `feasibility/demozoo_8bit.py`: the Demozoo 8-bit slice, its overlap with Pouet, and other signals.
- `feasibility/pouet_comments_sample.py`: stratified comment sample (1 request per second).
- `feasibility/csdb_sample.py`: CSDb comment sample (1 request per second).
- `feasibility/yt_alive.py`: YouTube oEmbed liveness check.
- `feasibility/rank_sketch.py`: first-cut ranking without comments.
