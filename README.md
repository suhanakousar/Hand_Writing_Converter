# Handwritten Assignment Studio

A full-stack web application that converts academic text into ultra-realistic handwritten-style PDFs.

**Created by Suhana Kousar**

## Features
- Text input with live preview
- Multiple handwriting fonts
- Various page styles (notebook, grid, cream, etc.)
- Page numbering, headers, footers, watermarks
- Undo/Redo functionality
- File import
- Print functionality
- Export to PDF, JPG, PNG

## 🚀 Quick Deploy

### Recommended: Render.com (Easiest)

1. Go to https://render.com and sign up with GitHub
2. Click "New +" → "Web Service"
3. Connect repository: `suhanakousar/Hand_Writing_Converter`
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
5. Add environment variable: `SESSION_SECRET` (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
6. Deploy!

**See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions**

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# App runs on http://localhost:5000
```

## Environment Variables

- `SESSION_SECRET`: Flask session secret key (required for production)

## Tech Stack

- **Backend**: Python 3.11, Flask, ReportLab, Pillow
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Server**: Gunicorn

## License

Created by Suhana Kousar
