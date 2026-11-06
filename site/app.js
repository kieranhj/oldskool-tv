"use strict";
// Oldskool TV: a static single-page app over data/catalog.json. Routes live in the URL hash.

const $ = (s, el = document) => el.querySelector(s);
const view = $("#view");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const slug = (s) => encodeURIComponent(s);
const store = {
  get(k, d) { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode: fine */ } },
};

let DB = [], META = {}, BY_ID = new Map();

// ---------- theme ----------
function applyTheme(t) { document.documentElement.dataset.theme = t; }
applyTheme(store.get("theme", matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"));
$("#theme").onclick = () => { const t = document.documentElement.dataset.theme === "light" ? "dark" : "light"; applyTheme(t); store.set("theme", t); };

// ---------- nav ----------
$("#menu").onclick = () => document.body.classList.toggle("nav-open");
$("#scrim").onclick = () => document.body.classList.remove("nav-open");
$("#search").onsubmit = (e) => { e.preventDefault(); const q = $("#q").value.trim(); location.hash = q ? `#/search/${slug(q)}` : "#/"; };
addEventListener("keydown", (e) => {
  if (e.key === "/" && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); $("#q").focus(); }
});

function sidebar(active) {
  const later = store.get("later", []).length;
  const a = (href, label, n) => `<a href="${href}" class="${href === active ? "on" : ""}"><span>${esc(label)}</span><span>${n ?? ""}</span></a>`;
  $("#side").innerHTML =
    a("#/", "Home") + a("#/later", "Watch later", later || "") + a("#/about", "About") +
    `<h4>Platforms</h4>` + META.platforms.map(([p, n]) => a(`#/platform/${slug(p)}`, p, n)).join("") +
    `<h4>Topics</h4>` + META.topics.map(([t, n]) => a(`#/topic/${slug(t)}`, t, n)).join("");
}

// ---------- helpers ----------
const thumb = (r) => `https://i.ytimg.com/vi/${r.video}/mqdefault.jpg`;
const byline = (r) => esc(r.by.join(", ") || "Unknown");
function placingBadge(r) {
  const p = r.placings[0];
  if (!p) return "";
  return p.rank === 1 ? "1st" : p.rank === 2 ? "2nd" : p.rank === 3 ? "3rd" : "";
}
function card(r, reason) {
  const pb = placingBadge(r);
  return `<a class="vcard" href="#/watch/${r.id}">
    <div class="thumb"><img loading="lazy" src="${thumb(r)}" alt="">
      <span class="badge">${esc(r.platform)}</span>${pb ? `<span class="badge r">${pb}</span>` : ""}</div>
    <div class="vt">${esc(r.title)}</div>
    <div class="sub">${byline(r)} · ${r.year ?? "?"} · ${esc(r.kind)}</div>
    ${reason ? `<div class="reason">${esc(reason)}</div>` : ""}
  </a>`;
}
function shelf(title, sub, rows, more, reason) {
  if (!rows.length) return "";
  return `<section class="shelf"><div class="shelf-head"><h2>${esc(title)}</h2>${more ? `<a href="${more}">See all</a>` : ""}</div>
    ${sub ? `<p class="shelf-sub">${esc(sub)}</p>` : ""}
    <div class="row">${rows.map((r) => card(r, reason?.(r))).join("")}</div></section>`;
}
const byScore = (a, b) => b.score - a.score;
const total = (r) => r.votes.up + r.votes.pig + r.votes.down;
const approval = (r) => (r.votes.up + 0.5 * r.votes.pig) / Math.max(1, total(r));

// ---------- lists used by the home page and "see all" pages ----------
const LISTS = {
  classics: { title: "All-time classics", sub: "The best-loved 8-bit prods, across every machine.",
    rows: () => [...DB].sort(byScore), reason: (r) => r.why },
  "still-loved": { title: "Still loved", sub: "Released before 2019 and still picking up thumbs on Pouet years later.",
    rows: () => DB.filter((r) => r.votes.since2019 > 0).sort((a, b) => b.votes.since2019 - a.votes.since2019),
    reason: (r) => `+${r.votes.since2019} thumbs up since 2019` },
  new: { title: "New classics", sub: "Released since 2019 and already up with the greats.",
    rows: () => DB.filter((r) => r.year >= 2019).sort(byScore), reason: (r) => r.why },
  golden: { title: "Golden oldies", sub: "From before 1995, when it all started.",
    rows: () => DB.filter((r) => r.year && r.year < 1995).sort(byScore), reason: (r) => r.why },
  gems: { title: "Hidden gems", sub: "Near-universal approval from the people who've seen them, but fewer have.",
    rows: () => DB.filter((r) => total(r) < 40 && total(r) >= 5).sort((a, b) => approval(b) - approval(a) || b.score - a.score),
    reason: (r) => r.why },
  tiny: { title: "Tiny intros", sub: "Whole productions in a few kilobytes or less.",
    rows: () => DB.filter((r) => / intro$/.test(r.kind) && /^(\d+b|1K|2K|4K)/.test(r.kind)).sort(byScore),
    reason: (r) => r.kind },
};

// ---------- pages ----------
function home() {
  document.title = "Oldskool TV";
  const plats = META.platforms.slice(0, 6).map(([p]) =>
    shelf(p, "", DB.filter((r) => r.platform === p).sort(byScore).slice(0, 12), `#/platform/${slug(p)}`, (r) => r.why)).join("");
  const s = (k) => { const L = LISTS[k]; return shelf(L.title, L.sub, L.rows().slice(0, 12), `#/list/${k}`, L.reason); };
  view.innerHTML = `<h1>The 8-bit demoscene, worth watching</h1>
    <p class="lede">${META.videos} classics from the C64, Spectrum, Atari, CPC and ${META.platforms.length - 4} more machines,
    picked from what sceners have voted for on Pouet and Demozoo, and what they're still voting for.</p>
    ${s("classics")}${s("still-loved")}${s("new")}${s("gems")}${s("golden")}${s("tiny")}${plats}`;
}

function list(key) {
  const L = LISTS[key];
  if (!L) return notFound();
  document.title = `${L.title} - Oldskool TV`;
  view.innerHTML = `<h1>${esc(L.title)}</h1><p class="lede">${esc(L.sub)}</p>
    <div class="grid">${L.rows().map((r) => card(r, L.reason(r))).join("")}</div>`;
}

const SORTS = {
  best: ["Best", byScore],
  newest: ["Newest", (a, b) => (b.year ?? 0) - (a.year ?? 0) || byScore(a, b)],
  oldest: ["Oldest", (a, b) => (a.year ?? 9999) - (b.year ?? 9999) || byScore(a, b)],
};
function filtered(title, sub, rows, base, sort) {
  sort = SORTS[sort] ? sort : "best";
  view.innerHTML = `<h1>${esc(title)}</h1>${sub ? `<p class="lede">${esc(sub)}</p>` : ""}
    <div class="chips">${Object.entries(SORTS).map(([k, [label]]) =>
      `<a class="chip ${k === sort ? "on" : ""}" href="${base}/${k}">${label}</a>`).join("")}</div>
    <div class="grid">${[...rows].sort(SORTS[sort][1]).map((r) => card(r, r.why)).join("")}</div>`;
}
function platform(p, sort) {
  const rows = DB.filter((r) => r.platform === p);
  if (!rows.length) return notFound();
  document.title = `${p} - Oldskool TV`;
  filtered(p, `${rows.length} prods to watch.`, rows, `#/platform/${slug(p)}`, sort);
}
function topic(t, sort) {
  const rows = DB.filter((r) => r.topics.includes(t));
  if (!rows.length) return notFound();
  document.title = `${t} - Oldskool TV`;
  filtered(t, `${rows.length} prods.`, rows, `#/topic/${slug(t)}`, sort);
}

function haystack(r) {
  return r._hay ??= [r.title, r.by.join(" "), r.platform, r.kind, r.summary, r.why, r.highlights.join(" "),
    r.topics.join(" "), r.credits.map((c) => c.who.join(" ")).join(" "), r.placings.map((p) => p.party).join(" "),
    r.year].join(" ").toLowerCase();
}
function search(q) {
  document.title = `${q} - Oldskool TV`;
  $("#q").value = q;
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  const hits = DB.map((r) => {
    const h = haystack(r);
    if (!terms.every((t) => h.includes(t))) return null;
    const inTitle = terms.filter((t) => (r.title + " " + r.by.join(" ")).toLowerCase().includes(t)).length;
    return [r, inTitle * 10 + r.score];
  }).filter(Boolean).sort((a, b) => b[1] - a[1]).map(([r]) => r);
  view.innerHTML = `<h1>Results for “${esc(q)}”</h1><p class="lede">${hits.length} found.</p>
    <div class="grid">${hits.map((r) => card(r, r.why)).join("")}</div>`;
}

function laterList() {
  document.title = "Watch later - Oldskool TV";
  const ids = store.get("later", []);
  const rows = ids.map((id) => BY_ID.get(id)).filter(Boolean);
  view.innerHTML = `<h1>Watch later</h1><p class="lede">${rows.length ? "Saved in this browser only." : "Nothing saved yet. Use “Watch later” on any video."}</p>
    <div class="grid">${rows.map((r) => card(r, r.why)).join("")}</div>`;
}

function toggleLater(id) {
  const ids = store.get("later", []);
  const i = ids.indexOf(id);
  i >= 0 ? ids.splice(i, 1) : ids.unshift(id);
  store.set("later", ids);
  return i < 0;
}

const ordinal = (n) => n + ((n % 100 >= 11 && n % 100 <= 13) ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[n % 10] || "th"));

function watch(id) {
  const r = BY_ID.get(id);
  if (!r) return notFound();
  document.title = `${r.title} - Oldskool TV`;
  const L = r.links;
  const links = [
    L.pouet && `<a href="https://www.pouet.net/prod.php?which=${L.pouet}" target="_blank" rel="noopener">Pouet</a>`,
    L.demozoo && `<a href="https://demozoo.org/productions/${L.demozoo}/" target="_blank" rel="noopener">Demozoo</a>`,
    L.csdb && `<a href="https://csdb.dk/release/?id=${L.csdb}" target="_blank" rel="noopener">CSDb</a>`,
    L.zxart && `<a href="https://zxart.ee/eng/software/${esc(L.zxart)}/" target="_blank" rel="noopener">ZXArt</a>`,
    `<a href="https://www.youtube.com/watch?v=${r.video}" target="_blank" rel="noopener">YouTube${r.channel ? ` (${esc(r.channel)})` : ""}</a>`,
  ].filter(Boolean).join("");
  const facts = [
    ["By", byline(r)],
    ["Released", esc(r.release ?? r.year ?? "unknown")],
    ["Platform", `<a href="#/platform/${slug(r.platform)}">${esc(r.platform)}</a>`],
    ["Type", esc(r.kind)],
    ...(r.expanded.length ? [["Needs", esc(r.expanded.join(", "))]] : []),
    ...r.placings.map((p) => ["Compo", `${ordinal(p.rank)} in ${esc(p.compo)} at ${esc(p.party)}`]),
    ...r.awards.map((a) => ["Award", `${a.status === "winner" ? "Winner" : "Nominee"}: ${esc(a.category)} (${esc(a.event)})`]),
    ...r.credits.map((c) => [esc(c.role), esc(c.who.join(", "))]),
    ["Pouet", `${r.votes.up} up · ${r.votes.pig} pig · ${r.votes.down} down${r.votes.cdc ? ` · ${r.votes.cdc} coup${r.votes.cdc > 1 ? "s" : ""} de cœur` : ""}`],
  ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  const q = r.quote;
  const basis = { comments: "Written by Claude from CSDb comments and the Pouet/Demozoo records.",
    facts: "Written by Claude from the Pouet/Demozoo records.",
    "facts+knowledge": "Written by Claude from the Pouet/Demozoo records and background knowledge.",
    none: "No write-up yet." }[r.basis];
  const later = store.get("later", []).includes(r.id);
  const next = upNext(r);
  view.innerHTML = `<div class="watch">
    <div>
      <div class="player"><iframe src="https://www.youtube-nocookie.com/embed/${r.video}?rel=0" title="${esc(r.title)}"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen></iframe></div>
      <h1 class="wtitle">${esc(r.title)}</h1>
      <div class="wmeta"><span><a href="#/search/${slug(r.by[0] ?? "")}">${byline(r)}</a></span><span>${r.year ?? ""}</span>
        <span>${esc(r.platform)}</span><span>${esc(r.kind)}</span>${r.expanded.length ? `<span>Needs ${esc(r.expanded.join(", "))}</span>` : ""}</div>
      <div class="actions">
        <button class="btn ${later ? "on" : ""}" id="later"><svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 10.4 3.5 2.1-.8 1.3L11 13V7h2z"/></svg><span>${later ? "Saved" : "Watch later"}</span></button>
        ${r.emulator && L.demozoo ? `<a class="btn" href="https://demozoo.org/productions/${L.demozoo}/" target="_blank" rel="noopener">Run it in your browser (Demozoo)</a>` : ""}
        ${r.topics.map((t) => `<a class="chip" href="#/topic/${slug(t)}">${esc(t)}</a>`).join("")}
      </div>
      <div class="panel">
        <p>${esc(r.summary)}</p>
        ${r.why ? `<p class="why">${esc(r.why)}</p>` : ""}
        ${r.highlights.length ? `<div class="hl">${r.highlights.map((h) => `<span>${esc(h)}</span>`).join("")}</div>` : ""}
        ${q ? `<blockquote><p>“${esc(q.text)}”</p><cite>${esc(q.user ?? "CSDb user")}${q.date ? `, ${esc(q.date)}` : ""}, on CSDb</cite></blockquote>` : ""}
        <div class="basis">${basis}</div>
      </div>
      <div class="panel"><h3>Details</h3><dl class="facts">${facts}</dl></div>
      <div class="panel"><h3>Elsewhere</h3><div class="links">${links}</div></div>
    </div>
    <aside class="next"><h3>Up next</h3>${next.map((n) => `<a class="mini" href="#/watch/${n.id}">
      <div class="thumb"><img loading="lazy" src="${thumb(n)}" alt=""></div>
      <div><div class="vt">${esc(n.title)}</div><div class="sub">${byline(n)} · ${n.year ?? ""}<br>${esc(n.platform)}</div></div></a>`).join("")}</aside>
  </div>`;
  $("#later").onclick = (e) => {
    const on = toggleLater(r.id);
    e.currentTarget.classList.toggle("on", on);
    e.currentTarget.querySelector("span").textContent = on ? "Saved" : "Watch later";
    sidebar(location.hash);
  };
}

function upNext(r) {
  // Same authors first, then shared topics on the same platform, then the same platform, then shared topics anywhere.
  const scoreOf = (o) => (o.by.some((b) => r.by.includes(b)) ? 4 : 0) + (o.platform === r.platform ? 2 : 0) +
    o.topics.filter((t) => r.topics.includes(t)).length * 1.5 + o.score / 10;
  return DB.filter((o) => o.id !== r.id).map((o) => [o, scoreOf(o)]).sort((a, b) => b[1] - a[1]).slice(0, 14).map(([o]) => o);
}

function about() {
  document.title = "About - Oldskool TV";
  const withQuote = DB.filter((r) => r.quote).length;
  view.innerHTML = `<article class="prose">
    <h1>About Oldskool TV</h1>
    <p class="lede">The 8-bit demoscene prods worth watching, as videos, each with a short write-up of what it is and why sceners rate it.</p>
    <div class="stats"><div><b>${META.videos}</b>videos</div><div><b>${META.platforms.length}</b>platforms</div>
      <div><b>${META.years[0]}–${META.years[1]}</b>years</div><div><b>${withQuote}</b>quotes from CSDb</div></div>
    <h2>How the picks are made</h2>
    <p>Every 8-bit prod with a YouTube video on <a href="https://www.pouet.net" target="_blank" rel="noopener">Pouet</a> or
    <a href="https://demozoo.org" target="_blank" rel="noopener">Demozoo</a> is a candidate. That's about 9,800 demos, intros, cracktros and invitations.
    Each is scored on its Pouet thumbs (with allowance for how many people voted), coups de cœur, compo placings and awards.
    Prods from before 2019 also score for the thumbs they've gained since then, using Pouet's archived weekly data, so the ones people are still discovering rise.
    Every platform gets a share of the list, so the C64 can't take every place.</p>
    <h2>The write-ups</h2>
    <p>Claude wrote each summary from the prod's records: credits, compo results, Demozoo tags and notes and, for the C64, user comments on
    <a href="https://csdb.dk" target="_blank" rel="noopener">CSDb</a>. Quotes are copied exactly from those comments.
    Each write-up says what it was based on. Spot a mistake? The source records are linked from every video page.</p>
    <p>Topics such as 3D or pixel art were labelled by Claude from Demozoo tags, the write-ups and three stills from each video,
    so they say what's on screen, not how it's done. Tiny intros are picked out from the prod type.</p>
    <h2>Thanks</h2>
    <p>All the data comes from the people who keep Pouet, Demozoo and CSDb going, and from the sceners who made, voted on and filmed these prods.
    Videos are played from YouTube and belong to their uploaders.</p>
    <p class="sub">Data built ${esc(META.generated)}. This is an early prototype.</p>
  </article>`;
}

function notFound() { view.innerHTML = `<p class="status">Nothing here. <a href="#/">Back home</a>.</p>`; }

// ---------- router ----------
function route() {
  const [, page, a, b] = location.hash.replace(/^#/, "").split("/").map((s) => decodeURIComponent(s || ""));
  document.body.classList.remove("nav-open");
  if (page !== "search") $("#q").value = "";
  sidebar(location.hash || "#/");
  if (!page) home();
  else if (page === "watch") watch(a);
  else if (page === "platform") platform(a, b);
  else if (page === "topic") topic(a, b);
  else if (page === "list") list(a);
  else if (page === "search") search(a);
  else if (page === "later") laterList();
  else if (page === "about") about();
  else notFound();
  scrollTo(0, 0);
}

Promise.all([fetch("data/catalog.json").then((r) => r.json()), fetch("data/meta.json").then((r) => r.json())])
  .then(([db, meta]) => {
    DB = db; META = meta; BY_ID = new Map(db.map((r) => [r.id, r]));
    addEventListener("hashchange", route);
    route();
  })
  .catch((e) => { view.innerHTML = `<p class="status">Couldn't load the catalogue (${esc(e.message)}).</p>`; });
