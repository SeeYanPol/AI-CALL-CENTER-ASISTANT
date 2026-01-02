# Google Vertex AI Setup Guide
**For Lazada CallSim Project**

This guide will help you set up Google Cloud Vertex AI for the CallSim project.

---

## Prerequisites

- Google Cloud account
- Credit card (for billing, though free tier is generous)
- Python 3.10+

---

## Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com
   - Sign in with your Google account

2. **Create a new project**
   - Click "Select a project" → "New Project"
   - Project name: `lazada-callsim` (or your choice)
   - Click "Create"
   - Wait for project creation (30 seconds)

3. **Note your Project ID**
   - You'll see it in the format: `lazada-callsim-123456`
   - Copy this ID - you'll need it later!

---

## Step 2: Enable Vertex AI API

1. **Open API Library**
   - In Google Cloud Console, search for "Vertex AI API"
   - Or visit: https://console.cloud.google.com/apis/library

2. **Enable the API**
   - Click "Vertex AI API"
   - Click "Enable"
   - Wait for activation (1-2 minutes)

---

## Step 3: Create Service Account

1. **Go to IAM & Admin**
   - Navigation menu → IAM & Admin → Service Accounts
   - Or visit: https://console.cloud.google.com/iam-admin/serviceaccounts

2. **Create Service Account**
   - Click "Create Service Account"
   - Service account name: `callsim-ai`
   - Service account ID: `callsim-ai@your-project.iam.gserviceaccount.com`
   - Click "Create and Continue"

3. **Grant Permissions**
   - Role: Select "Vertex AI User"
   - Click "Continue"
   - Click "Done"

---

## Step 4: Generate Credentials JSON

1. **Find your service account**
   - In the service accounts list, find `callsim-ai`

2. **Create a key**
   - Click the three dots (⋮) → "Manage keys"
   - Click "Add Key" → "Create new key"
   - Select "JSON"
   - Click "Create"

3. **Download the file**
   - A JSON file will download automatically
   - Name it: `vertex-ai-credentials.json`
   - Move it to your project: `d:\PAUL\backend\`

⚠️ **IMPORTANT**: This file contains secrets! Never commit it to Git.

---

## Step 5: Configure Environment

1. **Edit your `.env` file**
   ```bash
   cd d:\PAUL\backend
   notepad .env
   ```

2. **Add these lines**
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id-here
   GOOGLE_APPLICATION_CREDENTIALS=backend/vertex-ai-credentials.json
   ```

3. **Replace values**
   - `your-project-id-here` → Your actual project ID from Step 1
   - Verify the path to your JSON file

---

## Step 6: Test the Setup

1. **Run the test script**
   ```bash
   cd d:\PAUL\backend
   python -c "from vertexai.preview.generative_models import GenerativeModel; import vertexai; vertexai.init(project='YOUR_PROJECT_ID', location='us-central1'); model = GenerativeModel('gemini-1.5-flash'); print('✅ Vertex AI configured successfully!')"
   ```

2. **Expected output**
   ```
   ✅ Vertex AI configured successfully!
   ```

3. **If you see errors**
   - Check your project ID is correct
   - Verify the JSON file path
   - Ensure Vertex AI API is enabled

---

## Step 7: Start the Application

```bash
cd d:\PAUL\backend
python app_simple.py
```

You should see:
```
============================================================
CallSim - Lazada Customer Support Simulator
============================================================
Frontend: http://localhost:5500
API Docs: http://localhost:5000/apidocs
API: http://localhost:5000/api/v1/
Vertex AI: Configured
============================================================
```

---

## 💰 Pricing & Free Tier

**Good news for students!**

- Gemini 1.5 Flash: **FREE up to 1500 requests/day**
- After that: $0.35 per 1 million characters
- For this project: ~500-1000 requests = **$0** cost

**Free tier includes:**
- 15 requests per minute
- 1,500 requests per day
- Perfect for school projects!

---

## 🔒 Security Best Practices

1. **Never commit credentials**
   ```bash
   # Add to .gitignore
   echo "vertex-ai-credentials.json" >> .gitignore
   ```

2. **Restrict service account**
   - Only give "Vertex AI User" role
   - Don't use "Owner" or "Editor"

3. **Use environment variables**
   - Always use `.env` file
   - Never hardcode credentials in code

---

## 🆘 Troubleshooting

### Error: "Permission Denied"
**Solution**: Grant "Vertex AI User" role to service account

### Error: "API not enabled"
**Solution**: Enable Vertex AI API in Cloud Console

### Error: "Application Default Credentials not found"
**Solution**: Set `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

### Error: "Quota exceeded"
**Solution**: Wait for daily quota reset (free tier limit)

---

## 📚 Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Guide](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Pricing Calculator](https://cloud.google.com/products/calculator)

---

## ✅ Checklist

Before running the project, verify:

- [ ] Google Cloud project created
- [ ] Project ID copied
- [ ] Vertex AI API enabled
- [ ] Service account created with "Vertex AI User" role
- [ ] JSON credentials downloaded
- [ ] `.env` file configured with project ID and credentials path
- [ ] Test command runs successfully
- [ ] `app_simple.py` shows "Vertex AI: Configured"

---

🎉 **You're all set!** Start practicing Lazada customer support scenarios!
