import json
import re
import statistics

with open("output/data/pages.json", encoding="utf-8") as f:
    pages = json.load(f)

with open("templates/base.html", encoding="utf-8") as f:
    template = f.read()

topics = [
    ("vesak",     "Significance of Vesak",               2,  5),
    ("editor",    "From the Desk of the Editor",         5,  7),
    ("sinhala",   "Sinhala: A Unique Language",          7,  10),
    ("builders",  "Builders of our Nation",              10, 15),
    ("teaching",  "The Buddha's Teaching",               15, 18),
    ("picture",   "A Picture is worth a Thousand Words", 18, 19),
    ("profit",    "From Profit to Purpose",              19, 22),
    ("piliweth",  "\u0db6\u0ddc\u0daf\u0dca\u0db0 \u0dc0\u0dad\u0dca \u0db4\u0dd2\u0dc5\u0dd2\u0dc0\u0dd9\u0dad\u0dca", 22, 25),
    ("heritage",  "A Bit of our Heritage - Kelaniya",    25, 28),
    ("verses",    "Verses from Lovada Sangarava",        28, 31),
    ("pali",      "The Pali Alphabet in English",        31, 33),
]

def _fix_ocr(s):
    s = re.sub(r'(?<=\s)1\]', 'the', s)
    s = re.sub(r'(?<=\s)0\]', 'of', s)
    s = s.replace('\ufffd', "'")
    s = s.replace('\u2019', "'")
    s = s.replace('\u2018', "'")
    return s

def clean_text(text):
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if re.match(r'^[\d\u0D80-\u0DFF]*\s*The\s*Bosat\s*[-]\s*Wesak\s*[\d\u0D80-\u0DFF]*$', s, re.IGNORECASE):
            cleaned.append("")
            continue
        if re.match(r'^\d+$', s) and len(s) <= 2:
            cleaned.append("")
            continue
        if re.match(r'^[ivxlcdm]+$', s, re.IGNORECASE):
            cleaned.append("")
            continue
        low = s.lower()
        if low.startswith('go to table') or low.startswith('go to content') or 'table of content' in low:
            cleaned.append("")
            continue
        cleaned.append(_fix_ocr(s))
    return cleaned

def build_format_map(page_formats):
    m = {}
    sizes = [f["size"] for f in page_formats if f["size"] > 0]
    if not sizes:
        return m, 12, 15.6, 13.8
    median = statistics.median(sizes)
    h_th = median * 1.35
    sh_th = median * 1.15
    cls_map = {}
    for i, f in enumerate(page_formats):
        if f["size"] > h_th:
            cls = "heading"
        elif f["size"] > sh_th:
            cls = "subheading"
        elif f["bold"]:
            cls = "bold"
        elif f["italic"]:
            cls = "italic"
        else:
            cls = "body"
        cls_map[i] = cls
    return cls_map, median, h_th, sh_th

def is_heading_by_content(text):
    s = text.strip()
    if not s:
        return None
    if re.match(r'^[\d\.\s]+$', s):
        return None
    if re.match(r'^\d+\.$', s):
        return None
    all_words = s.split()
    upper_words = sum(1 for w in all_words if w.isupper() and len(w) > 1)
    if len(all_words) >= 3 and upper_words >= len(all_words) * 0.7 and len(s) < 80 and len(s) > 10:
        return "heading"
    known_headings = [
        "significance of", "from the desk", "sinhala: a unique",
        "builders of our", "the buddha's teaching", "a picture is worth",
        "from profit to purpose", "a bit of our heritage",
        "verses from", "the pali alphabet", "contents",
        "vesak poya", "full moon poya",
    ]
    low = s.lower().rstrip(".:!,")
    for kh in known_headings:
        if low.startswith(kh):
            return "heading"
    if s.endswith(":") and len(s) < 55:
        return "subheading"
    if len(s) < 60 and len(s.split()) <= 5 and s.endswith(":"):
        return "subheading"
    return None

def render_page(raw_lines, page_formats, topic_name=""):
    cls_map, median, h_th, sh_th = build_format_map(page_formats)

    topic_lower = topic_name.lower().strip()

    blocks = []
    cur = []
    for line in raw_lines:
        if not line.strip():
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line.strip())
    if cur:
        blocks.append(cur)

    html_parts = []
    fmt_idx = 0
    fmt_len = len(page_formats)
    blk_idx = 0

    while blk_idx < len(blocks):
        lines = blocks[blk_idx]
        text = " ".join(lines)

        chk = is_heading_by_content(text) if lines else None

        if not chk and fmt_idx < fmt_len:
            fmt = page_formats[fmt_idx]
            if fmt["size"] > h_th:
                chk = "heading"
            elif fmt["size"] > sh_th:
                chk = "subheading"

        if chk:
            tag = "h3" if chk == "heading" else "h4"
            out = text
            if " by " in text.lower() and chk == "heading":
                out = re.split(r'\s+by\s+', text, maxsplit=1, flags=re.IGNORECASE)[0]
            out_clean = out.lower().strip().rstrip(".:!,")
            if (out_clean == topic_lower or
                out_clean == topic_lower.rstrip(".:!,") or
                out_clean in topic_lower or
                topic_lower in out_clean):
                fmt_idx += len(lines)
                blk_idx += 1
                continue
            html_parts.append(f"<{tag}>{out}</{tag}>")
            fmt_idx += len(lines)
            blk_idx += 1
            continue

        is_bold = any(page_formats[fi]["bold"] for fi in range(fmt_idx, min(fmt_idx + len(lines) + 2, fmt_len)) if fi < fmt_len)
        is_italic = any(page_formats[fi]["italic"] for fi in range(fmt_idx, min(fmt_idx + len(lines) + 2, fmt_len)) if fi < fmt_len)

        fmt_idx = min(fmt_idx + len(lines) + 1, fmt_len)

        wrapped = text
        if len(text) < 130 and is_bold and is_italic:
            wrapped = f"<strong><em>{wrapped}</em></strong>"
        elif len(text) < 130 and is_bold:
            wrapped = f"<strong>{wrapped}</strong>"
        elif len(text) < 130 and is_italic:
            wrapped = f"<em>{wrapped}</em>"
        html_parts.append(f"<p>{wrapped}</p>")

        blk_idx += 1

    return "\n".join(html_parts)

content = ""

for idx, (topic_id, topic_name, start, end) in enumerate(topics, 1):
    section_id = f"topic-{topic_id}"

    merged_html = []
    images = []

    for i in range(start, end):
        p = pages[i]
        if not p["text"].strip():
            images.extend(p["images"])
            continue
        raw_lines = clean_text(p["text"])
        html = render_page(raw_lines, p.get("formats", []), topic_name)
        if html:
            merged_html.append(html)
        images.extend(p["images"])

    section_html = f'<section id="{section_id}" class="topic-section">\n'
    section_html += f'<h2 class="topic-title"><span class="topic-no">Article {idx:02d}</span>{topic_name}</h2>\n'
    section_html += "\n".join(merged_html)

    for img in images:
        section_html += f'<div class="image-wrapper"><img src="../images/{img}" alt=""></div>\n'

    section_html += f'<a href="#" class="back-to-top">&uarr; Back to top</a>\n'
    section_html += '</section>\n'
    content += section_html

hero_html = ""
if pages[0]["images"]:
    hero_html = f'<div class="hero"><img src="../images/{pages[0]["images"][0]}" alt="The BOSAT - Vesak"></div>\n'

full_content = hero_html + content

nav_links = ""
for idx, (topic_id, topic_name, start, end) in enumerate(topics, 1):
    nav_links += f'<li><a href="#topic-{topic_id}"><span class="nav-num">{idx:02d}</span>{topic_name}</a></li>\n'

final_html = template.replace("{{CONTENT}}", full_content).replace("{{NAV_LINKS}}", nav_links)

with open("output/html/index.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("HTML Generated")
