import os
import re
import uuid
import random
import html
import time
import threading
from io import BytesIO

from flask import (Flask, render_template, request, jsonify, send_file,
                   session, send_from_directory)
from reportlab.lib.pagesizes import A4, LETTER, LEGAL
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-prod')

FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
GENERATED_DIR = os.path.join(os.path.dirname(__file__), 'generated')
os.makedirs(GENERATED_DIR, exist_ok=True)

AVAILABLE_FONTS = {}

def register_fonts():
    font_files = {
        'DancingScript': 'DancingScript-Regular.ttf',
        'Pacifico': 'Pacifico-Regular.ttf',
        'ComicNeue': 'ComicNeue-Regular.ttf',
    }
    for name, filename in font_files.items():
        path = os.path.join(FONTS_DIR, filename)
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                AVAILABLE_FONTS[name] = path
            except Exception:
                pass

register_fonts()

PAGE_SIZES = {
    'A4': A4,
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
        for _ in range(15):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            r = random.uniform(2, 8)
            c.circle(x, y, r, fill=1, stroke=0)
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
    margin_right = 30
    margin_top = 50
    margin_bottom = 50

    spacing_variation = settings.get('spacing_variation', True)
    jitter = settings.get('jitter', True)
    ink_variation = settings.get('ink_variation', True)

    filename = f"{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(GENERATED_DIR, filename)

    c = pdf_canvas.Canvas(filepath, pagesize=page_size)

    draw_page_background(c, width, height, settings)

    lines = text.split('\n')
    y = height - margin_top
    x_base = margin_left + 10

    usable_width = width - margin_left - margin_right - 20

    for line in lines:
        line_type, content = classify_line(line)

        if line_type == 'empty':
            y -= line_spacing * 0.6
            if y < margin_bottom:
                c.showPage()
                draw_page_background(c, width, height, settings)
                y = height - margin_top
            continue

        if line_type == 'title':
            c.setFont(font_name, font_size + 6)
            c.setFillColor(HexColor('#000000'))
            tw = c.stringWidth(content, font_name, font_size + 6)
            x = (width - tw) / 2
            jitter_y = apply_realism(0, 1.5, jitter)
            c.drawString(x, y + jitter_y, content)
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
            c.setFont(font_name, font_size + 1)
            c.setFillColor(HexColor('#000000'))
            wrapped = wrap_text(content, font_name, font_size + 1, usable_width, c)
            for wl in wrapped:
                if y < margin_bottom:
                    c.showPage()
                    draw_page_background(c, width, height, settings)
                    y = height - margin_top
                jitter_x = apply_realism(0, 1.2, jitter)
                jitter_y = apply_realism(0, 1, jitter)
                c.drawString(x_base + jitter_x, y + jitter_y, wl)
                y -= apply_realism(line_spacing, 2, spacing_variation)
            y -= line_spacing * 0.3
        elif line_type == 'heading':
            c.setFont(font_name, font_size + 3)
            c.setFillColor(HexColor('#000000'))
            jitter_y = apply_realism(0, 1, jitter)
            c.drawString(x_base, y + jitter_y, content)
            y -= line_spacing * 1.5
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
            wrapped = wrap_text(content, font_name, font_size, usable_width, c)
            for wl in wrapped:
                if y < margin_bottom:
                    c.showPage()
                    draw_page_background(c, width, height, settings)
                    y = height - margin_top
                jitter_x = apply_realism(0, 1.5, jitter)
                jitter_y = apply_realism(0, 1, jitter)
                char_spacing = apply_realism(0, 0.3, spacing_variation)
                if spacing_variation and jitter:
                    draw_jittered_text(c, wl, x_base + jitter_x, y + jitter_y, font_name, font_size)
                else:
                    c.drawString(x_base + jitter_x, y + jitter_y, wl)
                y -= apply_realism(line_spacing, 2, spacing_variation)

        if y < margin_bottom:
            c.showPage()
            draw_page_background(c, width, height, settings)
            y = height - margin_top

    c.save()
    return filename

def draw_jittered_text(c, text, x, y, font_name, font_size):
    for char in text:
        jx = random.uniform(-0.4, 0.4)
        jy = random.uniform(-0.5, 0.5)
        c.drawString(x + jx, y + jy, char)
        x += c.stringWidth(char, font_name, font_size) + random.uniform(-0.2, 0.3)

def wrap_text(text, font_name, font_size, max_width, c):
    words = text.split()
    lines = []
    current_line = ''
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        tw = c.stringWidth(test_line, font_name, font_size)
        if tw <= max_width:
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


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = sanitize_text(data['text'][:50000])
    settings = {
        'font': data.get('font', 'ComicNeue'),
        'font_size': max(10, min(36, int(data.get('font_size', 18)))),
        'line_spacing': max(16, min(50, int(data.get('line_spacing', 28)))),
        'ink_color': data.get('ink_color', '#0A1F5C'),
        'margin_left': max(20, min(120, int(data.get('margin_left', 60)))),
        'page_style': data.get('page_style', 'blank'),
        'page_size': data.get('page_size', 'A4'),
        'spacing_variation': data.get('spacing_variation', True),
        'jitter': data.get('jitter', True),
        'ink_variation': data.get('ink_variation', True),
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


@app.route('/api/export/<filename>/<fmt>')
def export_file(filename, fmt):
    if fmt not in ('jpg', 'png'):
        return jsonify({'error': 'Invalid format'}), 400
    if not re.match(r'^[a-f0-9]+\.pdf$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    filepath = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        from pdf2image import convert_from_path
        images = convert_from_path(filepath, first_page=1, last_page=1, dpi=200)
        img = images[0]
        buf = BytesIO()
        if fmt == 'jpg':
            img.save(buf, 'JPEG', quality=95)
            mime = 'image/jpeg'
            ext = 'jpg'
        else:
            img.save(buf, 'PNG')
            mime = 'image/png'
            ext = 'png'
        buf.seek(0)
        return send_file(buf, mimetype=mime, as_attachment=True,
                         download_name=f'handwritten_assignment.{ext}')
    except ImportError:
        from reportlab.graphics import renderPM
        from reportlab.graphics.shapes import Drawing
        return jsonify({'error': 'Image export requires pdf2image and poppler. PDF download is available.'}), 501


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
