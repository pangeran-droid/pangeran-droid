#!/usr/bin/env python3
"""
Kali-Linux-terminal-styled neofetch profile SVG generator.

Same engine as the original script, but wrapped in a dark terminal window
(title bar + traffic-light dots) and recolored to match the classic
Kali look: red "user@host" header/prompt, cyan/blue field values,
light-blue ASCII art, navy window background.

Env vars:
  GITHUB_LOGIN   - github username to fetch stats for (required)
  GITHUB_TOKEN   - token with at least public read access (required for live stats)
  AVATAR_PATH    - optional explicit path to an avatar image
  OUT_PATH       - output svg path (default: profile.svg)
"""

import os
import sys
import random
import glob
from xml.sax.saxutils import escape as xml_escape

random.seed()

LOGIN = os.environ.get("GITHUB_LOGIN", "kali")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_PATH = os.environ.get("OUT_PATH", "assets/profile.svg")

# ---------------------------------------------------------------------------
# Field list shown on the right, neofetch-style.
# ---------------------------------------------------------------------------
PROFILE_FIELDS = [
    ("Role", "informatics student"),
    ("Focus", "junior web developer & cybersecurity enthusiast"),
    ("Stack.Frontend", "html, css, javascript"),
    ("Stack.Backend", "php, laravel, codeigniter"),
    ("Stack.Scripting", "python"),
    ("Stack.Database", "mysql"),
    ("Stack.Security", "burp suite"),
    ("Environment", "linux, git, github, vscode"),
    ("Interests", "cybersecurity"),
    ("Contact.GitHub", f"github.com/{LOGIN}"),
    ("Contact.Telegram", "t.me/pangeran1337"),
]

# ---- Kali color scheme -----------------------------------------------------
BG_COLOR = "#0b1120"          # terminal window background (deep navy)
TITLEBAR_COLOR = "#141c30"    # title bar strip
TITLE_TEXT_COLOR = "#7f8aa6"
ACCENT = "#5dc9f2"             # ASCII art color (light blue dots)
HEADER_COLOR = "#e8384f"       # bold red "login@login" header + prompt user/path
LABEL_COLOR = "#ffffff"        # bold field labels
VALUE_COLOR = "#5dc9f2"        # field values (cyan/blue)
PALETTE = ["#0b1120", "#e8384f", "#3ddc84", "#ffd166", "#4d8cff",
           "#b16cff", "#39e0d0", "#e8e8e8"]

PROMPT_COMMANDS = [
    "informatics student",
    "junior web developer",
    "cybersecurity enthusiast",
]
PROMPT_TYPE_SPEED = 0.08
PROMPT_DELETE_SPEED = 0.045
PROMPT_HOLD_TIME = 1.1
PROMPT_GAP_TIME = 0.4
PROMPT_CHAR_W = 9.0

RAMP = " .:-=+*#%@"

CELL_W = 8.4
CELL_H = 15.0
ART_COLS = 34

TITLEBAR_H = 34


def find_avatar():
    explicit = os.environ.get("AVATAR_PATH")
    if explicit and os.path.exists(explicit):
        return explicit
    for pattern in ("assets/avatar.*", "avatar.*", ".github/avatar.*"):
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def ascii_rows_from_image(path):
    from PIL import Image
    import numpy as np

    img = Image.open(path).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    arr = np.array(img).astype(np.float32)
    rgb = arr[..., :3]
    alpha = arr[..., 3]

    has_real_alpha = alpha.min() < 250
    if not has_real_alpha:
        m = max(2, int(side * 0.05))
        corners = np.concatenate([
            rgb[0:m, 0:m].reshape(-1, 3),
            rgb[0:m, -m:].reshape(-1, 3),
            rgb[-m:, 0:m].reshape(-1, 3),
            rgb[-m:, -m:].reshape(-1, 3),
        ], axis=0)
        bg_color = np.median(corners, axis=0)
        dist = np.sqrt(((rgb - bg_color) ** 2).sum(axis=-1))
        alpha = np.clip((dist - 42.0) * 6.0, 0, 255)

    rows = max(1, round(ART_COLS * (CELL_W / CELL_H)))

    mask_img = Image.fromarray(alpha.astype(np.uint8), mode="L").resize((ART_COLS, rows), Image.LANCZOS)
    gray_img = Image.fromarray(rgb.astype(np.uint8)).convert("L").resize((ART_COLS, rows), Image.LANCZOS)
    mask_px = mask_img.load()
    gray_px = gray_img.load()

    out_rows = []
    for y in range(rows):
        line = []
        for x in range(ART_COLS):
            fg = mask_px[x, y] / 255.0
            if fg < 0.22:
                line.append(" ")
                continue
            lum = gray_px[x, y] / 255.0
            idx = min(len(RAMP) - 2, int(lum * (len(RAMP) - 1)))
            line.append(RAMP[idx])
        out_rows.append("".join(line))
    return out_rows


def ascii_rows_dragon():
    """Procedural Kali-dragon-ish silhouette (stylized, dotted) when no
    avatar is provided — echoes the curled-tail dragon look of the
    reference screenshot using the character ramp for shading."""
    rows_n = max(1, round(ART_COLS * (CELL_W / CELL_H)))
    mid_chars = ":;."

    def in_dragon(x, y):
        nx = (x - ART_COLS * 0.42) / (ART_COLS / 2)
        ny = (y - rows_n * 0.5) / (rows_n / 2)
        # a loose spiral/curl shape reminiscent of the Kali dragon curve
        r = (nx ** 2 + ny ** 2) ** 0.5
        theta = (nx * 3.4 + ny * 2.1)
        spiral = abs((r * 5.0 - theta) % 2.0 - 1.0) < 0.22
        body = r < 0.9
        return spiral and body

    out_rows = []
    for y in range(rows_n):
        line = []
        for x in range(ART_COLS):
            if in_dragon(x, y):
                if random.random() < 0.12:
                    line.append(" ")
                else:
                    line.append(random.choice(mid_chars))
            else:
                line.append(" ")
        out_rows.append("".join(line))
    return out_rows


def build_prompt_typing_svg(commands, x, y):
    durations = []
    for cmd in commands:
        n = max(1, len(cmd))
        durations.append(n * PROMPT_TYPE_SPEED + PROMPT_HOLD_TIME + n * PROMPT_DELETE_SPEED + PROMPT_GAP_TIME)
    total = sum(durations)

    max_w = max(len(c) for c in commands) * PROMPT_CHAR_W

    keyframes_css = []
    cursor_stops = []
    groups_svg = []
    t = 0.0
    for i, cmd in enumerate(commands):
        n = max(1, len(cmd))
        full_w = n * PROMPT_CHAR_W
        type_dur = n * PROMPT_TYPE_SPEED
        delete_dur = n * PROMPT_DELETE_SPEED

        t_start = t
        t_type_end = t_start + type_dur
        t_hold_end = t_type_end + PROMPT_HOLD_TIME
        t_delete_end = t_hold_end + delete_dur
        t = t_delete_end + PROMPT_GAP_TIME

        def pct(sec):
            return round(max(0.0, min(100.0, sec / total * 100)), 3)

        stops = [
            (0, 0, "steps(1, jump-end)"),
            (pct(t_start), 0, f"steps({n}, jump-end)"),
            (pct(t_type_end), full_w, "steps(1, jump-end)"),
            (pct(t_hold_end), full_w, f"steps({n}, jump-end)"),
            (pct(t_delete_end), 0, "steps(1, jump-end)"),
            (100, 0, "steps(1, jump-end)"),
        ]
        seen = []
        for p, w, tf in stops:
            if seen and seen[-1][0] == p:
                seen[-1] = (p, w, tf)
            else:
                seen.append((p, w, tf))

        body = " ".join(
            f"{p}% {{ width: {w:.1f}px; animation-timing-function: {tf}; }}" for p, w, tf in seen
        )
        keyframes_css.append(f"@keyframes promptClip{i} {{ {body} }}")
        cursor_stops.extend(seen)

        groups_svg.append(f'''
      <clipPath id="promptClip{i}">
        <rect x="{x}" y="{y-14}" width="{full_w:.1f}" height="20" class="promptClipRect{i}" />
      </clipPath>''')

    text_svg = []
    for i, cmd in enumerate(commands):
        full_w = max(1, len(cmd)) * PROMPT_CHAR_W
        text_svg.append(
            f'\n      <text x="{x}" y="{y}" class="promptcmd" clip-path="url(#promptClip{i})" '
            f'textLength="{full_w:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{xml_escape(cmd)}</text>'
        )

    clip_anim_css = "\n".join(
        f".promptClipRect{i} {{ animation: promptClip{i} {total:.3f}s infinite; }}"
        for i in range(len(commands))
    )

    cursor_body = " ".join(
        f"{p}% {{ transform: translateX({w:.1f}px); animation-timing-function: {tf}; }}"
        for p, w, tf in cursor_stops
    )
    cursor_css = (
        f"@keyframes promptCursorMove {{ {cursor_body} }}\n      "
        f".promptcursor {{ animation: promptCursorMove {total:.3f}s infinite, blink 1s steps(1) infinite; }}"
    )

    cursor_svg = f'<rect x="{x:.1f}" y="{y-14:.1f}" width="8" height="16" class="promptcursor" />'

    style = "\n      ".join(keyframes_css) + "\n      " + clip_anim_css + "\n      " + cursor_css
    defs = "".join(groups_svg)
    return style, defs, "".join(text_svg), cursor_svg, max_w


def fetch_github_stats(login, token):
    stats = {
        "repos": "N/A", "stars": "N/A", "followers": "N/A",
        "contributions": "N/A", "top_languages": "N/A",
    }
    if not token:
        return stats
    try:
        import requests
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        user_resp = requests.get(f"https://api.github.com/users/{login}", headers=headers, timeout=15)
        user_resp.raise_for_status()
        user = user_resp.json()
        stats["followers"] = str(user.get("followers", "N/A"))
        stats["repos"] = str(user.get("public_repos", "N/A"))

        repos_resp = requests.get(
            f"https://api.github.com/users/{login}/repos?per_page=100&type=owner",
            headers=headers, timeout=15,
        )
        repos_resp.raise_for_status()
        repos = repos_resp.json()
        stats["stars"] = str(sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork")))

        lang_count = {}
        for r in repos:
            lang = r.get("language")
            if lang:
                lang_count[lang] = lang_count.get(lang, 0) + 1
        top_langs = sorted(lang_count, key=lang_count.get, reverse=True)[:4]
        stats["top_languages"] = ", ".join(top_langs) if top_langs else "N/A"
    except Exception as e:
        print(f"warning: failed to fetch live stats: {e}", file=sys.stderr)
    return stats


def build_svg(art_rows, fields):
    PAD = 34
    ART_W = ART_COLS * CELL_W
    ART_H = len(art_rows) * CELL_H
    GAP = 46
    FIELD_LINE_H = 22
    HEADER_H = 26
    RULE_GAP = 10
    SWATCH = 20
    SWATCH_GAP = 8
    PROMPT_H = 62

    info_x = PAD + ART_W + GAP
    header_y = TITLEBAR_H + PAD + HEADER_H
    rule_y = header_y + RULE_GAP
    fields_start_y = rule_y + 30

    fields_h = len(fields) * FIELD_LINE_H
    swatch_y = fields_start_y + fields_h + 14
    info_bottom = swatch_y + SWATCH + 10

    ART_OFFSET_Y = -14
  
    art_top = fields_start_y +  ART_OFFSET_Y
    art_bottom = art_top + ART_H
    content_bottom = max(info_bottom, art_bottom)

    prompt_y = content_bottom + 40
    H = prompt_y + PROMPT_H + 20
    header_text = f"{LOGIN}@github"
    rule_len = max(len(header_text) + 2, ART_COLS)
    W = info_x + max(360, len(max([f"{k}: {v}" for k, v in fields], key=len)) * 8.2) + PAD

    art_lines = []
    for i, row in enumerate(art_rows):
        y = art_top + i * CELL_H + CELL_H * 0.8
        delay = round(i * 0.045, 3)
        art_lines.append(
            f'\n      <text x="{PAD}" y="{y:.1f}" class="art fadein" '
            f'style="animation-delay:{delay}s" textLength="{ART_W:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{xml_escape(row)}</text>'
        )
    art_svg = "".join(art_lines)

    header_svg = (
        f'<text x="{info_x}" y="{header_y}" class="header">{xml_escape(header_text)}</text>'
        f'\n  <line x1="{info_x}" y1="{rule_y}" x2="{info_x + rule_len * 9.4}" y2="{rule_y}" class="rule" />'
    )

    field_lines = []
    for i, (label, value) in enumerate(fields):
        y = fields_start_y + i * FIELD_LINE_H
        delay = 0.5 + i * 0.06
        field_lines.append(
            f'\n      <text x="{info_x}" y="{y}" class="fieldline typewriter" style="animation-delay:{delay:.2f}s">'
            f'<tspan class="label">{xml_escape(label)}:</tspan> '
            f'<tspan class="value">{xml_escape(value)}</tspan></text>'
        )
    fields_svg = "".join(field_lines)

    swatch_lines = []
    for i, color in enumerate(PALETTE):
        x = info_x + i * (SWATCH + SWATCH_GAP)
        delay = 0.5 + len(fields) * 0.06 + i * 0.05
        swatch_lines.append(
            f'\n      <rect x="{x:.1f}" y="{swatch_y:.1f}" width="{SWATCH}" height="{SWATCH}" rx="3" '
            f'fill="{color}" stroke="#2a3350" stroke-width="1" class="swatch" style="animation-delay:{delay:.2f}s" />'
        )
    swatch_svg = "".join(swatch_lines)

    prompt_line1 = f"┌──({LOGIN}@github-[~]"
    prompt_line2 = "└─$ "

    typed_x = PAD + (len(prompt_line2) + 1) * 9.0
    typed_y = prompt_y + 24
    prompt_style, prompt_defs, prompt_cmd_svg, prompt_cursor_svg, cmd_max_w = build_prompt_typing_svg(
        PROMPT_COMMANDS, typed_x, typed_y
    )

    prompt_svg = (
        f'<text x="{PAD}" y="{prompt_y}" class="prompt">{xml_escape(prompt_line1)}</text>'
        f'\n  <text x="{PAD}" y="{typed_y}" class="prompt">{xml_escape(prompt_line2)}</text>'
        f'\n  {prompt_cmd_svg}'
        f'\n  {prompt_cursor_svg}'
    )

    W = max(W, typed_x + cmd_max_w + PAD)

    # --- window chrome (title bar + traffic-light dots + title label) -----
    title_text = f"{LOGIN}@github: ~"
    chrome_svg = f'''
  <rect x="0" y="0" width="{W:.0f}" height="{H:.0f}" rx="10" fill="{BG_COLOR}" />
  <path d="M0,10 a10,10 0 0 1 10,-10 h{W-20:.0f} a10,10 0 0 1 10,10 v{TITLEBAR_H-10:.0f} h-{W:.0f} z"
        fill="{TITLEBAR_COLOR}" />
  <circle cx="24" cy="{TITLEBAR_H/2:.0f}" r="6" fill="#ff5f57" />
  <circle cx="46" cy="{TITLEBAR_H/2:.0f}" r="6" fill="#febc2e" />
  <circle cx="68" cy="{TITLEBAR_H/2:.0f}" r="6" fill="#28c840" />
  <text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 5:.0f}" text-anchor="middle" class="titletext">{xml_escape(title_text)}</text>
  <line x1="0" y1="{TITLEBAR_H}" x2="{W:.0f}" y2="{TITLEBAR_H}" stroke="#1f2740" stroke-width="1" />'''

    return f'''<svg width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .art {{ font-family: 'Courier New', monospace; font-size: {CELL_H*0.82:.1f}px; fill: {ACCENT}; white-space: pre; }}
      .header {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; fill: {HEADER_COLOR}; }}
      .rule {{ stroke: {HEADER_COLOR}; stroke-width: 1.4; opacity: 0.85; }}
      .fieldline {{ font-family: 'Courier New', monospace; font-size: 13px; }}
      .label {{ fill: {LABEL_COLOR}; font-weight: bold; }}
      .value {{ fill: {VALUE_COLOR}; }}
      .prompt {{ font-family: 'Courier New', monospace; font-size: 15px; font-weight: bold; fill: {HEADER_COLOR}; }}
      .titletext {{ font-family: 'Courier New', monospace; font-size: 13px; fill: {TITLE_TEXT_COLOR}; }}
      .promptcmd {{ font-family: 'Courier New', monospace; font-size: 15px; fill: {VALUE_COLOR}; white-space: pre; }}
      .promptcursor {{ fill: {ACCENT}; }}
      {prompt_style}
      .fadein {{ animation-name: reveal; animation-duration: 0.35s; animation-fill-mode: forwards; animation-timing-function: steps(1); }}
      .typewriter {{ animation-name: reveal; animation-duration: 0.4s; animation-fill-mode: forwards; animation-timing-function: steps(1); }}
      .swatch {{ animation-name: revealSwatch; animation-duration: 0.35s; animation-fill-mode: forwards; animation-timing-function: steps(1); }}
      @keyframes reveal {{ 0% {{ opacity: 0; }} 1%, 100% {{ opacity: 1; }} }}
      @keyframes revealSwatch {{ 0% {{ opacity: 0; }} 1%, 100% {{ opacity: 1; }} }}
      @keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
    </style>
    {prompt_defs}
  </defs>
  {chrome_svg}

  {art_svg}

  {header_svg}
  {fields_svg}
  {swatch_svg}

  {prompt_svg}
</svg>
'''


def main():
    avatar_path = find_avatar()
    if avatar_path:
        print(f"using avatar image: {avatar_path}")
        art_rows = ascii_rows_from_image(avatar_path)
    else:
        print("no avatar found, using procedural Kali-dragon placeholder art")
        art_rows = ascii_rows_dragon()

    stats = fetch_github_stats(LOGIN, TOKEN)

    fields = list(PROFILE_FIELDS)
    fields.extend([
        ("GitHub.Repos", stats["repos"]),
        ("GitHub.Stars", stats["stars"]),
        ("GitHub.Followers", stats["followers"]),
        ("GitHub.Languages", stats["top_languages"]),
    ])

    svg = build_svg(art_rows, fields)
    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
