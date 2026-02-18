import os
import re
import uuid
import random
import html
import time
import threading
import zipfile
from io import BytesIO

from flask import (Flask, render_template, request, jsonify, send_file,
                   session, send_from_directory)
from reportlab.lib.pagesizes import A4, LETTER, LEGAL
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-prod')

FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
# Use temp dir on Vercel/serverless where project dir is read-only
if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    import tempfile
    GENERATED_DIR = os.path.join(tempfile.gettempdir(), 'handwriting_generated')
else:
    GENERATED_DIR = os.path.join(os.path.dirname(__file__), 'generated')
try:
    os.makedirs(GENERATED_DIR, exist_ok=True)
except OSError:
    import tempfile
    GENERATED_DIR = os.path.join(tempfile.gettempdir(), 'handwriting_generated')
    os.makedirs(GENERATED_DIR, exist_ok=True)

AVAILABLE_FONTS = {}

def register_fonts():
    if not os.path.isdir(FONTS_DIR):
        os.makedirs(FONTS_DIR, exist_ok=True)
        return
    for filename in os.listdir(FONTS_DIR):
        if filename.endswith('.ttf'):
            name = os.path.splitext(filename)[0]
            display_name = name.replace('-Regular', '').replace('QE', '')
            path = os.path.join(FONTS_DIR, filename)
            try:
                pdfmetrics.registerFont(TTFont(display_name, path))
                AVAILABLE_FONTS[display_name] = path
            except Exception:
                pass

register_fonts()

PAGE_SIZES = {
    'A4': A4,
    'A3': (297*mm, 420*mm),
    'A5': (148*mm, 210*mm),
    'Letter': LETTER,
    'Legal': LEGAL,
}

def sanitize_text(text):
    text = html.escape(text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#x27;', "'").replace('&quot;', '"')
    return text

def classify_line(line):
    stripped = line.strip()
    if not stripped:
        return 'empty', stripped
    upper = stripped.upper()
    if any(kw in upper for kw in ['HOME ASSIGNMENT', 'ASSIGNMENT', 'HOMEWORK']):
        return 'title', stripped
    if re.match(r'^(NAME|STUDENT NAME)\s*[:.]', stripped, re.IGNORECASE):
        return 'name', stripped
    if re.match(r'^(ID|ROLL NO|STUDENT ID|REG)\s*[:.]', stripped, re.IGNORECASE):
        return 'id', stripped
    if re.match(r'^(DATE|SUBMITTED ON)\s*[:.]', stripped, re.IGNORECASE):
        return 'date', stripped
    if re.match(r'^(SUBJECT|COURSE|CLASS)\s*[:.]', stripped, re.IGNORECASE):
        return 'subject', stripped
    if re.match(r'^\d+[\.\)]\s+', stripped):
        return 'question', stripped
    if re.match(r'^(Q\d+|Question\s+\d+)', stripped, re.IGNORECASE):
        return 'question', stripped
    if re.match(r'^(Ans|Answer|A)\s*[:.\)]\s*', stripped, re.IGNORECASE):
        return 'answer_label', stripped
    if stripped.startswith('#'):
        return 'heading', stripped.lstrip('#').strip()
    return 'answer', stripped

def draw_page_background(c, width, height, settings):
    page_style = settings.get('page_style', 'blank')
    margin_left = settings.get('margin_left', 60)

    if page_style == 'cream':
        c.setFillColor(HexColor('#FFF8E7'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
    elif page_style == 'aged':
        c.setFillColor(HexColor('#F5E6C8'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColor(HexColor('#EAD5AA'))
        for _ in range(25):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            r = random.uniform(1, 5)
            c.circle(x, y, r, fill=1, stroke=0)
    elif page_style == 'recycled':
        c.setFillColor(HexColor('#DCD6CB'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#C4BBAF'))
        for _ in range(100):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            c.line(x, y, x + random.uniform(1, 3), y + random.uniform(1, 3))
    elif page_style == 'parchment':
        c.setFillColor(HexColor('#FCF5E5'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#F0E4C8'))
        c.setLineWidth(0.5)
        for _ in range(30):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            c.circle(x, y, random.uniform(10, 30), fill=0, stroke=1)
    elif page_style == 'legal_yellow':
        c.setFillColor(HexColor('#FFF9C4'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#E0E0E0'))
        c.setLineWidth(0.3)
        line_spacing = settings.get('line_spacing', 28)
        y = height - 60
        while y > 40:
            c.line(margin_left, y, width - 30, y)
            y -= line_spacing
        c.setStrokeColor(HexColor('#FF9999'))
        c.setLineWidth(0.8)
        c.line(margin_left, height, margin_left, 0)
    elif page_style == 'notebook':
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#E0E0E0'))
        c.setLineWidth(0.3)
        line_spacing = settings.get('line_spacing', 28)
        y = height - 60
        while y > 40:
            c.line(margin_left, y, width - 30, y)
            y -= line_spacing
        c.setStrokeColor(HexColor('#FF9999'))
        c.setLineWidth(0.8)
        c.line(margin_left, height, margin_left, 0)
    elif page_style == 'grid':
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#E8E8E8'))
        c.setLineWidth(0.2)
        step = 20
        x = 0
        while x <= width:
            c.line(x, 0, x, height)
            x += step
        y = 0
        while y <= height:
            c.line(0, y, width, y)
            y += step
    elif page_style == 'grain':
        c.setFillColor(HexColor('#FDFBF7'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColor(HexColor('#E8E4DC'))
        for _ in range(400):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            r = random.uniform(0.3, 1)
            c.circle(x, y, r, fill=1, stroke=0)
    elif page_style == 'fold_crease':
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#E8E8E8'))
        c.setLineWidth(0.5)
        crease_y = height * 0.35 + random.uniform(-20, 20)
        c.line(0, crease_y, width, crease_y + random.uniform(-3, 3))
    elif page_style == 'corner_shadow':
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        for (cx, cy) in [(0, 0), (width, 0), (0, height), (width, height)]:
            c.setFillColor(HexColor('#F0F0F0'))
            c.circle(cx, cy, 80, fill=1, stroke=0)
    else:
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(0, 0, width, height, fill=1, stroke=0)

def apply_realism(value, variation, enabled):
    if not enabled:
        return value
    return value + random.uniform(-variation, variation)

def generate_pdf(text, settings):
    page_size_name = settings.get('page_size', 'A4')
    page_size = PAGE_SIZES.get(page_size_name, A4)
    width, height = page_size

    font_name = settings.get('font', 'ComicNeue')
    if font_name not in AVAILABLE_FONTS:
        font_name = list(AVAILABLE_FONTS.keys())[0] if AVAILABLE_FONTS else 'Helvetica'

    font_size = settings.get('font_size', 18)
    line_spacing = settings.get('line_spacing', 28)
    ink_color = settings.get('ink_color', '#0A1F5C')
    margin_left = settings.get('margin_left', 60)
    margin_right = max(40, settings.get('margin_right', 40))
    margin_top = 50
    margin_bottom = 50

    spacing_variation = settings.get('spacing_variation', True)
    jitter = settings.get('jitter', True)
    ink_variation = settings.get('ink_variation', True)
    word_size_variation = settings.get('word_size_variation', True)
    baseline_shift = settings.get('baseline_shift', True)
    jitter_strength = settings.get('jitter_strength', 1.0)
    ink_flow = settings.get('ink_flow', True)
    gel_pen = settings.get('gel_pen', False)
    new_question_on_new_page = settings.get('new_question_on_new_page', False)
    margin_rule = settings.get('margin_rule', True)
    double_margin = settings.get('double_margin', False)
    bold_question = settings.get('bold_question', False)
    underline_headings = settings.get('underline_headings', False)
    signature_data = settings.get('signature_base64')
    page_numbers = settings.get('page_numbers', False)
    header_text = settings.get('header_text', '')
    footer_text = settings.get('footer_text', '')
    watermark_text = settings.get('watermark_text', '')

    filename = f"{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(GENERATED_DIR, filename)

    c = pdf_canvas.Canvas(filepath, pagesize=page_size)
    page_num = 1

    def draw_header_footer(page_num_val, total_pages=None):
        """Draw header, footer, page numbers, and watermark."""
        # Header
        if header_text:
            c.setFont(font_name, font_size - 2)
            c.setFillColor(HexColor('#666666'))
            header_y = height - 25
            tw = c.stringWidth(header_text, font_name, font_size - 2)
            c.drawString((width - tw) / 2, header_y, header_text)
        
        # Footer
        footer_y = 20
        footer_items = []
        if footer_text:
            footer_items.append(footer_text)
        if page_numbers:
            page_str = f"Page {page_num_val}"
            if total_pages:
                page_str += f" of {total_pages}"
            footer_items.append(page_str)
        
        if footer_items:
            footer_line = " • ".join(footer_items)
            c.setFont(font_name, font_size - 3)
            c.setFillColor(HexColor('#666666'))
            tw = c.stringWidth(footer_line, font_name, font_size - 3)
            c.drawString((width - tw) / 2, footer_y, footer_line)
        
        # Watermark
        if watermark_text:
            c.saveState()
            c.setFont(font_name, font_size + 10)
            c.setFillColor(HexColor('#E0E0E0'))
            c.rotate(45)
            tw = c.stringWidth(watermark_text, font_name, font_size + 10)
            c.drawString(width / 2 - tw / 2, height / 2, watermark_text)
            c.restoreState()

    draw_page_background(c, width, height, settings)
    page_style = settings.get('page_style', 'blank')
    if margin_rule and page_style not in ('legal_yellow', 'notebook'):
        c.setStrokeColor(HexColor('#FF9999'))
        c.setLineWidth(0.8)
        c.line(margin_left, height, margin_left, 0)
        if double_margin:
            c.line(margin_left + 12, height, margin_left + 12, 0)
    
    # Draw header/footer/watermark on first page
    # We'll need to count pages first, so we'll do this after content generation
    # For now, draw on first page
    draw_header_footer(page_num)

    lines = text.split('\n')
    y = height - margin_top
    x_base = margin_left + 10
    if margin_rule:
        x_base = margin_left + 16 if double_margin else margin_left + 10

    usable_width = width - margin_left - margin_right - 20
    if margin_rule:
        usable_width -= 4
    if double_margin:
        usable_width -= 4

    for line in lines:
        line_type, content = classify_line(line)

        if line_type == 'empty':
            y -= line_spacing * 0.6
            if y < margin_bottom:
                c.showPage()
                page_num += 1
                draw_page_background(c, width, height, settings)
                if margin_rule:
                    c.setStrokeColor(HexColor('#FF9999'))
                    c.setLineWidth(0.8)
                    c.line(margin_left, height, margin_left, 0)
                    if double_margin:
                        c.line(margin_left + 12, height, margin_left + 12, 0)
                draw_header_footer(page_num)
                y = height - margin_top
            continue

        if line_type == 'question' and new_question_on_new_page and y < height - margin_top - 50:
            c.showPage()
            page_num += 1
            draw_page_background(c, width, height, settings)
            if margin_rule:
                c.setStrokeColor(HexColor('#FF9999'))
                c.setLineWidth(0.8)
                c.line(margin_left, height, margin_left, 0)
                if double_margin:
                    c.line(margin_left + 12, height, margin_left + 12, 0)
            draw_header_footer(page_num)
            y = height - margin_top

        if line_type == 'title':
            c.setFont(font_name, font_size + 6)
            c.setFillColor(HexColor('#000000'))
            tw = c.stringWidth(content, font_name, font_size + 6)
            x = (width - tw) / 2
            jitter_y = apply_realism(0, 1.5, jitter)
            c.drawString(x, y + jitter_y, content)
            if underline_headings:
                c.setStrokeColor(HexColor('#000000'))
                c.setLineWidth(0.5)
                c.line(x, y - 2, x + tw, y - 2)
            y -= line_spacing * 1.8
        elif line_type in ('name', 'id', 'subject'):
            c.setFont(font_name, font_size + 1)
            c.setFillColor(HexColor('#000000'))
            jitter_x = apply_realism(0, 1, jitter)
            jitter_y = apply_realism(0, 1, jitter)
            c.drawString(x_base + jitter_x, y + jitter_y, content)
            y -= line_spacing * 1.3
        elif line_type == 'date':
            c.setFont(font_name, font_size + 1)
            c.setFillColor(HexColor('#000000'))
            tw = c.stringWidth(content, font_name, font_size + 1)
            x = width - margin_right - tw - 10
            jitter_y = apply_realism(0, 1, jitter)
            c.drawString(x, y + jitter_y, content)
            y -= line_spacing * 1.3
        elif line_type == 'question':
            qfs = font_size + 1
            c.setFont(font_name, qfs)
            c.setFillColor(HexColor('#000000'))
            wrapped = wrap_text(content, font_name, qfs, usable_width, c)
            for wl in wrapped:
                if y < margin_bottom:
                    c.showPage()
                    page_num += 1
                    draw_page_background(c, width, height, settings)
                    if margin_rule:
                        c.setStrokeColor(HexColor('#FF9999'))
                        c.setLineWidth(0.8)
                        c.line(margin_left, height, margin_left, 0)
                        if double_margin:
                            c.line(margin_left + 12, height, margin_left + 12, 0)
                    draw_header_footer(page_num)
                    y = height - margin_top
                jitter_x = apply_realism(0, 1.2, jitter)
                jitter_y = apply_realism(0, 1, jitter)
                if bold_question:
                    c.drawString(x_base + jitter_x + 0.4, y + jitter_y, wl)
                c.drawString(x_base + jitter_x, y + jitter_y, wl)
                y -= apply_realism(line_spacing, 2, spacing_variation)
            y -= line_spacing * 0.3
        elif line_type == 'heading':
            hfs = font_size + 3
            c.setFont(font_name, hfs)
            c.setFillColor(HexColor('#000000'))
            wrapped_heading = wrap_text(content, font_name, hfs, usable_width, c)
            for wh in wrapped_heading:
                jitter_y = apply_realism(0, 1, jitter)
                c.drawString(x_base, y + jitter_y, wh)
                if underline_headings:
                    tw = c.stringWidth(wh, font_name, hfs)
                    c.setStrokeColor(HexColor('#000000'))
                    c.setLineWidth(0.5)
                    c.line(x_base, y - 2, x_base + tw, y - 2)
                y -= line_spacing * 1.2
            y -= line_spacing * 0.3
        elif line_type == 'answer_label':
            actual_color = ink_color
            if ink_variation:
                base = HexColor(ink_color)
                r_var = min(1, max(0, base.red + random.uniform(-0.03, 0.03)))
                g_var = min(1, max(0, base.green + random.uniform(-0.03, 0.03)))
                b_var = min(1, max(0, base.blue + random.uniform(-0.03, 0.03)))
                c.setFillColor(Color(r_var, g_var, b_var))
            else:
                c.setFillColor(HexColor(actual_color))
            c.setFont(font_name, font_size)
            jitter_x = apply_realism(0, 1, jitter)
            jitter_y = apply_realism(0, 1, jitter)
            c.drawString(x_base + jitter_x, y + jitter_y, content)
            y -= apply_realism(line_spacing, 2, spacing_variation)
        else:
            realistic_settings = {
                'word_size_variation': word_size_variation,
                'baseline_shift': baseline_shift,
                'jitter_strength': jitter_strength,
                'ink_flow': ink_flow,
                'gel_pen': gel_pen,
            }
            wrapped = wrap_text(content, font_name, font_size, usable_width, c)
            for wl in wrapped:
                if y < margin_bottom:
                    c.showPage()
                    page_num += 1
                    draw_page_background(c, width, height, settings)
                    if margin_rule:
                        c.setStrokeColor(HexColor('#FF9999'))
                        c.setLineWidth(0.8)
                        c.line(margin_left, height, margin_left, 0)
                        if double_margin:
                            c.line(margin_left + 12, height, margin_left + 12, 0)
                    draw_header_footer(page_num)
                    y = height - margin_top
                jitter_x = apply_realism(0, 1.5, jitter)
                jitter_y = apply_realism(0, 1, jitter)
                start_y = y
                if (spacing_variation or jitter) and (word_size_variation or baseline_shift or ink_flow):
                    end_y = draw_realistic_text(c, wl, x_base + jitter_x, y + jitter_y, font_name, font_size, ink_color, realistic_settings, usable_width)
                    y = end_y - apply_realism(line_spacing, 1.5, spacing_variation)
                elif spacing_variation and jitter:
                    end_y = draw_jittered_text(c, wl, x_base + jitter_x, y + jitter_y, font_name, font_size, usable_width)
                    y = end_y - apply_realism(line_spacing, 1.5, spacing_variation)
                else:
                    if ink_variation or ink_flow:
                        base = HexColor(ink_color)
                        r = min(1, max(0, base.red + random.uniform(-0.03, 0.03)))
                        g = min(1, max(0, base.green + random.uniform(-0.03, 0.03)))
                        b = min(1, max(0, base.blue + random.uniform(-0.03, 0.03)))
                        c.setFillColor(Color(r, g, b))
                    else:
                        c.setFillColor(HexColor(ink_color))
                    c.setFont(font_name, font_size)
                    c.drawString(x_base + jitter_x, y + jitter_y, wl)
                    y -= apply_realism(line_spacing, 2, spacing_variation)

        if y < margin_bottom:
            c.showPage()
            page_num += 1
            draw_page_background(c, width, height, settings)
            if margin_rule:
                c.setStrokeColor(HexColor('#FF9999'))
                c.setLineWidth(0.8)
                c.line(margin_left, height, margin_left, 0)
                if double_margin:
                    c.line(margin_left + 12, height, margin_left + 12, 0)
            draw_header_footer(page_num)
            y = height - margin_top

    # Update footer with total page count on all pages
    total_pages = page_num
    # Note: ReportLab doesn't easily allow updating pages after creation
    # So we'll draw page numbers as we go, but total count will be approximate
    # For exact count, we'd need a two-pass approach
    
    if signature_data:
        try:
            import base64
            raw = signature_data
            if ',' in raw:
                raw = raw.split(',', 1)[1]
            img_data = base64.b64decode(raw)
            img = Image.open(BytesIO(img_data)).convert('RGBA')
            img.thumbnail((120, 50), Image.Resampling.LANCZOS)
            buf = BytesIO()
            img.save(buf, 'PNG')
            buf.seek(0)
            ir = ImageReader(buf)
            c.drawImage(ir, margin_left, margin_bottom, width=img.width, height=img.height)
        except Exception:
            pass

    c.save()
    return filename

def draw_jittered_text(c, text, x, y, font_name, font_size, max_width=None):
    """Draw text with per-character jitter; wrap to next line if max_width exceeded."""
    start_x = x
    current_y = y
    line_height = font_size * 1.35
    effective_max = (max_width - 4) if max_width else None
    for char in text:
        cw = c.stringWidth(char, font_name, font_size)
        extra = random.uniform(-0.2, 0.25)
        if effective_max and (x - start_x) + cw + max(0, extra) > effective_max and (x > start_x):
            x = start_x
            current_y -= line_height
            extra = 0
        jx = random.uniform(-0.4, 0.4)
        jy = random.uniform(-0.5, 0.5)
        c.drawString(x + jx, current_y + jy, char)
        x += cw + extra
    return current_y


def get_ink_color_with_flow(base_hex, position_ratio, ink_flow, gel_pen):
    """Ink flow: darker at start, slight fade at end. Gel pen: slightly richer/darker."""
    base = HexColor(base_hex)
    r, g, b = base.red, base.green, base.blue
    if ink_flow:
        # Slight darker at start (0), slight fade at end (1)
        fade = 1.0 - (position_ratio * 0.12)
        r, g, b = r * fade, g * fade, b * fade
    if gel_pen:
        r = min(1, r * 1.08)
        g = min(1, g * 1.02)
        b = min(1, b * 0.95)
    r = min(1, max(0, r + random.uniform(-0.02, 0.02)))
    g = min(1, max(0, g + random.uniform(-0.02, 0.02)))
    b = min(1, max(0, b + random.uniform(-0.02, 0.02)))
    return Color(r, g, b)


def draw_realistic_text(c, text, x, y, font_name, font_size, ink_color, settings, max_width=None):
    """Per-letter variation: word size variation, baseline shift, horizontal jitter. Respects max_width for wrapping."""
    word_size_var = settings.get('word_size_variation', True)
    baseline_shift = settings.get('baseline_shift', True)
    jitter_strength = settings.get('jitter_strength', 1.0)
    ink_flow = settings.get('ink_flow', True)
    gel_pen = settings.get('gel_pen', False)
    words = text.split()
    if not words:
        return y
    current_x = x
    current_y = y
    line_height = font_size * 1.4
    # Leave room for horizontal jitter so we never draw past margin
    effective_max = (max_width - 5) if max_width else None
    for i, word in enumerate(words):
        pos_ratio = i / max(1, len(words))
        color = get_ink_color_with_flow(ink_color, pos_ratio, ink_flow, gel_pen)
        c.setFillColor(color)
        size = font_size
        if word_size_var:
            size = font_size + random.uniform(-1.2, 1.5)
            size = max(font_size - 1, min(font_size + 2, size))
        c.setFont(font_name, size)
        word_width = c.stringWidth(word, font_name, size)
        space_width = c.stringWidth(' ', font_name, size) if current_x > x else 0
        random_spacing = random.uniform(-0.1, 0.2)
        current_line_width = current_x - x
        total_width_needed = current_line_width + space_width + word_width + max(0, random_spacing)
        if effective_max and total_width_needed > effective_max:
            if current_x > x:
                current_x = x
                current_y -= line_height
                space_width = 0
                random_spacing = 0
            else:
                # Word itself is too wide, truncate to fit
                if word_width > effective_max:
                    ratio = (effective_max - 2) / word_width
                    word = word[:max(1, int(len(word) * ratio))]
                    word_width = c.stringWidth(word, font_name, size)
        by = current_y
        if baseline_shift:
            by = current_y + random.uniform(-1.2, 1.2) * jitter_strength
        jx = random.uniform(-0.5, 0.5) * jitter_strength if jitter_strength else 0
        jy = random.uniform(-0.5, 0.5) * jitter_strength if jitter_strength else 0
        if current_x > x and space_width > 0:
            c.drawString(current_x + jx, by + jy, ' ')
            current_x += space_width
        c.drawString(current_x + jx, by + jy, word)
        current_x += word_width + random_spacing
        if effective_max and (current_x - x) > effective_max:
            current_x = x + effective_max
    return current_y

def wrap_text(text, font_name, font_size, max_width, c):
    """Wrap text to fit within max_width, with safety margin for variable font sizes and jitter."""
    words = text.split()
    lines = []
    current_line = ''
    # Use 85% so variable font size (+2pt) and per-char/word jitter don't overflow
    safe_width = max_width * 0.85
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        tw = c.stringWidth(test_line, font_name, font_size)
        if tw <= safe_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines if lines else ['']

def cleanup_old_files():
    while True:
        time.sleep(3600)
        now = time.time()
        for f in os.listdir(GENERATED_DIR):
            fp = os.path.join(GENERATED_DIR, f)
            if os.path.isfile(fp) and now - os.path.getmtime(fp) > 3600:
                try:
                    os.remove(fp)
                except Exception:
                    pass

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()


@app.route('/')
def index():
    fonts = list(AVAILABLE_FONTS.keys())
    return render_template('index.html', fonts=fonts)


@app.route('/api/fonts')
def get_fonts():
    return jsonify(list(AVAILABLE_FONTS.keys()))


@app.route('/api')
def api_info():
    """API documentation for programmatic use."""
    return jsonify({
        'name': 'Handwritten Assignment Studio API',
        'endpoints': {
            'POST /api/generate': {
                'description': 'Generate handwritten-style PDF from text',
                'body': {
                    'text': 'string (required)',
                    'font': 'string (optional)',
                    'font_size': 'int 10-36 (optional)',
                    'line_spacing': 'int (optional)',
                    'ink_color': '#hex (optional)',
                    'margin_left': 'int (optional)',
                    'page_style': 'blank|cream|aged|notebook|grid|grain|fold_crease|corner_shadow|... (optional)',
                    'page_size': 'A4|A3|A5|Letter|Legal (optional)',
                    'spacing_variation': 'bool (optional)',
                    'jitter': 'bool (optional)',
                    'ink_flow': 'bool (optional)',
                    'gel_pen': 'bool (optional)',
                    'margin_rule': 'bool (optional)',
                    'new_question_on_new_page': 'bool (optional)',
                    'signature_base64': 'data URL or base64 image (optional)',
                },
                'response': '{ "filename": "abc123.pdf" } or { "error": "..." }',
            },
            'GET /api/download/<filename>': 'Download generated PDF (filename from generate response)',
            'GET /api/export/<filename>/jpg|png': 'Export first page as image. Add ?scan=1 for scan effect.',
            'POST /api/auto-structure': 'Body: { "text": "..." }. Returns { "structured": "..." } with formatted headings/questions.',
        },
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = sanitize_text(data['text'][:50000])

    def _int(val, default, lo, hi):
        try:
            return max(lo, min(hi, int(val)))
        except (TypeError, ValueError):
            return default

    def _float(val, default, lo, hi):
        try:
            return max(lo, min(hi, float(val)))
        except (TypeError, ValueError):
            return default

    def _bool(val, default=True):
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        return default

    settings = {
        'font': data.get('font') or 'ComicNeue',
        'font_size': _int(data.get('font_size'), 18, 10, 36),
        'line_spacing': _int(data.get('line_spacing'), 28, 16, 50),
        'ink_color': data.get('ink_color') or '#0A1F5C',
        'margin_left': _int(data.get('margin_left'), 60, 20, 120),
        'page_style': data.get('page_style') or 'blank',
        'page_size': data.get('page_size') or 'A4',
        'spacing_variation': _bool(data.get('spacing_variation'), True),
        'jitter': _bool(data.get('jitter'), True),
        'ink_variation': _bool(data.get('ink_variation'), True),
        'word_size_variation': _bool(data.get('word_size_variation'), True),
        'baseline_shift': _bool(data.get('baseline_shift'), True),
        'jitter_strength': _float(data.get('jitter_strength'), 1.0, 0.2, 2.0),
        'ink_flow': _bool(data.get('ink_flow'), True),
        'gel_pen': _bool(data.get('gel_pen'), False),
        'new_question_on_new_page': _bool(data.get('new_question_on_new_page'), False),
        'margin_rule': _bool(data.get('margin_rule'), True),
        'double_margin': _bool(data.get('double_margin'), False),
        'bold_question': _bool(data.get('bold_question'), False),
        'underline_headings': _bool(data.get('underline_headings'), False),
        'signature_base64': data.get('signature_base64'),
        'page_numbers': _bool(data.get('page_numbers'), False),
        'header_text': (data.get('header_text') or '').strip()[:200],
        'footer_text': (data.get('footer_text') or '').strip()[:200],
        'watermark_text': (data.get('watermark_text') or '').strip()[:100],
    }

    ink = settings['ink_color']
    if not re.match(r'^#[0-9a-fA-F]{6}$', ink):
        settings['ink_color'] = '#0A1F5C'

    if settings['font'] not in AVAILABLE_FONTS:
        settings['font'] = list(AVAILABLE_FONTS.keys())[0] if AVAILABLE_FONTS else 'Helvetica'

    try:
        filename = generate_pdf(text, settings)
        return jsonify({'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_pdf(filename):
    if not re.match(r'^[a-f0-9]+\.pdf$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    filepath = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, as_attachment=True, download_name='handwritten_assignment.pdf')


def apply_scan_effect(img):
    """Apply scan effect: slight tilt, minor blur, subtle noise, light border shadow."""
    from PIL import ImageFilter, ImageOps
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False
    
    img = img.convert('RGB')
    w, h = img.size
    tilt_deg = random.uniform(0.5, 1.0)
    rotated = img.rotate(-tilt_deg, expand=True, resample=Image.Resampling.BICUBIC)
    rotated = rotated.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    if has_numpy:
        arr = np.array(rotated, dtype=np.uint8)
        noise = np.random.randint(-6, 7, arr.shape, dtype=np.int16)
        arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        out = Image.fromarray(arr)
    else:
        pixels = list(rotated.getdata())
        noisy_pixels = []
        for r, g, b in pixels:
            n = random.uniform(-6, 6)
            r = max(0, min(255, int(r + n)))
            g = max(0, min(255, int(g + n)))
            b = max(0, min(255, int(b + n)))
            noisy_pixels.append((r, g, b))
        out = Image.new('RGB', rotated.size)
        out.putdata(noisy_pixels)
    
    pad = 16
    out = ImageOps.expand(out, border=pad, fill=(238, 236, 232))
    return out


def _pdf_to_image(filepath, page_index=0):
    """Convert a single PDF page to PIL Image."""
    import fitz  # PyMuPDF
    doc = fitz.open(filepath)
    try:
        page = doc[page_index]
        zoom = 200 / 72  # 200 dpi
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        return img
    finally:
        doc.close()


def _pdf_page_count(filepath):
    """Return number of pages in PDF."""
    import fitz
    doc = fitz.open(filepath)
    try:
        return len(doc)
    finally:
        doc.close()


def _pdf_all_pages_to_images(filepath):
    """Convert all PDF pages to list of PIL Images."""
    import fitz
    doc = fitz.open(filepath)
    images = []
    try:
        zoom = 200 / 72
        mat = fitz.Matrix(zoom, zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    finally:
        doc.close()


@app.route('/api/export/<filename>/<fmt>')
def export_file(filename, fmt):
    if fmt not in ('jpg', 'png'):
        return jsonify({'error': 'Invalid format'}), 400
    if not re.match(r'^[a-f0-9]+\.pdf$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    filepath = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    scan_effect = request.args.get('scan', '0') == '1'

    try:
        images = _pdf_all_pages_to_images(filepath)
    except ImportError:
        return jsonify({'error': 'Install pymupdf: pip install pymupdf'}), 501
    except Exception as e:
        app.logger.error(f'Export error: {e}')
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

    if not images:
        return jsonify({'error': 'No pages in PDF'}), 500

    ext = 'jpg' if fmt == 'jpg' else 'png'
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, img in enumerate(images):
            if scan_effect:
                try:
                    img = apply_scan_effect(img)
                except Exception as e:
                    app.logger.warning(f'Scan effect failed on page {i+1}: {e}')
            page_buf = BytesIO()
            if fmt == 'jpg':
                img.save(page_buf, 'JPEG', quality=95)
            else:
                img.save(page_buf, 'PNG')
            page_buf.seek(0)
            zf.writestr(f'page_{i+1}.{ext}', page_buf.getvalue())
    zip_buf.seek(0)
    return send_file(zip_buf, mimetype='application/zip', as_attachment=True,
                     download_name='handwritten_assignment_all_pages.zip')


@app.route('/api/auto-structure', methods=['POST'])
def auto_structure():
    """Restructure pasted text into proper heading, numbered questions, paragraphs."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    text = (data['text'] or '').strip()
    if not text:
        return jsonify({'structured': ''})
    lines = text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            out.append('')
            i += 1
            continue
        upper = stripped.upper()
        if any(kw in upper for kw in ['ASSIGNMENT', 'HOMEWORK', 'HOME WORK']):
            out.append(stripped)
            i += 1
            continue
        if re.match(r'^(NAME|STUDENT|ID|ROLL|DATE|SUBJECT|COURSE|CLASS)\s*[:.]', stripped, re.IGNORECASE):
            out.append(stripped)
            i += 1
            continue
        if re.match(r'^\d+[\.\)]\s+', stripped) or re.match(r'^(Q\d+|Question\s+\d+)', stripped, re.IGNORECASE):
            out.append(stripped)
            i += 1
            continue
        if re.match(r'^(Ans|Answer|A)\s*[:.\)]\s*', stripped, re.IGNORECASE):
            out.append(stripped)
            i += 1
            continue
        if stripped.startswith('#'):
            out.append(stripped)
            i += 1
            continue
        if out and out[-1] and not out[-1].strip().endswith(('.', '!', '?')) and not re.match(r'^(Ans|Answer|Q\d+)', out[-1], re.I):
            out[-1] = out[-1] + ' ' + stripped
        else:
            out.append(stripped)
        i += 1
    result = '\n'.join(out)
    return jsonify({'structured': result})


@app.route('/api/preview', methods=['POST'])
def preview():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = sanitize_text(data['text'][:50000])
    lines = text.split('\n')
    preview_lines = []
    for line in lines:
        line_type, content = classify_line(line)
        preview_lines.append({'type': line_type, 'content': content})

    return jsonify({'lines': preview_lines})


@app.route('/generated/<filename>')
def serve_generated(filename):
    if not re.match(r'^[a-f0-9]+\.pdf$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    return send_from_directory(GENERATED_DIR, filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
