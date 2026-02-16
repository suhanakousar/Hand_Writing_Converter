# Deployment Guide for Handwritten Assignment Studio

## ⚠️ Important: Netlify Limitation

**Netlify does NOT natively support Flask applications.** Netlify is designed for:
- Static websites
- Serverless functions (limited Python support)
- JAMstack applications

## ✅ Recommended Deployment Options

### Option 1: Render.com (EASIEST - Recommended)

1. **Go to**: https://render.com
2. **Sign up/Login** with GitHub
3. **Click**: "New +" → "Web Service"
4. **Connect Repository**: Select `suhanakousar/Hand_Writing_Converter`
5. **Configure**:
   ```
   Name: writestudio (or your preferred name)
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --bind 0.0.0.0:$PORT app:app
   ```
6. **Add Environment Variable**:
   - Key: `SESSION_SECRET`
   - Value: Generate using: `python -c "import secrets; print(secrets.token_hex(32))"`
7. **Click**: "Create Web Service"
8. **Wait** for deployment (5-10 minutes)
9. **Your app will be live** at: `https://writestudio.onrender.com`

**Free Tier**: 750 hours/month, sleeps after 15 min inactivity

---

### Option 2: Railway.app (FASTEST)

1. **Go to**: https://railway.app
2. **Sign up/Login** with GitHub
3. **Click**: "New Project" → "Deploy from GitHub"
4. **Select**: `Hand_Writing_Converter` repository
5. **Railway auto-detects** Python and installs dependencies
6. **Add Environment Variable**:
   - Key: `SESSION_SECRET`
   - Value: (generate random secret)
7. **Deploy** - Railway handles everything automatically
8. **Your app will be live** at: `https://your-app-name.up.railway.app`

**Free Tier**: $5 credit/month, no sleep

---

### Option 3: PythonAnywhere (FREE Forever)

1. **Go to**: https://www.pythonanywhere.com
2. **Sign up** for free account
3. **Upload files** via Files tab
4. **Create Web App**:
   - Choose "Manual configuration"
   - Python 3.11
   - Point WSGI file to: `/home/yourusername/mysite/app.py`
5. **Edit WSGI file**:
   ```python
   import sys
   path = '/home/yourusername/mysite'
   if path not in sys.path:
       sys.path.append(path)
   from app import app as application
   ```
6. **Add environment variable** in Web tab
7. **Reload** web app

**Free Tier**: Limited but permanent

---

### Option 4: Fly.io (Modern & Fast)

1. **Install Fly CLI**: https://fly.io/docs/getting-started/installing-flyctl/
2. **Login**: `fly auth login`
3. **Initialize**: `fly launch`
4. **Deploy**: `fly deploy`
5. **Your app**: `https://your-app-name.fly.dev`

**Free Tier**: 3 shared VMs

---

## ❌ Why Not Netlify?

Netlify requires:
- Converting Flask routes to serverless functions (major refactoring)
- Each API endpoint needs separate function
- Complex state management
- Limited Python library support
- No persistent file storage for PDFs

**Better Alternative**: Use Netlify for frontend + Render/Railway for backend API

---

## Quick Start Commands

### For Render.com:
```bash
# Already done - just connect repo on Render dashboard
```

### For Railway.app:
```bash
# Already done - just connect repo on Railway dashboard
```

### Generate SESSION_SECRET:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Post-Deployment Checklist

- [ ] Set `SESSION_SECRET` environment variable
- [ ] Test PDF generation
- [ ] Verify fonts are loading
- [ ] Check file uploads work
- [ ] Test all features
- [ ] Update README with live URL

---

## Need Help?

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **PythonAnywhere Docs**: https://help.pythonanywhere.com
