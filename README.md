# CallSim - Lazada Customer Support Simulator

**AI-Powered Call Center Training for Senior High School**

---

## 🎯 What Is This?

A web-based training simulator where you practice being a **Lazada Customer Support Agent**. The AI simulates real customers with delivery, order, and app problems.

### **Supported Issues**
✅ **Delivery**: Late packages, tracking, rider location  
✅ **Orders**: Wrong items, refunds, cancellations, damages  
✅ **Internet/App**: Login errors, connection issues, loading problems  

❌ **NOT Supported**: Anything else (AI will politely decline)

---

## 🚀 Quick Start

### **5-Minute Setup**

1. **Install Python**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set Up Google Vertex AI**
   - Follow **[VERTEX_AI_SETUP.md](VERTEX_AI_SETUP.md)** (detailed guide)
   - Get your Google Cloud project ID
   - Download credentials JSON file

4. **Configure Environment**
   ```bash
   cp .env.example .env
   notepad .env
   ```
   
   Add to `.env`:
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=backend/vertex-ai-credentials.json
   ```

5. **Initialize Database**
   ```bash
   cd backend
   python init_db.py
   ```

6. **Start CallSim**
   
   **Option A: One-Click Start (Recommended)**
   ```powershell
   .\start-all.ps1
   ```
   This starts both backend and frontend, then opens your browser automatically!
   
   **Option B: Manual Start**
   ```powershell
   # Terminal 1 - Backend
   .\start-callsim.ps1
   
   # Terminal 2 - Frontend  
   .\start-frontend.ps1
   ```
   Then open: http://localhost:5500/index.html

---

## 📚 Documentation

- **[VERTEX_AI_SETUP.md](VERTEX_AI_SETUP.md)** ← Start here! Complete Google Cloud setup
- **[GET_STARTED.md](GET_STARTED.md)** - Quick reference
- **[SIMPLIFICATION_NOTES.md](SIMPLIFICATION_NOTES.md)** - Architecture notes

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Model | Google Vertex AI (Gemini 1.5 Flash) |
| Backend | Flask (Python) |
| Database | SQLite |
| Auth | JWT + BCrypt |
| TTS | gTTS (Google Text-to-Speech) |
| Frontend | HTML5, CSS3, Vanilla JS |

---

## 🎓 For Students

### **Learning Goals**
- Practice customer service communication
- Handle common Lazada support issues
- Build professional phone etiquette
- Learn problem-solving under constraints
- Understand AI-assisted workflows

### **Evaluation System**
Your calls are scored on:
- **Overall Performance** (0-100)
- **Empathy** (How caring were you?)
- **Clarity** (How clear was your communication?)
- **Problem-Solving** (Did you help the customer?)

---

## 🎨 Lazada Branding

**Colors Used:**
- Navy Blue: `#0F1111` (primary background)
- Orange: `#F57224` (accent, buttons, highlights)

**Why these colors?**
They match Lazada's official brand identity!

---

## 🔒 Security Features

Even though this is educational, we included:
- ✅ JWT authentication
- ✅ Password hashing (BCrypt)
- ✅ Input sanitization
- ✅ CORS protection
- ✅ Rate limiting
- ✅ Audit logging

---

## 💰 Cost

**FREE for students!**

Gemini 1.5 Flash free tier:
- 1,500 requests/day
- $0 cost for typical school use
- ~500 practice calls = FREE

See [VERTEX_AI_SETUP.md](VERTEX_AI_SETUP.md#-pricing--free-tier) for details.

---

## 📁 Project Structure

```
d:\PAUL\
├── backend/
│   ├── app_simple.py              # Main Flask app
│   ├── models.py                  # Database models
│   ├── auth.py                    # Authentication
│   ├── database.py                # DB config
│   ├── schemas.py                 # Validation
│   ├── requirements.txt           # Dependencies
│   ├── .env.example               # Config template
│   └── vertex-ai-credentials.json # Google Cloud key (YOU create this)
├── html/
│   ├── intro.html                 # Landing page
│   ├── main-menu.html             # Main menu
│   └── call.html                  # Call interface
├── css/                           # Lazada-themed styles
├── js/                            # Frontend logic
└── README.md                      # This file
```

---

## 🚀 What's Next?

### **After Basic Setup:**
1. Create admin account (first user)
2. Add trainer/student accounts
3. Start practice sessions
4. Review call transcripts
5. Evaluate performance

### **Future Enhancements:**
- Voice recognition (Web Speech API)
- Real-time pronunciation feedback
- More scenario types
- Performance analytics dashboard
- Export reports for grading

---

## 🆘 Help & Troubleshooting

### **Can't start server?**
- Check Python version: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Verify `.env` file exists with correct values

### **Vertex AI not working?**
- Follow [VERTEX_AI_SETUP.md](VERTEX_AI_SETUP.md) step-by-step
- Verify project ID and credentials path
- Check API is enabled in Google Cloud Console

### **Frontend not loading?**
- Use Live Server extension in VS Code
- Or open `index.html` directly
- Check CORS settings in `.env`

### **🎤 Microphone Not Working? ("not-allowed" error)**

**Common Causes:**
1. **Browser Permission Denied** - You blocked microphone access
2. **Not Using HTTPS** - Browsers require HTTPS for microphone (except localhost)
3. **No Microphone Connected** - Check your device settings

**Solutions:**

✅ **Grant Permission:**
- Look for the 🔒 icon in your browser's address bar
- Click it and allow microphone access
- Or click the "Grant Permission" button that appears on the page

✅ **Check Browser Settings:**
- **Chrome**: `chrome://settings/content/microphone`
- **Edge**: `edge://settings/content/microphone`
- **Firefox**: Settings → Privacy & Security → Permissions → Microphone

✅ **Use HTTPS or Localhost:**
- Access via `http://localhost:5500` or `http://127.0.0.1:5500`
- Or use Live Server which provides a local server
- For production, use HTTPS

✅ **Test Your Microphone:**
- Check Windows Sound Settings
- Make sure a microphone is connected and not muted
- Try: Settings → System → Sound → Input

**Still Not Working?**
- Type your complaints instead of speaking
- The text input works without microphone permissions
- The AI will respond the same way

---

## 📝 License & Credits

**Senior High School Project - 2025**

- **AI Model**: Google Vertex AI (Gemini 1.5 Flash)
- **Training Context**: Lazada Customer Support
- **Purpose**: Educational call center training

---

## ✅ Pre-Flight Checklist

Before your first call simulation:

- [ ] Python 3.10+ installed
- [ ] Google Cloud project created
- [ ] Vertex AI API enabled
- [ ] Service account credentials downloaded
- [ ] `.env` file configured
- [ ] Database initialized (`python init_db.py`)
- [ ] Server running (`python app_simple.py`)
- [ ] Frontend accessible (http://localhost:5500)
- [ ] User account created

---

🎉 **Ready to train!** Open the frontend and start your first Lazada support call!
