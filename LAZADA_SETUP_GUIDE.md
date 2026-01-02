# 🎯 Lazada CallSim - Complete Setup Guide

**Senior High School Project**  
**Version**: 2.0 (Lazada Edition with Google Vertex AI)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Google Cloud Setup](#google-cloud-setup)
4. [Backend Setup](#backend-setup)
5. [Database Setup](#database-setup)
6. [Frontend Setup](#frontend-setup)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This simulator trains students to handle Lazada customer support calls for:
- ✅ **Delivery Issues** (tracking, late packages, rider location)
- ✅ **Order Problems** (wrong items, refunds, cancellations)
- ✅ **Internet/App Issues** (login errors, loading problems)

The AI will **politely decline** any other topics.

**Total Setup Time**: ~15-20 minutes

---

## Prerequisites

### Required
- ✅ **Python 3.10 or higher**
- ✅ **Google Cloud account** (free tier available)
- ✅ **VS Code** (recommended) with Live Server extension
- ✅ **Internet connection**

### Optional
- Git (for version control)
- Postman (for API testing)

### Check Python Version
```bash
python --version
# Should show: Python 3.10.x or higher
```

---

## Google Cloud Setup

### Step 1: Create Google Cloud Project

1. **Sign in to Google Cloud Console**
   - Visit: https://console.cloud.google.com
   - Use your Google account

2. **Create New Project**
   ```
   - Click "Select a project" dropdown
   - Click "New Project"
   - Project name: lazada-callsim-yourname
   - Click "Create"
   ```

3. **Note Your Project ID**
   - After creation, you'll see: `lazada-callsim-yourname-123456`
   - **Copy this ID** - you'll need it later!

### Step 2: Enable Vertex AI API

1. **Open API Library**
   ```
   - Navigation Menu (≡) → APIs & Services → Library
   - Search: "Vertex AI API"
   - Click on "Vertex AI API"
   - Click "Enable"
   - Wait 1-2 minutes for activation
   ```

2. **Verify Activation**
   - You should see "API Enabled" badge
   - If not, refresh the page

### Step 3: Create Service Account

1. **Navigate to IAM**
   ```
   - Navigation Menu (≡) → IAM & Admin → Service Accounts
   - Click "Create Service Account"
   ```

2. **Configure Service Account**
   ```
   Service account name: callsim-ai
   Service account ID: callsim-ai@your-project.iam.gserviceaccount.com
   Description: Lazada CallSim AI Service
   Click "Create and Continue"
   ```

3. **Grant Permissions**
   ```
   Role: Vertex AI User
   Click "Continue"
   Click "Done"
   ```

### Step 4: Generate Credentials

1. **Create JSON Key**
   ```
   - Find "callsim-ai" in service accounts list
   - Click three dots (⋮) → "Manage keys"
   - Click "Add Key" → "Create new key"
   - Select "JSON"
   - Click "Create"
   ```

2. **Download & Store**
   ```
   - File downloads as: callsim-ai-xxxxx.json
   - Rename to: vertex-ai-credentials.json
   - Move to: d:\PAUL\backend\
   ```

⚠️ **SECURITY WARNING**: Never commit this file to Git! It contains secrets.

---

## Backend Setup

### Step 1: Install Dependencies

```bash
# Navigate to backend folder
cd d:\PAUL\backend

# Install Python packages
pip install -r requirements.txt
```

**Expected output:**
```
Collecting Flask==3.0.0
Collecting google-cloud-aiplatform==1.75.0
Collecting gTTS==2.4.0
...
Successfully installed Flask-3.0.0 ...
```

### Step 2: Configure Environment

1. **Create .env file**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file**
   ```bash
   notepad .env
   ```

3. **Update these values:**
   ```env
   # Flask Configuration
   FLASK_ENV=development
   FLASK_DEBUG=True
   PORT=5000

   # Secret Keys (Generate new ones!)
   FLASK_SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-here

   # CORS (Keep as is for local development)
   ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

   # Database (SQLite - local file)
   DATABASE_URL=sqlite:///callsim.db

   # Google Cloud Vertex AI
   GOOGLE_CLOUD_PROJECT=your-project-id-from-step-1
   GOOGLE_APPLICATION_CREDENTIALS=backend/vertex-ai-credentials.json
   ```

4. **Generate secure keys (optional but recommended):**
   ```bash
   python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
   ```
   
   Copy the generated keys into your `.env` file.

---

## Database Setup

### Step 1: Initialize Database

```bash
cd d:\PAUL\backend
python init_db.py
```

**Expected output:**
```
============================================================
CallSim Database Initialization
============================================================
✅ Database tables created successfully!
✅ Admin user created: admin@callsim.local
   Password: admin123
   (Change this password after first login!)
============================================================
```

### Step 2: Run Migration (if upgrading from old version)

```bash
python migrate_db.py
```

**Expected output:**
```
============================================================
Lazada CallSim - Database Migration
============================================================
✅ Adding recording_directory to call_sessions...
✅ Adding recording_path to chat_messages...
============================================================
✅ Migration completed successfully!
============================================================
```

---

## Frontend Setup

### Step 1: Install VS Code Live Server

1. **Open VS Code**
2. **Install Extension**
   ```
   - Click Extensions (Ctrl+Shift+X)
   - Search: "Live Server"
   - Click Install on "Live Server by Ritwick Dey"
   ```

### Step 2: Configure CORS

The backend is already configured to allow `http://localhost:5500` (Live Server's default port).

If you use a different port, update `ALLOWED_ORIGINS` in `.env`.

---

## Testing

### Step 1: Start Backend Server

```bash
cd d:\PAUL\backend
python app_simple.py
```

**Expected output:**
```
============================================================
CallSim - Lazada Customer Support Simulator
============================================================
Frontend: http://localhost:5500
API Docs: http://localhost:5000/apidocs
API: http://localhost:5000/api/v1/
Vertex AI: Configured
============================================================
 * Running on http://0.0.0.0:5000
```

✅ If you see "Vertex AI: Configured" - you're good!  
❌ If you see "Vertex AI: Not Configured" - check your `.env` file

### Step 2: Start Frontend

1. **Open VS Code**
2. **Open** `d:\PAUL\index.html`
3. **Right-click** → "Open with Live Server"
4. **Browser opens** at `http://localhost:5500`

### Step 3: Test Login

1. **Click through intro screen**
2. **Click "START"** in main menu
3. **Login with default admin:**
   ```
   Email: admin@callsim.local
   Password: admin123
   ```

### Step 4: Test AI Response

1. **Start a call session**
2. **Send a message**: "My package is late"
3. **Wait for AI response** (should mention Lazada and offer help)
4. **Test constraint**: "Can you help me cook rice?"
5. **AI should decline**: "I can only assist with delivery, order, or app issues..."

---

## Troubleshooting

### Problem: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: "Vertex AI not configured"
**Checklist:**
- [ ] `.env` file has correct `GOOGLE_CLOUD_PROJECT`
- [ ] `vertex-ai-credentials.json` exists in `backend/`
- [ ] Path in `.env` is correct: `backend/vertex-ai-credentials.json`
- [ ] Vertex AI API is enabled in Google Cloud Console

### Problem: "Permission denied" from Google Cloud
**Solution:**
```
1. Go to Google Cloud Console
2. IAM & Admin → Service Accounts
3. Find "callsim-ai"
4. Grant "Vertex AI User" role
```

### Problem: CORS error in browser
**Solution:**
```env
# In .env, add your frontend URL:
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000
```

### Problem: Database error
**Solution:**
```bash
# Delete and recreate database
del callsim.db
python init_db.py
```

### Problem: Port 5000 already in use
**Solution:**
```env
# In .env, change port:
PORT=5001
```
Then access backend at `http://localhost:5001`

---

## Next Steps

After successful setup:

1. **Change admin password**
   - Login as admin
   - Go to settings
   - Update password

2. **Create student accounts**
   - Register as trainer/student
   - Or use admin panel to create users

3. **Start training**
   - Begin call sessions
   - Practice Lazada support scenarios
   - Review transcripts and scores

4. **Explore API docs**
   - Visit: http://localhost:5000/apidocs
   - Learn about available endpoints

---

## 📚 Additional Resources

- **[README.md](../README.md)** - Project overview
- **[VERTEX_AI_SETUP.md](../VERTEX_AI_SETUP.md)** - Detailed Google Cloud guide
- **[GET_STARTED.md](../GET_STARTED.md)** - Quick reference

---

## ✅ Setup Complete!

You should now have:
- ✅ Backend server running on port 5000
- ✅ Frontend accessible at http://localhost:5500
- ✅ Vertex AI configured and working
- ✅ Database initialized
- ✅ Default admin account created

**Ready to train!** 🎉

Start your first Lazada customer support simulation and practice handling delivery, order, and app issues!
