from pathlib import Path
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
import qrcode
import barcode
from barcode.writer import ImageWriter

from config import (
    CARD_OUTPUT_FOLDER,
    LOGO_PATH,
    PRINCIPAL_SIGN_PATH,
    FRONT_BG_PATH,
    BACK_BG_PATH,
    FONT_REGULAR,
    FONT_BOLD,
)
from database import Student, Card

# Standard ATM size @300 DPI
CARD_WIDTH = 1011
CARD_HEIGHT = 638
CORNER_RADIUS = 38

WHITE_RGBA = (255, 255, 255, 255)
BLACK = (20, 20, 20)
PURPLE = (120, 56, 161)
GREY_TEXT = (70, 70, 70)

def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    if Path(path).is_file():
        return ImageFont.truetype(path, size)
    return ImageFont.truetype("arial.ttf", size)

# --- PROFESSIONAL FONT SIZING (Updated for full-look) ---
FONT_TITLE = load_font(FONT_BOLD, 32)        
FONT_LABEL_BIG = load_font(FONT_BOLD, 30)    
FONT_LABEL = load_font(FONT_BOLD, 26)        
FONT_VALUE = load_font(FONT_REGULAR, 25)     
FONT_SMALL = load_font(FONT_REGULAR, 18)     
FONT_BACK_HEAD = load_font(FONT_BOLD, 28)
FONT_BACK_TEXT = load_font(FONT_REGULAR, 20)

def _load_optional(path: str, size: Tuple[int, int] | None = None) -> Image.Image | None:
    if not path or not Path(path).is_file():
        return None
    img = Image.open(path).convert("RGBA")
    if size:
        img = img.resize(size, Image.LANCZOS)
    return img

def add_corners(im, radius):
    mask = Image.new("L", im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + im.size, radius=radius, fill=255)
    output = Image.new("RGBA", im.size, (0, 0, 0, 0))
    output.paste(im, (0, 0), mask=mask)
    return output

# ---------- FRONT SIDE ----------

def generate_front_image(student: Student, card: Card | None = None) -> Image.Image:
    img = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), WHITE_RGBA)
    d = ImageDraw.Draw(img)

    # Increased layout values to eliminate bottom white space
    strip_h = int(CARD_HEIGHT * 0.22)      
    top_margin = strip_h + 40             
    line_gap = int(CARD_HEIGHT * 0.095)   

    # Purple Header
    d.rectangle([0, 0, CARD_WIDTH, strip_h], fill=PURPLE)

    # Logo
    logo = _load_optional(LOGO_PATH, size=(110, 110))
    if logo:
        img.paste(logo, (40, 20), logo)

    # College Name
    college_lines = ["Mahatma Gandhi Mission's", "COLLEGE OF COMPUTER SCIENCE & IT"]
    text_y = 25
    for line in college_lines:
        bbox = d.textbbox((0, 0), line, font=FONT_LABEL_BIG)
        w = bbox[2] - bbox[0]
        d.text(((CARD_WIDTH - w) // 2, text_y), line, fill=WHITE_RGBA, font=FONT_LABEL_BIG)
        text_y += 38

    # Small address/web text in header
    small_text = "Near Airport, Nanded - 431605, Tel: (02462)-222592   Web: www.mgmccsit.ac.in"
    bbox = d.textbbox((0, 0), small_text, font=FONT_SMALL)
    d.text(((CARD_WIDTH - (bbox[2] - bbox[0])) // 2, strip_h - 35),
           small_text, fill=WHITE_RGBA, font=FONT_SMALL)

    left_margin = 60
    label_w = 160 

    # --- Student Details Section ---
    # Name
    d.text((left_margin, top_margin), "Name:", fill=BLACK, font=FONT_LABEL)
    d.text((left_margin + label_w, top_margin), student.full_name, fill=BLACK, font=FONT_TITLE)

    # Address
    addr_y = top_margin + line_gap
    d.text((left_margin, addr_y), "Address:", fill=BLACK, font=FONT_LABEL)
    addr_text_y = addr_y
    for line in [student.address_line1, student.address_line2, student.address_line3]:
        if line:
            d.text((left_margin + label_w, addr_text_y), line, fill=BLACK, font=FONT_VALUE)
            addr_text_y += 30

    # Class
    y = addr_text_y + 20
    d.text((left_margin, y), "Class:", fill=BLACK, font=FONT_LABEL)
    d.text((left_margin + label_w, y), student.class_name or "", fill=BLACK, font=FONT_VALUE)

    # DOB & Blood Group
    y += line_gap
    d.text((left_margin, y), "DOB:", fill=BLACK, font=FONT_LABEL)
    d.text((left_margin + label_w, y), student.dob or "", fill=BLACK, font=FONT_VALUE)
    d.text((left_margin + 450, y), "Blood grp:", fill=BLACK, font=FONT_LABEL)
    d.text((left_margin + 610, y), student.blood_group or "", fill=BLACK, font=FONT_VALUE)

    # Contact & Year
    y += line_gap
    d.text((left_margin, y), "Contact:", fill=BLACK, font=FONT_LABEL)
    d.text((left_margin + label_w, y), student.contact_no or "", fill=BLACK, font=FONT_VALUE)
    d.text((left_margin + 450, y), "Year:", fill=BLACK, font=FONT_LABEL)
    d.text((left_margin + 580, y), student.year_text or "", fill=BLACK, font=FONT_VALUE)

    # Photo (Centered Right)
    photo_w, photo_h = 200, 240
    photo_x = CARD_WIDTH - photo_w - 60
    photo_y = top_margin
    d.rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], outline=BLACK, width=2)

    if student.photo_path and Path(student.photo_path).is_file():
        photo = Image.open(student.photo_path).convert("RGBA").resize((photo_w, photo_h), Image.LANCZOS)
        img.paste(photo, (photo_x, photo_y))

    # Signature Position - Fixed to Fill Bottom Space
    sign = _load_optional(PRINCIPAL_SIGN_PATH, size=(220, 80))
    if sign:
        img.paste(sign, (photo_x - 10, CARD_HEIGHT - 160), sign)
    
    # FIXED: Using FONT_LABEL object instead of FONT_BOLD string
    d.text((photo_x + 50, CARD_HEIGHT - 80), "Principal", fill=BLACK, font=FONT_LABEL)

    return img

# ---------- BACK SIDE ----------

def _generate_qr(data: str, size: int = 240) -> Image.Image:
    qr = qrcode.QRCode(version=1, box_size=10, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGBA").resize((size, size), Image.LANCZOS)

def _generate_barcode(data: str, width: int = 300, height: int = 70) -> Image.Image:
    code128 = barcode.get("code128", data, writer=ImageWriter())
    tmp = Path(CARD_OUTPUT_FOLDER) / f"tmp_bar{data}"
    code128.save(str(tmp))
    img = Image.open(tmp.with_suffix(".png")).convert("RGBA").resize((width, height), Image.LANCZOS)
    tmp.with_suffix(".png").unlink(missing_ok=True)
    return img

def generate_back_image(student: Student, card: Card) -> Image.Image:
    base = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), WHITE_RGBA)
    d = ImageDraw.Draw(base)

    top_h = int(CARD_HEIGHT * 0.45)
    bg = _load_optional(BACK_BG_PATH, size=(CARD_WIDTH, CARD_HEIGHT - top_h))
    if bg:
        base.paste(bg, (0, top_h))

    d.text((60, 50), "PLEASE NOTE", fill=BLACK, font=FONT_BACK_HEAD)

    rules = [
        "1. The student should possess Identity Card and must produce whenever demanded.",
        "2. If it is lost, the card holder must intimate to the Principal",
        "   and apply for a new card within a week.",
        "3. If this card does not belong to you, please return it to :",
        "   The Principal, MGM's College of Comp. Sci. & IT, Nanded.",
    ]
    text_y = 100
    for line in rules:
        d.text((60, text_y), line, fill=BLACK, font=FONT_BACK_TEXT)
        text_y += 35

    bar_data = card.barcode_number or student.student_code
    bar_img = _generate_barcode(bar_data)
    base.paste(bar_img, (CARD_WIDTH - 350, 50))

    qr_size = 240
    qr_img = _generate_qr(card.qr_data or student.student_code, qr_size)
    qr_x = (CARD_WIDTH - qr_size) // 2
    qr_y = top_h + 30
    base.paste(qr_img, (qr_x, qr_y))

    return base

# ---------- PUBLIC API ----------

def generate_card_images(student: Student, card: Card) -> Tuple[str, str]:
    Path(CARD_OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

    front_final = add_corners(generate_front_image(student, card), CORNER_RADIUS)
    back_final = add_corners(generate_back_image(student, card), CORNER_RADIUS)

    front_path = Path(CARD_OUTPUT_FOLDER) / f"{student.student_code}_front.png"
    back_path = Path(CARD_OUTPUT_FOLDER) / f"{student.student_code}_back.png"

    front_final.save(front_path, format="PNG", dpi=(300, 300))
    back_final.save(back_path, format="PNG", dpi=(300, 300))

    card.front_image_path = str(front_path)
    card.back_image_path = str(back_path)

    return str(front_path), str(back_path)