# Handwritten Assignment Studio

## Overview
A full-stack web application that converts academic text into ultra-realistic handwritten-style PDFs. Users paste their assignment text and generate PDFs with advanced formatting controls including font selection, page styles, realism effects, and more.

## Tech Stack
- **Backend**: Python 3.11, Flask, ReportLab (PDF generation), Pillow
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Server**: Gunicorn-ready

## Project Architecture
```
/
├── app.py                  # Flask backend, PDF generation engine
├── static/
│   ├── style.css           # Main UI styles
│   ├── preview.css         # Live preview styles
│   └── script.js           # Frontend logic, live preview, API calls
├── templates/
│   └── index.html          # Main page template
├── fonts/                  # Handwriting font files (.ttf)
│   ├── DancingScript-Regular.ttf
│   ├── Pacifico-Regular.ttf
│   └── ComicNeue-Regular.ttf
└── generated/              # Temporary PDF output directory (auto-cleaned)
```

## Key Features
- Text input with word/character counter
- Auto-detection of titles, names, dates, questions, answers
- Multiple handwriting fonts (DancingScript, Pacifico, ComicNeue)
- Page styles: Blank, Cream, Aged, Notebook, Grid
- Realism effects: spacing variation, letter jitter, ink variation
- Live preview before generating
- PDF download with multi-page support
- Session settings persistence via localStorage

## Running the App
- Development: `python app.py` (runs on port 5000)
- Production: `gunicorn --bind 0.0.0.0:5000 app:app`

## Environment Variables
- `SESSION_SECRET`: Flask session secret key
