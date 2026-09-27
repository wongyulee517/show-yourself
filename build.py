#!/usr/bin/env python3
"""Build the academic profile site.

Reads content/*.yaml, renders templates/index.html with Jinja2, copies static/
into dist/. Run `python3 build.py --serve` to build and preview locally.
"""

from __future__ import annotations

import argparse
import datetime
import http.server
import shutil
import sys
from collections import OrderedDict
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from themes import THEMES, resolve_palette

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DEFAULT_OUT = ROOT / "dist"

# Inline stroke icons used by the sidebar links. Keys are the `icon` values in
# content/links.yaml. Unknown names fall back to "link".
_SVG_OPEN = (
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
)
ICONS: dict[str, str] = {
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 10v7M8 7v.5M12 17v-4a2 2 0 0 1 4 0v4M12 10v7"/>',
    "cv": '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
    "scholar": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>',
    "github": '<path d="M16 22v-3.5a3 3 0 0 0-.8-2.3c2.7-.3 5.5-1.3 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.3 4.3 0 0 0-.1-3.2s-1-.3-3.4 1.3a11.7 11.7 0 0 0-6 0C7.5 3.5 6.5 3.8 6.5 3.8a4.3 4.3 0 0 0-.1 3.2A4.6 4.6 0 0 0 5 10.2c0 4.7 2.8 5.7 5.5 6a3 3 0 0 0-.8 2.3V22"/><path d="M9 20c-4 1.5-4-2-6-2"/>',
    "email": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "orcid": '<circle cx="12" cy="12" r="9"/><path d="M8.5 9.5v6M8.5 7v.5M11.5 9.5h2.5a3 3 0 0 1 0 6h-2.5z"/>',
    "twitter": '<path d="M4 4l16 16M20 4L4 20"/>',
    "bluesky": '<path d="M12 10c-1.5-3-5-6.5-8-6.5-1 0-1 1.5-1 3 0 4 2 7 6 7.5-3 .5-4 2-3 4s5 1 6-3c1 4 5 5 6 3s0-3.5-3-4c4-.5 6-3.5 6-7.5 0-1.5 0-3-1-3-3 0-6.5 3.5-8 6.5z"/>',
    "website": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "semantic-scholar": '<path d="M4 6h16M4 12h10M4 18h16"/><path d="M17 10l3 2-3 2"/>',
    "dblp": '<path d="M5 4h6v16H5zM13 8h6v12h-6z"/>',
    "youtube": '<rect x="3" y="6" width="18" height="12" rx="3"/><path d="M10 9.5v5l4.5-2.5z"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1.5 1.5"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1.5-1.5"/>',
}


def icon(name: str | None) -> Markup:
    body = ICONS.get((name or "link").strip().lower(), ICONS["link"])
    return Markup(_SVG_OPEN + body + "</svg>")


def load_yaml(name: str, default):
    path = CONTENT / f"{name}.yaml"
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def format_authors(authors: list[str], aliases: list[str]) -> Markup:
    """Comma-join authors, wrapping any alias of the site owner in <strong>."""
    alias_set = {a.strip() for a in aliases if a}
    parts = []
    for author in authors:
        text = escape(author)
        if author.strip() in alias_set:
            text = Markup("<strong>") + text + Markup("</strong>")
        parts.append(text)
    return Markup(", ").join(parts)


def group_by_year(pubs: list[dict]) -> list[tuple[int | str, list[dict]]]:
    """Newest year first; within a year, keep the order written in YAML."""
    ordered = sorted(pubs, key=lambda p: _year_key(p.get("year")), reverse=True)
    groups: "OrderedDict[int | str, list[dict]]" = OrderedDict()
    for pub in ordered:
        groups.setdefault(pub.get("year", "n.d."), []).append(pub)
    return list(groups.items())


def _year_key(year) -> int:
    try:
        return int(year)
    except (TypeError, ValueError):
        return -1


def build_nav(profile: dict, show_teaching: bool) -> list[dict]:
    """Top tabs: one per generated page, then any extra links from profile.yaml."""
    labels = profile.get("nav_labels") or {}
    nav = [
        {"label": labels.get("home", "About"), "href": "index.html"},
        {"label": labels.get("publications", "Publications"), "href": "publications.html"},
    ]
    if show_teaching:
        nav.append({"label": labels.get("teaching", "Teaching"), "href": "teaching.html"})
    nav.extend(profile.get("nav_extra") or [])
    return nav


def build(out_dir: Path, theme: str | None = None) -> Path:
    profile = load_yaml("profile", {})
    palette = resolve_palette(profile, theme)
    links = load_yaml("links", [])
    career = load_yaml("career", [])
    publications = load_yaml("publications", [])
    teaching = load_yaml("teaching", [])

    sections = profile.get("sections") or {}
    show_teaching = bool(sections.get("teaching", True)) and bool(teaching)

    aliases = profile.get("author_aliases") or [profile.get("name", "")]
    for pub in publications:
        pub["authors_html"] = format_authors(pub.get("authors", []), aliases)
        pub["selected"] = bool(pub.get("selected", False))
        pub["links"] = pub.get("links") or {}

    by_year = group_by_year(publications)
    newest_first = [pub for _, pubs in by_year for pub in pubs]
    selected = [p for p in newest_first if p["selected"]]
    # Home page shows the selected papers; with none marked, the newest few.
    highlights = selected or newest_first[: int(profile.get("recent_count", 3))]

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["icon"] = icon

    context = dict(
        profile=profile,
        palette=palette,
        links=links,
        career=career,
        publications=publications,
        publications_by_year=by_year,
        selected=selected,
        highlights=highlights,
        teaching=teaching,
        nav=build_nav(profile, show_teaching),
        year=datetime.date.today().year,
    )

    pages = [
        ("index.html", None),
        ("publications.html", "Publications"),
    ]
    if show_teaching:
        pages.append(("teaching.html", "Teaching"))

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    if STATIC.exists():
        shutil.copytree(STATIC, out_dir, dirs_exist_ok=True)

    for filename, title in pages:
        html = env.get_template(filename).render(
            current_page=filename, page_title=title, **context
        )
        (out_dir / filename).write_text(html, encoding="utf-8")
    return out_dir


def serve(directory: Path, port: int) -> None:
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *a, directory=str(directory), **kw
    )
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {directory} at http://127.0.0.1:{port}/  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (default: dist/)")
    parser.add_argument("--serve", action="store_true", help="build, then serve the output locally")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--theme", choices=sorted(THEMES), default=None,
        help="preview with this theme instead of the one in profile.yaml",
    )
    args = parser.parse_args(argv)

    out = build(args.out, theme=args.theme)
    print(f"Built {sorted(p.name for p in out.glob('*.html'))} in {out}")
    if args.serve:
        serve(out, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
