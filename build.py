"""Build the Art Intelligence website.

Reads all copy from content.toml, fetches the latest posts from Substack,
and writes the finished pages to _site/. Run with:  python3 build.py
If Substack can't be reached, the last fetched posts (posts-cache.json) are used.
"""
import email.utils
import html
import json
import re
import shutil
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
CACHE = ROOT / "posts-cache.json"

C = tomllib.loads((ROOT / "content.toml").read_text(encoding="utf-8"))
S = C["site"]


def t(s):
    """Escape text and turn **words** into the heavier weight."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(s, quote=False))


def attr(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- Substack
def fetch_posts():
    feed = S["substack"].rstrip("/") + "/feed"
    try:
        req = urllib.request.Request(feed, headers={"User-Agent": "artintelligence-site-build"})
        with urllib.request.urlopen(req, timeout=20) as r:
            root = ET.fromstring(r.read())
        posts = []
        for it in root.findall("./channel/item"):
            d = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
            posts.append({"title": (it.findtext("title") or "").strip(),
                          "link": (it.findtext("link") or "").strip(),
                          "date": d.strftime("%-d %b %Y"),
                          "iso": d.strftime("%Y-%m-%d")})
        CACHE.write_text(json.dumps(posts, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"Fetched {len(posts)} posts from Substack")
        return posts
    except Exception as e:  # network down, feed changed: fall back to the last good copy
        print(f"Could not fetch Substack ({e}); using cached posts")
        return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else []


def filtered(posts):
    ex = [x.lower() for x in C["writing"]["exclude"]]
    keep = [p for p in posts if not any(x in p["title"].lower() for x in ex)]
    return keep[: C["writing"]["max_posts"]]


# ---------------------------------------------------------------- pieces
def head(title, desc):
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{attr(title)}</title>
<meta name="description" content="{attr(desc)}">
<link rel="preload" href="fonts/ValleySans-Variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sorts+Mill+Goudy:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
"""


def header(cur):
    def a(href, label, key):
        c = ' aria-current="page"' if key == cur else ""
        return f'<a href="{href}"{c}>{label}</a>'
    return f"""<header class="site-header">
  <div class="bar">
    <a class="logo" href="index.html"><img src="assets/logo-carbon.png" alt="Art Intelligence" width="128" height="31"></a>
    <nav class="nav t-detail" aria-label="Main">
      {a("services.html", "Services", "services")}
      {a("services.html#prompt-guide", "Prompt guide", "")}
      {a("writing.html", "Writing", "writing")}
      {a("about.html", "About", "about")}
      <a class="cta" href="{attr(S['booking_url'])}">Book a call</a>
    </nav>
  </div>
</header>
"""


def footer():
    return f"""<footer class="site-footer section">
  <div class="panel mahogany dark">
    <div class="top">
      <p class="mark" aria-label="Art Intelligence">Art<br>INT.</p>
      <div class="contact">
        <p class="t-sub">{t(C['footer']['heading'])}</p>
        <a class="cta" href="{attr(S['booking_url'])}">Book a call</a>
      </div>
    </div>
    <div class="follow">
      <a href="{attr(S['instagram'])}"><span class="t-detail">Instagram</span><span class="h">{t(S['instagram_handle'])}</span></a>
      <a href="{attr(S['substack'])}"><span class="t-detail">Substack</span><span class="h">The Art Intelligence</span></a>
      <a href="{attr(S['linkedin'])}"><span class="t-detail">LinkedIn</span><span class="h">Alice Acland</span></a>
      <a href="mailto:{attr(S['email'])}"><span class="t-detail">Email</span><span class="h">{t(S['email'])}</span></a>
    </div>
    <div class="bottom t-detail"><span class="muted">{t(S['copyright'])}</span></div>
  </div>
</footer>
</body>
</html>
"""


def facts(rows):
    return '<dl class="facts">' + "".join(
        f'<div><dt class="t-detail">{t(a)}</dt><dd>{t(b)}</dd></div>' for a, b in rows) + "</dl>"


def post_list(posts):
    return "\n".join(
        f'        <li><a href="{attr(p["link"])}"><span class="t-detail muted"><time datetime="{p["iso"]}">{p["date"]}</time></span>'
        f'<span class="t">{t(p["title"])}</span></a></li>' for p in posts)


# ---------------------------------------------------------------- pages
def home(posts):
    H = C["home"]
    idx = "\n".join(f'          <li><a href="{attr(s["link"])}"><span class="n">{i+1:02d}</span><span class="t">{t(s["title"])}</span></a></li>'
                    for i, s in enumerate(C["services_index"]))
    names = "".join(f"<span>{t(n)}</span>" for n in H["experience"])
    stages = "\n".join(f'        <div><span class="t-detail">{i+1:02d}</span><h3>{t(a)}</h3><p>{t(b)}</p></div>'
                       for i, (a, b) in enumerate(H["stages"]))
    also = "\n".join(f'        <div class="svc"><h3>{t(a)}</h3><p>{t(b)}</p><a class="t-detail link" href="{attr(l)}">{t(lt)}</a></div>'
                     for a, b, lt, l in H["also"])
    return head(S["name"], S["description"]) + header("home") + f"""
<main>
  <section class="panel cloud first hero-dot" aria-labelledby="h1">
    <div class="wrap hero2">
      <div class="copy">
        <span class="t-detail label">{t(H['label'])}</span>
        <h1 class="t-display" id="h1">{t(H['headline'])}</h1>
        <div class="actions"><a class="cta" href="{attr(S['booking_url'])}">Book a call</a></div>
      </div>
      <nav class="sample index-list" aria-label="Services">
        <ol class="t-list list">
{idx}
        </ol>
      </nav>
    </div>
  </section>

  <section class="section">
    <div class="wrap row">
      <span class="c-label t-detail rowlabel">{t(H['experience_label'])}</span>
      <p class="c-main names">{names}</p>
    </div>
  </section>

  <section class="section" aria-labelledby="con-h">
    <div class="wrap stack">
      <div class="row">
        <div class="c-label"></div>
        <h2 class="c-main t-sub" id="con-h">{t(H['consultancy_heading'])}</h2>
      </div>
      <div class="stages">
{stages}
      </div>
      <div class="row"><div class="c-label"></div><a class="c-main t-detail link" href="services.html#consultancy">Consultancy in detail</a></div>
    </div>
  </section>

  <section class="section">
    <div class="wrap row">
      <span class="c-label t-detail rowlabel">Also offered</span>
      <div class="c-main options">
{also}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="wr-h">
    <div class="wrap row">
      <div class="c-label stack" style="gap:20px">
        <h2 class="t-sub" id="wr-h">{t(H['writing_heading'])}</h2>
        <a class="t-detail link" href="writing.html">All writing</a>
      </div>
      <ul class="c-main posts">
{post_list(posts[:H['writing_count']])}
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="ab-h">
    <div class="wrap row" style="align-items:center">
      <div class="c-half"><div class="pair"><span aria-hidden="true"></span><img src="assets/portrait-square.jpg" alt="Alice Acland"></div></div>
      <div class="c-half stack" style="gap:24px">
        <h2 class="t-sub" id="ab-h">{t(H['founder_heading'])}</h2>
        <p class="measure">{t(H['founder_text'])}</p>
        <a class="t-detail link" href="about.html">About Alice</a>
      </div>
    </div>
  </section>
</main>
""" + footer()


def services():
    V = C["services"]
    stages = "\n".join(
        f'            <div><span class="t-detail">{i+1:02d}</span><h3>{t(n)}</h3><ul>'
        + "".join(f"<li>{t(x)}</li>" for x in items) + "</ul></div>"
        for i, (n, items) in enumerate(V["stages_detail"]))
    ws = "".join(f"<div><h3>{t(a)}</h3><p>{t(b)}</p></div>" for a, b in V["workshops"])
    also = "".join(f'<div class="svc"><h3>{t(a)}</h3><p>{t(b)}</p></div>' for a, b in V["also"])
    return head(f"Services | {S['name']}", "Consultancy, workshops, AI policy and a prompt guide for galleries, museums and foundations.") + header("services") + f"""
<main>
  <section class="intro-page">
    <div class="wrap row">
      <div class="c-label"></div>
      <h1 class="c-main t-display">{t(V['headline'])}</h1>
    </div>
  </section>

  <section class="section" id="consultancy" aria-labelledby="con-h">
    <div class="wrap stack">
      <div class="row">
        <div class="c-label"></div>
        <div class="c-main stack" style="gap:20px">
          <h2 class="t-sub" id="con-h">{t(V['consultancy_heading'])}</h2>
          <p class="measure">{t(V['consultancy_intro'])}</p>
        </div>
      </div>
      <div class="row">
        <div class="c-label"></div>
        <div class="c-main options">
          <div class="svc"><span class="t-detail">Option one</span><h3>{t(V['option_one_title'])}</h3>{facts(V['option_one'])}</div>
          <div class="svc"><span class="t-detail">Option two</span><h3>{t(V['option_two_title'])}</h3>{facts(V['option_two'])}</div>
        </div>
      </div>
      <div class="panel cloud flush">
        <div class="stack">
          <span class="t-detail rowlabel">What the work involves</span>
          <div class="stages">
{stages}
          </div>
        </div>
      </div>
      <div class="row">
        <span class="c-label t-detail rowlabel">Tools evaluated</span>
        <p class="c-main measure">{t(V['tools'])}</p>
      </div>
    </div>
  </section>

  <section class="section" id="workshops" aria-labelledby="ws-h">
    <div class="wrap stack">
      <div class="row">
        <div class="c-label"></div>
        <h2 class="c-main t-sub" id="ws-h">{t(V['workshops_heading'])}</h2>
      </div>
      <div class="row"><div class="c-label"></div><div class="c-main who" style="grid-template-columns:repeat(3,minmax(0,1fr))">{ws}</div></div>
    </div>
  </section>

  <section class="section" id="policy" aria-labelledby="po-h">
    <div class="wrap row">
      <div class="c-label"></div>
      <div class="c-main stack">
        <h2 class="t-sub" id="po-h">{t(V['policy_heading'])}</h2>
        {facts(V['policy'])}
      </div>
    </div>
  </section>

  <section class="section" id="prompt-guide" aria-labelledby="pg-h">
    <div class="wrap row">
      <div class="c-label"></div>
      <div class="c-main stack" style="gap:20px">
        <h2 class="t-sub" id="pg-h">{t(V['prompt_guide_heading'])}</h2>
        <p class="measure">{t(V['prompt_guide_text'])}</p>
        <a class="t-detail link" href="{attr(V['prompt_guide_link'])}">{t(V['prompt_guide_link_text'])}</a>
      </div>
    </div>
  </section>

  <section class="section" id="more">
    <div class="wrap row">
      <span class="c-label t-detail rowlabel">Also available</span>
      <div class="c-main options">{also}</div>
    </div>
  </section>
</main>
""" + footer()


def about():
    A = C["about"]
    paras = "".join(f"<p>{t(p)}</p>" for p in A["paragraphs"])
    pr = "".join(f"<div><h3>{t(a)}</h3><p>{t(b)}</p></div>" for a, b in A["principles"])
    return head(f"About Alice Acland | {S['name']}", "Alice Acland founded Art Intelligence in 2026 after ten years in public institutions and commercial galleries.") + header("about") + f"""
<main>
  <section class="intro-page">
    <div class="wrap row">
      <div class="c-label"></div>
      <h1 class="c-main t-display">{t(A['headline'])}</h1>
    </div>
  </section>

  <section class="section">
    <div class="wrap row" style="align-items:start">
      <div class="c-label"><div class="pair" style="max-width:360px"><span aria-hidden="true"></span><img src="assets/portrait-square.jpg" alt="Alice Acland"></div></div>
      <div class="c-main stack">
        <p class="t-sub">{t(A['intro'])}</p>
        <div class="stack measure" style="gap:0.8em">{paras}</div>
        {facts(A['cv'])}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="ex-h">
    <div class="wrap row">
      <div class="c-label"></div>
      <div class="c-main stack" style="gap:20px">
        <h2 class="t-sub" id="ex-h">{t(A['example_heading'])}</h2>
        <p class="measure">{t(A['example_text'])}</p>
        <a class="t-detail link" href="{attr(A['example_link'])}">Read the set-up guide</a>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="hw-h">
    <div class="wrap stack">
      <div class="row">
        <div class="c-label"></div>
        <h2 class="c-main t-sub" id="hw-h">{t(A['principles_heading'])}</h2>
      </div>
      <div class="who">{pr}</div>
    </div>
  </section>
</main>
""" + footer()


def writing(posts):
    W = C["writing"]
    app = "\n".join(f'        <li><a href="{attr(l)}"><span class="t-detail muted">{t(k)}</span><span class="t">{t(ti)}</span></a></li>'
                    for k, ti, l in W["appearances"])
    return head(f"Writing | {S['name']}", "Writing from The Art Intelligence newsletter on AI, technology and the art market.") + header("writing") + f"""
<main>
  <section class="intro-page">
    <div class="wrap row">
      <div class="c-label"></div>
      <div class="c-main stack">
        <h1 class="t-display">{t(W['headline'])}</h1>
        <p class="measure">{t(W['intro'])}</p>
        <div><a class="cta" href="{attr(S['substack'])}">Subscribe on Substack</a></div>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="wrap row">
      <span class="c-label t-detail rowlabel">Latest posts</span>
      <ul class="c-main posts">
{post_list(posts)}
      </ul>
    </div>
  </section>
  <section class="section">
    <div class="wrap row">
      <span class="c-label t-detail rowlabel">Appearances</span>
      <ul class="c-main posts">
{app}
      </ul>
    </div>
  </section>
</main>
""" + footer()


# ---------------------------------------------------------------- build
def main():
    posts = filtered(fetch_posts())
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for folder, exts in (("assets", {".css", ".png", ".jpg", ".jpeg", ".svg"}),
                         ("fonts", {".woff2", ".woff"})):
        src = ROOT / folder
        if src.exists():
            shutil.copytree(src, OUT / folder)
        else:  # files uploaded without their folder: gather them from the top level
            (OUT / folder).mkdir()
            for f in ROOT.iterdir():
                if f.is_file() and f.suffix.lower() in exts:
                    shutil.copy(f, OUT / folder / f.name)
    for name, page in [("index.html", home(posts)), ("services.html", services()),
                       ("about.html", about()), ("writing.html", writing(posts))]:
        (OUT / name).write_text(page, encoding="utf-8")
    if (ROOT / "CNAME").exists():
        shutil.copy(ROOT / "CNAME", OUT / "CNAME")
    print(f"Built {len(list(OUT.glob('*.html')))} pages into _site/")


if __name__ == "__main__":
    main()
