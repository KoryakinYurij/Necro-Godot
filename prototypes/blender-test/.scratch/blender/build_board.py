"""Build self-contained preview pages (images inlined as data URIs).

The preview server only serves the registered HTML file, so sibling <img src>
files 404 and every image has to be embedded.

Usage:
  python .scratch/blender/build_board.py sheet        # 2x2 hero render sheet
  python .scratch/blender/build_board.py checks       # geometry check sheet
  python .scratch/blender/build_board.py front        # one hero render, large
"""

import base64
import sys
from pathlib import Path

PREVIEW = Path(__file__).resolve().parent.parent / "preview"
CHECKS = PREVIEW / "checks"

VIEWS = [
    ("hero_front", "full body, front", "hero_front.jpg"),
    ("hero_three_quarter", "full body, three quarter", "hero_three_quarter.jpg"),
    ("hero_head_detail", "skull, glowing eyes, gold trim", "hero_head_detail.jpg"),
    ("hero_staff_lantern", "staff skull lantern and flame", "hero_staff_lantern.jpg"),
]

CHECK_VIEWS = [
    ("_check_shoulder", "pauldron and shoulder"),
    ("_check_neck", "neck, collar and hood junction"),
    ("_check_hand", "grip on the staff"),
    ("_check_hand_side", "grip from the worn side"),
]

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title><style>
  html,body {{ margin:0; background:#0d0d12; color:#d8d4e8;
               font:13px/1.35 system-ui,sans-serif; }}
  h1 {{ font-size:15px; margin:10px 14px 8px; font-weight:600; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; padding:0 14px 14px; }}
  figure {{ margin:0; }}
  img {{ display:block; width:100%; height:auto; border:1px solid #2b2b38; }}
  figcaption {{ color:#9d98b5; font-size:12px; margin-top:3px; }}
  .wide {{ padding:0 14px 14px; }}
</style></head><body>
<h1>{title}</h1>
"""


def data_uri(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build_sheet() -> str:
    parts = [HEAD.format(title="Necro Hero - polished renders (contact sheet)"),
             '<div class="grid">']
    for name, caption, filename in VIEWS:
        parts.append('<figure><img alt="%s" src="%s"><figcaption>%s</figcaption></figure>'
                     % (name, data_uri(PREVIEW / filename), caption))
    parts.append("</div></body></html>")
    return "".join(parts)


def build_checks() -> str:
    parts = [HEAD.format(title="Necro Hero - close-up geometry checks"),
             '<div class="grid">']
    for name, caption in CHECK_VIEWS:
        path = CHECKS / (name + ".jpg")
        if not path.exists():
            continue
        parts.append('<figure><img alt="%s" src="%s"><figcaption>%s</figcaption></figure>'
                     % (name, data_uri(path), caption))
    parts.append("</div></body></html>")
    return "".join(parts)


def build_single(key: str) -> str:
    for name, caption, filename in VIEWS:
        if name == key:
            return (HEAD.format(title="Necro Hero - " + caption)
                    + '<div class="wide"><img alt="%s" src="%s">'
                      "<figcaption>%s</figcaption></div></body></html>"
                      % (name, data_uri(PREVIEW / filename), caption))
    raise SystemExit("unknown view: %s" % key)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "sheet"
    if mode == "sheet":
        html, out = build_sheet(), PREVIEW / "sheet.html"
    elif mode == "checks":
        html, out = build_checks(), PREVIEW / "checks.html"
    else:
        html, out = build_single(mode), PREVIEW / ("single-%s.html" % mode)
    out.write_text(html, encoding="utf-8")
    print("wrote", out, len(html), "chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
