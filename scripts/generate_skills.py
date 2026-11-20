#!/usr/bin/env python3
"""
Animated Tech Stack & Skills SVG Generator (Multi-Source SVG + PNG + Kali-matched theme).

Supported source prefixes in ICON_SOURCES:
  - "skillicons:<Filename.svg>" -> Fetches from tandpfun/skill-icons (already framed)
  - "url:<https://...>"         -> Fetches any SVG or PNG URL & wraps it in a matching dark card
  - "local:<path/to/icon>"      -> Reads a local SVG or PNG file & wraps it in a matching dark card

Env vars:
  OUT_PATH   - Output SVG path (default: assets/skills.svg)
"""

import base64
import os
import re
import urllib.request

OUT_PATH = os.environ.get("OUT_PATH", "assets/skills.svg")

SKILLICONS_BASE = "https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/"
SIMPLEICONS_BASE = "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/"
PODMAN_BASE = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/"

# List of skills and accessible titles
SKILLS = [
    ("php", "PHP"),
    ("laravel", "Laravel"),
    ("codeigniter", "CodeIgniter"),
    ("frankenphp", "FrankenPHP"),
    ("mysql", "MySQL"),
    ("py", "Python"),
    ("js", "JavaScript"),
    ("html", "HTML5"),
    ("css", "CSS3"),
    ("bash", "Bash"),
    ("linux", "Linux"),
    ("kali", "Kali Linux"),
    ("ubuntu", "Ubuntu"),
    ("burpsuite", "Burp Suite"),
    ("docker", "Docker"),
    ("podman", "Podman"),
    ("git", "Git"),
    ("github", "GitHub"),
    ("vscode", "VS Code"),
]

# Format:
#   "skillicons:File.svg"           -> Native skill-icons card
#   "url:https://...|#HexColor"     -> External SVG or PNG wrapped in matching dark card
#   "local:assets/icons/x.png"      -> Local custom SVG or PNG wrapped in matching dark card
ICON_SOURCES = {
    "php": "skillicons:PHP-Dark.svg",
    "laravel": "skillicons:Laravel-Dark.svg",
    "codeigniter": f"url:{SIMPLEICONS_BASE}codeigniter.svg|#EE4623",
    "frankenphp": "url:https://raw.githubusercontent.com/dunglas/frankenphp/main/frankenphp.png",
    "mysql": "skillicons:MySQL-Dark.svg",
    "py": "skillicons:Python-Dark.svg",
    "js": "skillicons:JavaScript.svg",
    "html": "skillicons:HTML.svg",
    "css": "skillicons:CSS.svg",
    "bash": "skillicons:Bash-Dark.svg",
    "linux": "skillicons:Linux-Dark.svg",
    "kali": "skillicons:Kali-Dark.svg",
    "ubuntu": "skillicons:Ubuntu-Dark.svg",
    "burpsuite": f"url:{SIMPLEICONS_BASE}burpsuite.svg|#FF6633",
    "docker": "skillicons:Docker.svg",
    "podman": f"url:{PODMAN_BASE}podman.svg|#E02C2C",
    "git": "skillicons:Git.svg",
    "github": "skillicons:Github-Dark.svg",
    "vscode": "skillicons:VSCode-Dark.svg",
}

# Kali-matched dark palette
CARD_BG = "#242938"
CARD_BORDER = "#1f2740"

# Layout & Animation Configuration
PER_LINE = 6          # Icons per row (bottom row automatically centered)
ICON_SIZE = 54        # Size of each icon (px)
GAP_X = 20            # Horizontal gap between icons (px)
GAP_Y = 18            # Vertical gap between rows
PADDING_X = 24        # Left & right padding
PADDING_Y = 20        # Top & bottom padding


def load_raw_bytes(source_spec: str) -> tuple[bytes, bool, str | None]:
    """
    Load raw bytes from skillicons, external URL, or local path.
    Returns: (raw_bytes, needs_card_wrapper, optional_fill_tint)
    """
    tint_color = None
    if "|" in source_spec:
        source_spec, tint_color = source_spec.split("|", 1)

    if source_spec.startswith("skillicons:"):
        filename = source_spec.split(":", 1)[1]
        url = f"{SKILLICONS_BASE}{filename}"
        print(f"Downloading [skillicons] {filename}...")
        req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Skills-SVG-Generator"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), False, None

    if source_spec.startswith("url:"):
        url = source_spec.split(":", 1)[1]
        print(f"Downloading [url] {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Skills-SVG-Generator"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), True, tint_color

    if source_spec.startswith("local:"):
        path = source_spec.split(":", 1)[1]
        print(f"Reading [local] {path}...")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Local icon file not found: {path}")
        with open(path, "rb") as f:
            return f.read(), True, tint_color

    raise ValueError(f"Unsupported source prefix in: {source_spec}")


def extract_viewbox(raw_svg: str) -> str:
    """Extract viewBox from source SVG so non-256x256 icons scale cleanly."""
    match = re.search(r'viewBox="([^"]+)"', raw_svg)
    if match:
        return match.group(1)
    w_match = re.search(r'\bwidth="([0-9.]+)"', raw_svg)
    h_match = re.search(r'\bheight="([0-9.]+)"', raw_svg)
    if w_match and h_match:
        return f"0 0 {w_match.group(1)} {h_match.group(1)}"
    return "0 0 24 24"


def prepare_icon_svg(skill_key: str, index: int) -> str:
    """Fetch, detect SVG vs raster (PNG/WebP), and wrap into a matching 256x256 card."""
    source_spec = ICON_SOURCES.get(skill_key)
    if not source_spec:
        raise ValueError(f"No icon source configured for '{skill_key}'.")

    raw_bytes, needs_wrapper, tint_color = load_raw_bytes(source_spec)

    # Check if binary raster image (PNG magic header \x89PNG or WebP RIFF)
    is_png = raw_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = raw_bytes.startswith(b"RIFF") and raw_bytes[8:12] == b"WEBP"

    if is_png or is_webp:
        mime = "image/png" if is_png else "image/webp"
        b64_data = base64.b64encode(raw_bytes).decode("ascii")
        return f"""<svg width="{ICON_SIZE}" height="{ICON_SIZE}" viewBox="0 0 256 256">
          <rect x="2" y="2" width="252" height="252" rx="58" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="4" />
          <image x="44" y="44" width="168" height="168" href="data:{mime};base64,{b64_data}" preserveAspectRatio="xMidYMid meet" />
        </svg>"""

    raw_svg = raw_bytes.decode("utf-8")
    viewbox = extract_viewbox(raw_svg)

    # Strip outer <svg> tags
    inner = re.sub(r"<svg[^>]*>", "", raw_svg, count=1)
    inner = re.sub(r"</svg>\s*$", "", inner).strip()

    # Prefix IDs uniquely so gradients/clipPaths never collide
    prefix = f"icon{index}_"
    inner = re.sub(r'\bid="([^"]+)"', rf'id="{prefix}\1"', inner)
    inner = re.sub(r'url\(#([^)]+)\)', rf'url(#{prefix}\1)', inner)
    inner = re.sub(r'href="#([^"]+)"', rf'href="#{prefix}\1"', inner)

    if not needs_wrapper:
        return f"""<svg width="{ICON_SIZE}" height="{ICON_SIZE}" viewBox="0 0 256 256">
          {inner}
        </svg>"""

    fill_attr = f' fill="{tint_color}"' if tint_color else ""
    return f"""<svg width="{ICON_SIZE}" height="{ICON_SIZE}" viewBox="0 0 256 256">
          <rect x="2" y="2" width="252" height="252" rx="58" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="4" />
          <svg x="54" y="54" width="148" height="148" viewBox="{viewbox}"{fill_attr}>
            {inner}
          </svg>
        </svg>"""


def build_svg():
    total_icons = len(SKILLS)
    rows = (total_icons + PER_LINE - 1) // PER_LINE

    canvas_width = PER_LINE * ICON_SIZE + (PER_LINE - 1) * GAP_X + (PADDING_X * 2)
    canvas_height = rows * ICON_SIZE + (rows - 1) * GAP_Y + (PADDING_Y * 2)

    svg_elements = []

    for idx, (skill_key, label) in enumerate(SKILLS):
        row = idx // PER_LINE
        col = idx % PER_LINE

        icons_in_this_row = min(PER_LINE, total_icons - row * PER_LINE)
        row_width = icons_in_this_row * ICON_SIZE + (icons_in_this_row - 1) * GAP_X
        start_x = (canvas_width - row_width) / 2

        x = start_x + col * (ICON_SIZE + GAP_X)
        y = PADDING_Y + row * (ICON_SIZE + GAP_Y)

        delay = round(idx * 0.14, 2)
        icon_markup = prepare_icon_svg(skill_key, idx)

        svg_elements.append(f"""
  <g transform="translate({x}, {y})">
    <title>{label}</title>
    <g class="skill-float" style="animation-delay: {delay}s;">
      {icon_markup}
    </g>
  </g>""")

    return f"""<svg width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @keyframes floatWave {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-6px); }}
      }}
      .skill-float {{
        animation: floatWave 3s ease-in-out infinite;
      }}
    </style>
  </defs>
{''.join(svg_elements)}
</svg>
"""


def main():
    svg = build_svg()
    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()