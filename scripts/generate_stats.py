#!/usr/bin/env python3
"""
Animated GitHub Top Languages Card & Pie Chart SVG Generator.

Env vars:
  GITHUB_LOGIN   - GitHub username to fetch stats for (default: pangeran-droid)
  GITHUB_TOKEN   - Token with public read access (optional, avoids rate limit)
  OUT_CARD       - Output SVG path for bar card (default: assets/languages-card.svg)
  OUT_PIE        - Output SVG path for pie chart (default: assets/languages-pie.svg)
"""

import json
import os
import sys
import urllib.request

LOGIN = os.environ.get("GITHUB_LOGIN", "pangeran-droid")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_CARD = os.environ.get("OUT_CARD", "assets/languages-card.svg")
OUT_PIE = os.environ.get("OUT_PIE", "assets/languages-pie.svg")
TOP_N = 6

# Official GitHub Linguist colors JSON dataset
GITHUB_COLORS_URL = "https://raw.githubusercontent.com/ozh/github-colors/master/colors.json"
FALLBACK_COLORS = ["#5dc9f2", "#3ddc84", "#ffd166", "#e8384f", "#b16cff", "#39e0d0"]

# Kali-matched dark palette (harmonizes with profile.svg)
BG_COLOR = "#0b1120"
TRACK_COLOR = "#141c30"
BORDER_IDLE = "#1f2740"
BORDER_GLOW = "#5dc9f2"
TITLE_COLOR = "#5dc9f2"
TEXT_PRIMARY = "#e8e8e8"
TEXT_MUTED = "#7f8aa6"


def github_request(url: str, use_token: bool = True):
    """Perform an HTTP GET request and return (parsed_json, response_headers)."""
    headers = {
        "User-Agent": "GitHub-Stats-SVG-Generator",
        "Accept": "application/vnd.github+json",
    }
    if use_token and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data, resp.headers


def get_next_link(link_header: str | None) -> str | None:
    """Parse GitHub's RFC 5988 Link header for rel="next"."""
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) == 2 and section[1].strip() == 'rel="next"':
            return section[0].strip()[1:-1]
    return None


def fetch_official_lang_colors() -> dict:
    """Fetch official GitHub Linguist language colors dynamically."""
    try:
        data, _ = github_request(GITHUB_COLORS_URL, use_token=False)
        return {
            lang: info["color"]
            for lang, info in data.items()
            if isinstance(info, dict) and info.get("color")
        }
    except Exception as e:
        print(f"warning: failed to fetch official colors, using fallback: {e}", file=sys.stderr)
        return {}


def fetch_language_stats(login: str, lang_colors: dict):
    """Aggregate byte counts per language across all non-fork owned repositories."""
    repos = []
    next_url = f"https://api.github.com/users/{login}/repos?per_page=100&type=owner"
    seen_urls = set()

    while next_url:
        if next_url in seen_urls:
            break
        seen_urls.add(next_url)
        batch, headers = github_request(next_url)
        if not isinstance(batch, list):
            break
        repos.extend(batch)
        next_url = get_next_link(headers.get("Link"))

    totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        repo_langs, _ = github_request(lang_url)
        for lang, byte_count in repo_langs.items():
            totals[lang] = totals.get(lang, 0) + byte_count

    if not totals:
        raise RuntimeError(f"No language data found for user '{login}'.")

    sorted_langs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    top_langs = sorted_langs[:TOP_N]
    total_bytes = sum(count for _, count in top_langs)

    results = []
    for idx, (lang, count) in enumerate(top_langs):
        pct = round((count / total_bytes) * 100, 2)
        color = lang_colors.get(lang, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])
        results.append({"name": lang, "bytes": count, "pct": pct, "color": color})

    # Ensure percentages sum cleanly to 100.0%
    diff = round(100.0 - sum(item["pct"] for item in results), 2)
    if results:
        results[0]["pct"] = round(results[0]["pct"] + diff, 2)

    return results


def generate_card_svg(langs):
    """Generate the animated Top Languages progress bar card."""
    width = 360
    height = 215
    bar_x = 24
    bar_y = 54
    bar_width = width - 48
    bar_height = 10

    bar_segments = []
    current_x = 0.0
    for lang in langs:
        seg_w = (lang["pct"] / 100.0) * bar_width
        bar_segments.append(
            f'<rect x="{current_x:.2f}" y="0" width="{seg_w:.2f}" height="{bar_height}" fill="{lang["color"]}" />'
        )
        current_x += seg_w

    legend_items = []
    start_y = 86
    row_gap = 38
    col_width = (width - 48) / 2

    for idx, lang in enumerate(langs):
        col = idx % 2
        row = idx // 2
        lx = 24 + col * col_width
        ly = start_y + row * row_gap
        delay = round(0.15 + idx * 0.1, 2)

        legend_items.append(f"""
  <g transform="translate({lx:.1f}, {ly})">
    <g class="fade-up" style="animation-delay: {delay}s;">
      <circle cx="6" cy="7" r="5" fill="{lang['color']}" />
      <text x="18" y="11" fill="{TEXT_PRIMARY}" font-family="'Courier New', monospace" font-size="12.5" font-weight="bold">{lang['name']}</text>
      <text x="18" y="25" fill="{TEXT_MUTED}" font-family="'Courier New', monospace" font-size="11">{lang['pct']:.1f}%</text>
    </g>
  </g>""")

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="progress-clip">
      <rect x="0" y="0" width="{bar_width}" height="{bar_height}" rx="5" />
    </clipPath>
    <style>
      @keyframes fadeUp {{
        0% {{ opacity: 0; transform: translateY(6px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
      }}
      @keyframes growBar {{
        0% {{ transform: scaleX(0); }}
        100% {{ transform: scaleX(1); }}
      }}
      @keyframes borderGlow {{
        0%, 100% {{ stroke: {BORDER_IDLE}; }}
        50% {{ stroke: {BORDER_GLOW}; }}
      }}
      .card-border {{
        animation: borderGlow 6s ease-in-out infinite;
      }}
      .bar-anim {{
        transform-box: fill-box;
        transform-origin: left center;
        animation: growBar 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards;
      }}
      .fade-up {{
        opacity: 0;
        animation: fadeUp 0.55s ease-out forwards;
      }}
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG_COLOR}" stroke="{BORDER_IDLE}" class="card-border" />
  <text x="24" y="34" fill="{TITLE_COLOR}" font-family="'Courier New', monospace" font-size="15" font-weight="bold">Most Used Languages</text>

  <g transform="translate({bar_x}, {bar_y})">
    <rect x="0" y="0" width="{bar_width}" height="{bar_height}" rx="5" fill="{TRACK_COLOR}" />
    <g clip-path="url(#progress-clip)">
      <g class="bar-anim">
        {''.join(bar_segments)}
      </g>
    </g>
  </g>

  {''.join(legend_items)}
</svg>
"""


def generate_pie_svg(langs):
    """Generate the animated Donut/Pie chart card."""
    width = 360
    height = 215
    cx = 96
    cy = 122
    radius = 52
    stroke_width = 20
    circumference = 2 * 3.14159265 * radius

    keyframes_css = []
    slices = []
    accumulated_pct = 0.0

    for idx, lang in enumerate(langs):
        slice_len = (lang["pct"] / 100.0) * circumference
        rotation = -90 + (accumulated_pct / 100.0) * 360.0
        delay = round(idx * 0.12, 2)
        anim_name = f"sliceDraw_{idx}"

        keyframes_css.append(f"""
      @keyframes {anim_name} {{
        0% {{ stroke-dasharray: 0 {circumference:.2f}; }}
        100% {{ stroke-dasharray: {slice_len:.2f} {circumference:.2f}; }}
      }}""")

        slices.append(f"""
    <g transform="rotate({rotation:.2f} {cx} {cy})">
      <circle
        cx="{cx}" cy="{cy}" r="{radius}"
        fill="transparent"
        stroke="{lang['color']}"
        stroke-width="{stroke_width}"
        stroke-dasharray="0 {circumference:.2f}"
        style="animation: {anim_name} 0.85s cubic-bezier(0.22, 1, 0.36, 1) {delay}s forwards;"
      />
    </g>""")
        accumulated_pct += lang["pct"]

    legend_items = []
    start_y = 58
    item_gap = 24

    for idx, lang in enumerate(langs):
        ly = start_y + idx * item_gap
        delay = round(0.15 + idx * 0.09, 2)
        legend_items.append(f"""
  <g transform="translate(182, {ly})">
    <g class="fade-in" style="animation-delay: {delay}s;">
      <rect x="0" y="1" width="10" height="10" rx="3" fill="{lang['color']}" />
      <text x="16" y="10" fill="{TEXT_PRIMARY}" font-family="'Courier New', monospace" font-size="11.5" font-weight="bold">{lang['name']}</text>
      <text x="154" y="10" text-anchor="end" fill="{TEXT_MUTED}" font-family="'Courier New', monospace" font-size="11">{lang['pct']:.1f}%</text>
    </g>
  </g>""")

    top_lang_name = langs[0]["name"] if langs else ""
    top_lang_pct = f"{langs[0]['pct']:.0f}%" if langs else ""

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @keyframes fadeIn {{
        0% {{ opacity: 0; transform: translateX(6px); }}
        100% {{ opacity: 1; transform: translateX(0); }}
      }}
      @keyframes borderGlow {{
        0%, 100% {{ stroke: {BORDER_IDLE}; }}
        50% {{ stroke: {BORDER_GLOW}; }}
      }}
      {''.join(keyframes_css)}
      .card-border {{
        animation: borderGlow 6s ease-in-out infinite;
      }}
      .fade-in {{
        opacity: 0;
        animation: fadeIn 0.55s ease-out forwards;
      }}
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG_COLOR}" stroke="{BORDER_IDLE}" class="card-border" />
  <text x="24" y="34" fill="{TITLE_COLOR}" font-family="'Courier New', monospace" font-size="15" font-weight="bold">Language Distribution</text>

  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="transparent" stroke="{TRACK_COLOR}" stroke-width="{stroke_width}" />
  {''.join(slices)}

  <text x="{cx}" y="{cy - 2}" text-anchor="middle" fill="{TEXT_PRIMARY}" font-family="'Courier New', monospace" font-size="13" font-weight="bold">{top_lang_pct}</text>
  <text x="{cx}" y="{cy + 13}" text-anchor="middle" fill="{TEXT_MUTED}" font-family="'Courier New', monospace" font-size="10">{top_lang_name}</text>

  {''.join(legend_items)}
</svg>
"""


def main():
    official_colors = fetch_official_lang_colors()
    stats = fetch_language_stats(LOGIN, official_colors)

    os.makedirs(os.path.dirname(OUT_CARD) or ".", exist_ok=True)
    with open(OUT_CARD, "w", encoding="utf-8") as f:
        f.write(generate_card_svg(stats))
    print(f"wrote {OUT_CARD}")

    os.makedirs(os.path.dirname(OUT_PIE) or ".", exist_ok=True)
    with open(OUT_PIE, "w", encoding="utf-8") as f:
        f.write(generate_pie_svg(stats))
    print(f"wrote {OUT_PIE}")


if __name__ == "__main__":
    main()