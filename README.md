# Handwritten Assignment Studio

A full-stack web application that converts academic text into ultra-realistic handwritten-style PDFs.

## Features
- Text input with live preview
- Multiple handwriting fonts
- Various page styles (notebook, grid, cream, etc.)
- Page numbering, headers, footers, watermarks
- Undo/Redo functionality
- File import
- Print functionality
- Created by Suhana Kousar

## Deployment Options

### Option 1: Render.com (Recommended for Flask)
1. Go to https://render.com
2. Create a new Web Service
3. Connect your GitHub repository
4. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - Environment: Python 3
5. Add environment variable: `SESSION_SECRET` (generate a random secret)

### Option 2: Railway.app
1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repository
4. Railway will auto-detect Python and install dependencies
5. Add environment variable: `SESSION_SECRET`

### Option 3: PythonAnywhere
1. Go to https://www.pythonanywhere.com
2. Upload your files
3. Create a web app
4. Set WSGI file to point to app.py
5. Add environment variables

### Option 4: Netlify (Requires Refactoring)
Netlify doesn't natively support Flask. You would need to:
- Convert Flask routes to Netlify Functions (serverless)
- Or use Netlify as frontend + separate Flask backend

## Local Development
```bash
pip install -r requirements.txt
python app.py
```

## Environment Variables
- `SESSION_SECRET`: Flask session secret key (required for production)
