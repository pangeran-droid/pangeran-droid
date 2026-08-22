#!/usr/bin/env python3
"""
Generate a real Kali Linux / neofetch-style animated SVG profile card.

Features:
  - character-based ASCII art on the left
  - avatar background automatically removed
  - Kali-style dark terminal background
  - cyan ASCII art and terminal text
  - white labels + cyan values
  - 8-color terminal palette
  - animated field reveal
  - animated typing/deleting terminal prompt
  - blinking cursor
  - live GitHub statistics

Env vars:
  GITHUB_LOGIN   - github username to fetch stats for
  GITHUB_TOKEN   - token with at least public read access
  AVATAR_PATH    - optional explicit path to an avatar image
  OUT_PATH       - output svg path (default: assets/profile.svg)
"""

import os
import sys
import random
import glob
from xml.sax.saxutils import escape as xml_escape

random.seed()

LOGIN = os.environ.get("GITHUB_LOGIN", "pangeran-droid")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_PATH = os.environ.get("OUT_PATH", "assets/profile.svg")


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------

PROFILE_FIELDS = [
    ("Role", "informatics student"),
    ("Focus", "junior web developer & cybersecurity enthusiast"),
    ("Stack.Frontend", "html, css, javascript"),
    ("Stack.Backend", "php, laravel, codeigniter"),
    ("Stack.Scripting", "python"),
    ("Stack.Database", "mysql"),
    ("Environment", "linux, git, github, vscode"),
    ("Interests", "cybersecurity"),
    ("Contact.GitHub", f"github.com/{LOGIN}"),
    ("Contact.Telegram", "t.me/pangeran1337"),
]


# ---------------------------------------------------------------------------
# KALI / TERMINAL COLORS
# ---------------------------------------------------------------------------

ACCENT = "#00FFFF"
LABEL_COLOR = "#FFFFFF"
VALUE_COLOR = "#00FFFF"

PALETTE = [
    "#000000",
    "#FF0000",
    "#00FF00",
    "#FFFF00",
    "#0000FF",
    "#FF00FF",
    "#00FFFF",
    "#FFFFFF",
]


# ---------------------------------------------------------------------------
# TERMINAL PROMPT ANIMATION
# ---------------------------------------------------------------------------

PROMPT_COMMANDS = [
    "Informatics Student",
    "Junior Web Developer",
    "Cybersecurity Enthusiast",
]

PROMPT_TYPE_SPEED = 0.08
PROMPT_DELETE_SPEED = 0.045
PROMPT_HOLD_TIME = 1.1
PROMPT_GAP_TIME = 0.4
PROMPT_CHAR_W = 9.0


# ---------------------------------------------------------------------------
# ASCII ART
# ---------------------------------------------------------------------------

RAMP = " .`:-=+*cs#%@"

CELL_W = 8.4
CELL_H = 15.0
ART_COLS = 34


def find_avatar():
    explicit = os.environ.get("AVATAR_PATH")

    if explicit and os.path.exists(explicit):
        return explicit

    for pattern in (
        "assets/avatar.*",
        "avatar.*",
        ".github/avatar.*",
    ):
        matches = glob.glob(pattern)

        if matches:
            return matches[0]

    return None


def ascii_rows_from_image(path):
    """Convert avatar image into transparent ASCII art."""

    from PIL import Image
    import numpy as np

    img = Image.open(path).convert("RGBA")

    w, h = img.size

    side = min(w, h)

    left = (w - side) // 2
    top = (h - side) // 2

    img = img.crop(
        (
            left,
            top,
            left + side,
            top + side,
        )
    )

    arr = np.array(img).astype(np.float32)

    rgb = arr[..., :3]
    alpha = arr[..., 3]

    # ---------------------------------------------------------------
    # Detect whether image already has transparency
    # ---------------------------------------------------------------

    has_real_alpha = alpha.min() < 250

    if not has_real_alpha:

        m = max(
            2,
            int(side * 0.05),
        )

        corners = np.concatenate(
            [
                rgb[0:m, 0:m].reshape(-1, 3),
                rgb[0:m, -m:].reshape(-1, 3),
                rgb[-m:, 0:m].reshape(-1, 3),
                rgb[-m:, -m:].reshape(-1, 3),
            ],
            axis=0,
        )

        bg_color = np.median(
            corners,
            axis=0,
        )

        dist = np.sqrt(
            ((rgb - bg_color) ** 2).sum(axis=-1)
        )

        alpha = np.clip(
            (dist - 42.0) * 6.0,
            0,
            255,
        )

    # ---------------------------------------------------------------
    # Correct character-cell aspect ratio
    # ---------------------------------------------------------------

    rows = max(
        1,
        round(
            ART_COLS * (CELL_W / CELL_H)
        ),
    )

    mask_img = Image.fromarray(
        alpha.astype(np.uint8),
        mode="L",
    ).resize(
        (ART_COLS, rows),
        Image.LANCZOS,
    )

    gray_img = (
        Image.fromarray(
            rgb.astype(np.uint8)
        )
        .convert("L")
        .resize(
            (ART_COLS, rows),
            Image.LANCZOS,
        )
    )

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

            idx = min(
                len(RAMP) - 2,
                int(
                    lum * (len(RAMP) - 1)
                ),
            )

            line.append(RAMP[idx])

        out_rows.append(
            "".join(line)
        )

    return out_rows


def ascii_rows_placeholder():
    """Procedural fallback when no avatar exists."""

    rows_n = max(
        1,
        round(
            ART_COLS * (CELL_W / CELL_H)
        ),
    )

    mid_chars = "#*+=-:."

    def in_head_shoulders(x, y):

        nx = (
            x - ART_COLS / 2
        ) / (
            ART_COLS / 2
        )

        ny = (
            y - rows_n / 2
        ) / (
            rows_n / 2
        )

        # head
        hx = 0.0
        hy = -0.5
        hr = 0.36

        head = (
            (nx - hx) ** 2
            + (ny - hy) ** 2 * 1.15
        ) < hr ** 2

        # shoulders
        sx = 0.0
        sy = 0.55

        shoulders = (
            ny > 0.05
            and (
                ((nx - sx) ** 2) / (0.9 ** 2)
                + ((ny - sy) ** 2) / (0.8 ** 2)
                < 1.0
            )
        )

        return head or shoulders

    out_rows = []

    for y in range(rows_n):

        line = []

        for x in range(ART_COLS):

            if in_head_shoulders(x, y):

                if random.random() < 0.08:
                    line.append(" ")
                else:
                    line.append(
                        random.choice(mid_chars)
                    )

            else:
                line.append(" ")

        out_rows.append(
            "".join(line)
        )

    return out_rows


# ---------------------------------------------------------------------------
# TERMINAL TYPING ANIMATION
# ---------------------------------------------------------------------------

def build_prompt_typing_svg(commands, x, y):

    durations = []

    for cmd in commands:

        n = max(
            1,
            len(cmd),
        )

        durations.append(
            n * PROMPT_TYPE_SPEED
            + PROMPT_HOLD_TIME
            + n * PROMPT_DELETE_SPEED
            + PROMPT_GAP_TIME
        )

    total = sum(durations)

    max_w = (
        max(len(c) for c in commands)
        * PROMPT_CHAR_W
    )

    keyframes_css = []

    cursor_stops = []

    groups_svg = []

    t = 0.0

    for i, cmd in enumerate(commands):

        n = max(
            1,
            len(cmd),
        )

        full_w = (
            n * PROMPT_CHAR_W
        )

        type_dur = (
            n * PROMPT_TYPE_SPEED
        )

        delete_dur = (
            n * PROMPT_DELETE_SPEED
        )

        t_start = t

        t_type_end = (
            t_start + type_dur
        )

        t_hold_end = (
            t_type_end + PROMPT_HOLD_TIME
        )

        t_delete_end = (
            t_hold_end + delete_dur
        )

        t = (
            t_delete_end
            + PROMPT_GAP_TIME
        )

        def pct(sec):

            return round(
                max(
                    0.0,
                    min(
                        100.0,
                        sec / total * 100,
                    ),
                ),
                3,
            )

        stops = [
            (
                0,
                0,
                "steps(1, jump-end)",
            ),
            (
                pct(t_start),
                0,
                f"steps({n}, jump-end)",
            ),
            (
                pct(t_type_end),
                full_w,
                "steps(1, jump-end)",
            ),
            (
                pct(t_hold_end),
                full_w,
                f"steps({n}, jump-end)",
            ),
            (
                pct(t_delete_end),
                0,
                "steps(1, jump-end)",
            ),
            (
                100,
                0,
                "steps(1, jump-end)",
            ),
        ]

        seen = []

        for p, w, tf in stops:

            if seen and seen[-1][0] == p:

                seen[-1] = (
                    p,
                    w,
                    tf,
                )

            else:

                seen.append(
                    (
                        p,
                        w,
                        tf,
                    )
                )

        body = " ".join(
            f"{p}% {{ width: {w:.1f}px; "
            f"animation-timing-function: {tf}; }}"
            for p, w, tf in seen
        )

        keyframes_css.append(
            f"@keyframes promptClip{i} "
            f"{{ {body} }}"
        )

        cursor_stops.extend(
            seen
        )

        groups_svg.append(
            f'''
      <clipPath id="promptClip{i}">
        <rect
          x="{x}"
          y="{y-14}"
          width="{full_w:.1f}"
          height="20"
          class="promptClipRect{i}"
        />
      </clipPath>
'''
        )

    text_svg = []

    for i, cmd in enumerate(commands):

        full_w = (
            max(
                1,
                len(cmd),
            )
            * PROMPT_CHAR_W
        )

        text_svg.append(
            f'''
      <text
        x="{x}"
        y="{y}"
        class="promptcmd"
        clip-path="url(#promptClip{i})"
        textLength="{full_w:.1f}"
        lengthAdjust="spacingAndGlyphs"
        xml:space="preserve"
      >{xml_escape(cmd)}</text>
'''
        )

    clip_anim_css = "\n".join(
        f".promptClipRect{i} {{ "
        f"animation: promptClip{i} "
        f"{total:.3f}s infinite; }}"
        for i in range(len(commands))
    )

    cursor_body = " ".join(
        f"{p}% {{ "
        f"transform: translateX({w:.1f}px); "
        f"animation-timing-function: {tf}; }}"
        for p, w, tf in cursor_stops
    )

    cursor_css = (
        f"@keyframes promptCursorMove "
        f"{{ {cursor_body} }}\n"
        f".promptcursor {{ "
        f"animation: promptCursorMove "
        f"{total:.3f}s infinite, "
        f"blink 1s steps(1) infinite; }}"
    )

    cursor_svg = (
        f'<rect '
        f'x="{x:.1f}" '
        f'y="{y-14:.1f}" '
        f'width="8" '
        f'height="16" '
        f'class="promptcursor" />'
    )

    style = (
        "\n".join(keyframes_css)
        + "\n"
        + clip_anim_css
        + "\n"
        + cursor_css
    )

    defs = "".join(
        groups_svg
    )

    return (
        style,
        defs,
        "".join(text_svg),
        cursor_svg,
        max_w,
    )


# ---------------------------------------------------------------------------
# GITHUB API
# ---------------------------------------------------------------------------

def fetch_github_stats(login, token):

    stats = {
        "repos": "N/A",
        "stars": "N/A",
        "followers": "N/A",
        "contributions": "N/A",
        "top_languages": "N/A",
    }

    if not token:
        return stats

    try:

        import requests

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        # ---------------------------------------------------------------
        # User
        # ---------------------------------------------------------------

        user_resp = requests.get(
            f"https://api.github.com/users/{login}",
            headers=headers,
            timeout=15,
        )

        user_resp.raise_for_status()

        user = user_resp.json()

        stats["followers"] = str(
            user.get(
                "followers",
                "N/A",
            )
        )

        stats["repos"] = str(
            user.get(
                "public_repos",
                "N/A",
            )
        )

        # ---------------------------------------------------------------
        # Repositories
        # ---------------------------------------------------------------

        repos_resp = requests.get(
            f"https://api.github.com/users/{login}/repos"
            f"?per_page=100&type=owner",
            headers=headers,
            timeout=15,
        )

        repos_resp.raise_for_status()

        repos = repos_resp.json()

        stats["stars"] = str(
            sum(
                r.get(
                    "stargazers_count",
                    0,
                )
                for r in repos
                if not r.get("fork")
            )
        )

        # ---------------------------------------------------------------
        # Languages
        # ---------------------------------------------------------------

        lang_count = {}

        for r in repos:

            lang = r.get("language")

            if lang:

                lang_count[lang] = (
                    lang_count.get(
                        lang,
                        0,
                    )
                    + 1
                )

        top_langs = sorted(
            lang_count,
            key=lang_count.get,
            reverse=True,
        )[:4]

        stats["top_languages"] = (
            ", ".join(top_langs)
            if top_langs
            else "N/A"
        )

        # ---------------------------------------------------------------
        # Contributions
        # ---------------------------------------------------------------

        query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar {
                totalContributions
              }
            }
          }
        }
        """

        gql_resp = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={
                "query": query,
                "variables": {
                    "login": login
                },
            },
            timeout=15,
        )

        if gql_resp.status_code == 200:

            data = gql_resp.json()

            total = (
                data
                .get("data", {})
                .get("user", {})
                .get("contributionsCollection", {})
                .get("contributionCalendar", {})
                .get("totalContributions")
            )

            if total is not None:

                stats["contributions"] = (
                    f"{total} (last year)"
                )

    except Exception as e:

        print(
            f"warning: failed to fetch live stats: {e}",
            file=sys.stderr,
        )

    return stats


# ---------------------------------------------------------------------------
# BUILD SVG
# ---------------------------------------------------------------------------

def build_svg(art_rows, fields):

    PAD = 34

    ART_W = (
        ART_COLS * CELL_W
    )

    ART_H = (
        len(art_rows) * CELL_H
    )

    GAP = 46

    FIELD_LINE_H = 24

    HEADER_H = 26

    RULE_GAP = 10

    SWATCH = 20

    SWATCH_GAP = 8

    PROMPT_H = 62

    info_x = (
        PAD
        + ART_W
        + GAP
    )

    header_y = (
        PAD
        + HEADER_H
    )

    rule_y = (
        header_y
        + RULE_GAP
    )

    fields_start_y = (
        rule_y
        + 34
    )

    fields_h = (
        len(fields)
        * FIELD_LINE_H
    )

    swatch_y = (
        fields_start_y
        + fields_h
        + 14
    )

    info_bottom = (
        swatch_y
        + SWATCH
        + 10
    )

    art_top = (
        fields_start_y
        - 8
    )

    art_bottom = (
        art_top
        + ART_H
    )

    content_bottom = max(
        info_bottom,
        art_bottom,
    )

    prompt_y = (
        content_bottom
        + 40
    )

    H = (
        prompt_y
        + PROMPT_H
    )

    header_text = (
        f"{LOGIN}@github"
    )

    rule_len = max(
        len(header_text) + 2,
        ART_COLS,
    )

    max_field = max(
        [
            f"{k}: {v}"
            for k, v in fields
        ],
        key=len,
    )

    W = (
        info_x
        + max(
            360,
            len(max_field) * 8.2,
        )
        + PAD
    )

    # -----------------------------------------------------------------------
    # ASCII ART
    # -----------------------------------------------------------------------

    art_lines = []

    for i, row in enumerate(
        art_rows
    ):

        y = (
            art_top
            + i * CELL_H
            + CELL_H * 0.8
        )

        delay = round(
            i * 0.045,
            3,
        )

        art_lines.append(
            f'''
      <text
        x="{PAD}"
        y="{y:.1f}"
        class="art fadein"
        style="animation-delay:{delay}s"
        textLength="{ART_W:.1f}"
        lengthAdjust="spacingAndGlyphs"
        xml:space="preserve"
      >{xml_escape(row)}</text>
'''
        )

    art_svg = "".join(
        art_lines
    )

    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------

    header_svg = (
        f'''
      <text
        x="{info_x}"
        y="{header_y}"
        class="header"
      >{xml_escape(header_text)}</text>

      <line
        x1="{info_x}"
        y1="{rule_y}"
        x2="{info_x + rule_len * 9.4}"
        y2="{rule_y}"
        class="rule"
      />
'''
    )

    # -----------------------------------------------------------------------
    # FIELDS
    # -----------------------------------------------------------------------

    field_lines = []

    for i, (label, value) in enumerate(
        fields
    ):

        y = (
            fields_start_y
            + i * FIELD_LINE_H
        )

        delay = (
            0.5
            + i * 0.09
        )

        field_lines.append(
            f'''
      <text
        x="{info_x}"
        y="{y}"
        class="fieldline typewriter"
        style="animation-delay:{delay:.2f}s"
      >
        <tspan class="label">{xml_escape(label)}:</tspan>
        <tspan class="value"> {xml_escape(value)}</tspan>
      </text>
'''
        )

    fields_svg = "".join(
        field_lines
    )

    # -----------------------------------------------------------------------
    # PALETTE
    # -----------------------------------------------------------------------

    swatch_lines = []

    for i, color in enumerate(
        PALETTE
    ):

        x = (
            info_x
            + i
            * (
                SWATCH
                + SWATCH_GAP
            )
        )

        delay = (
            0.5
            + len(fields) * 0.09
            + i * 0.05
        )

        swatch_lines.append(
            f'''
      <rect
        x="{x:.1f}"
        y="{swatch_y:.1f}"
        width="{SWATCH}"
        height="{SWATCH}"
        rx="3"
        fill="{color}"
        class="swatch"
        style="animation-delay:{delay:.2f}s"
      />
'''
        )

    swatch_svg = "".join(
        swatch_lines
    )

    # -----------------------------------------------------------------------
    # TERMINAL PROMPT
    # -----------------------------------------------------------------------

    prompt_line1 = (
        f"┌──({LOGIN}@github)-[~]"
    )

    prompt_line2 = (
        "└─$ "
    )

    typed_x = (
        PAD
        + (
            len(prompt_line2)
            + 1
        )
        * 9.0
    )

    typed_y = (
        prompt_y
        + 24
    )

    (
        prompt_style,
        prompt_defs,
        prompt_cmd_svg,
        prompt_cursor_svg,
        cmd_max_w,
    ) = build_prompt_typing_svg(
        PROMPT_COMMANDS,
        typed_x,
        typed_y,
    )

    prompt_svg = (
        f'''
      <text
        x="{PAD}"
        y="{prompt_y}"
        class="prompt"
      >{xml_escape(prompt_line1)}</text>

      <text
        x="{PAD}"
        y="{typed_y}"
        class="prompt"
      >{xml_escape(prompt_line2)}</text>

      {prompt_cmd_svg}

      {prompt_cursor_svg}
'''
    )

    # Ensure longest prompt fits
    W = max(
        W,
        typed_x
        + cmd_max_w
        + PAD,
    )

    # -----------------------------------------------------------------------
    # FINAL SVG
    # -----------------------------------------------------------------------

    return f'''<svg
  width="{W:.0f}"
  height="{H:.0f}"
  viewBox="0 0 {W:.0f} {H:.0f}"
  xmlns="http://www.w3.org/2000/svg"
>

  <defs>

    <!-- Kali-style dark terminal background -->
    <linearGradient
      id="bgGradient"
      x1="0%"
      y1="0%"
      x2="100%"
      y2="100%"
    >
      <stop
        offset="0%"
        stop-color="#050505"
      />

      <stop
        offset="50%"
        stop-color="#080808"
      />

      <stop
        offset="100%"
        stop-color="#000000"
      />
    </linearGradient>

    <style>

      .art {{
        font-family: 'Courier New', monospace;
        font-size: {CELL_H * 0.82:.1f}px;
        fill: {ACCENT};
        white-space: pre;
      }}

      .header {{
        font-family: 'Courier New', monospace;
        font-size: 18px;
        font-weight: bold;
        fill: {ACCENT};
      }}

      .rule {{
        stroke: {ACCENT};
        stroke-width: 1.4;
        opacity: 0.85;
      }}

      .fieldline {{
        font-family: 'Courier New', monospace;
        font-size: 14px;
      }}

      .label {{
        fill: {LABEL_COLOR};
        font-weight: bold;
      }}

      .value {{
        fill: {VALUE_COLOR};
      }}

      .prompt {{
        font-family: 'Courier New', monospace;
        font-size: 15px;
        fill: {ACCENT};
      }}

      .cursor {{
        fill: {ACCENT};
        animation: blink 1s steps(1) infinite;
      }}

      .promptcmd {{
        font-family: 'Courier New', monospace;
        font-size: 15px;
        fill: {ACCENT};
        white-space: pre;
      }}

      .promptcursor {{
        fill: {ACCENT};
      }}

      {prompt_style}

      .fadein {{
        opacity: 0;
        animation-name: reveal;
        animation-duration: 0.35s;
        animation-fill-mode: forwards;
        animation-timing-function: steps(1);
      }}

      .typewriter {{
        opacity: 0;
        animation-name: reveal;
        animation-duration: 0.4s;
        animation-fill-mode: forwards;
        animation-timing-function: steps(1);
      }}

      .swatch {{
        opacity: 0;
        animation-name: revealSwatch;
        animation-duration: 0.35s;
        animation-fill-mode: forwards;
        animation-timing-function: steps(1);
      }}

      @keyframes reveal {{
        to {{
          opacity: 1;
        }}
      }}

      @keyframes revealSwatch {{
        to {{
          opacity: 1;
        }}
      }}

      @keyframes blink {{
        0%, 49% {{
          opacity: 1;
        }}

        50%, 100% {{
          opacity: 0;
        }}
      }}

    </style>

    {prompt_defs}

  </defs>


  <!-- Background -->

  <rect
    x="0"
    y="0"
    width="{W:.0f}"
    height="{H:.0f}"
    rx="18"
    fill="url(#bgGradient)"
  />


  <!-- ASCII avatar -->

  {art_svg}


  <!-- Header -->

  {header_svg}


  <!-- Profile fields -->

  {fields_svg}


  <!-- Terminal palette -->

  {swatch_svg}


  <!-- Terminal prompt -->

  {prompt_svg}

</svg>
'''


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():

    avatar_path = find_avatar()

    if avatar_path:

        print(
            f"using avatar image: {avatar_path}"
        )

        art_rows = (
            ascii_rows_from_image(
                avatar_path
            )
        )

    else:

        print(
            "no avatar found, using procedural placeholder art"
        )

        art_rows = (
            ascii_rows_placeholder()
        )

    # -----------------------------------------------------------------------
    # GitHub statistics
    # -----------------------------------------------------------------------

    stats = fetch_github_stats(
        LOGIN,
        TOKEN,
    )

    fields = list(
        PROFILE_FIELDS
    ) + [
        (
            "Repositories",
            stats["repos"],
        ),
        (
            "Stars",
            stats["stars"],
        ),
        (
            "Followers",
            stats["followers"],
        ),
        (
            "Contributions",
            stats["contributions"],
        ),
        (
            "Languages",
            stats["top_languages"],
        ),
    ]

    # -----------------------------------------------------------------------
    # Generate SVG
    # -----------------------------------------------------------------------

    svg = build_svg(
        art_rows,
        fields,
    )

    # Create output directory automatically
    output_dir = os.path.dirname(
        OUT_PATH
    )

    if output_dir:
        os.makedirs(
            output_dir,
            exist_ok=True,
        )

    with open(
        OUT_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(svg)

    print(
        f"wrote {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
