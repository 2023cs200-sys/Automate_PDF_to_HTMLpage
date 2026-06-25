import fitz
import json
import os
import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PDF_PATH = "pdf/document.pdf"
IMAGE_DIR = "output/images"
DATA_DIR = "output/data"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

pdf = fitz.open(PDF_PATH)
pages_data = []

LEGACY_FONTS = {"FMAbhayax", "FMAbabldBold", "FMBasurux"}

for page_num in range(len(pdf)):
    page = pdf[page_num]

    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))

    ocr_text = pytesseract.image_to_string(img, lang="sin+eng").strip()

    blocks = page.get_text("dict")["blocks"]
    formats = []
    spans_list = []
    for block in blocks:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            sizes = []
            bold = False
            italic = False
            font_name = ""
            text_parts = []
            for span in line["spans"]:
                sizes.append(span["size"])
                if span["flags"] & 2:
                    bold = True
                if span["flags"] & 1:
                    italic = True
                if not font_name:
                    font_name = span["font"]
                text_parts.append(span["text"])
            avg_size = sum(sizes) / len(sizes) if sizes else 12
            legacy = any(f in font_name for f in LEGACY_FONTS)
            formats.append({
                "size": round(avg_size, 1),
                "bold": bold,
                "italic": italic,
                "legacy": legacy,
                "font": font_name,
            })
            if text_parts:
                spans_list.append("".join(text_parts))

    page_info = {
        "page": page_num + 1,
        "text": ocr_text,
        "formats": formats,
        "images": []
    }

    images = page.get_images(full=True)
    for img_index, img_ref in enumerate(images):
        xref = img_ref[0]
        image = pdf.extract_image(xref)
        image_bytes = image["image"]
        image_ext = image["ext"]
        image_name = f"page_{page_num+1}_{img_index}.{image_ext}"
        image_path = os.path.join(IMAGE_DIR, image_name)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        page_info["images"].append(image_name)

    pages_data.append(page_info)
    print(f"Page {page_num+1}/{len(pdf)} processed")

with open(f"{DATA_DIR}/pages.json", "w", encoding="utf-8") as f:
    json.dump(pages_data, f, ensure_ascii=False, indent=4)

print("Extraction Complete")
