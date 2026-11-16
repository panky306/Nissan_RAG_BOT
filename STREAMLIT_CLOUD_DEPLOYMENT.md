# Streamlit Cloud Deployment Guide
## Nissan Recommendation Engine

---

## ✅ What Was Updated

### 1. **requirements.txt** - Fixed Deployment Issue
```
streamlit==1.40.1     # Fast wheels, no source build
duckdb==1.0.0         # Stable, no source build
openai==1.57.0        # Compatible version
pandas==2.2.0         # No source build needed
pyarrow==16.0.0       # Lighter, faster
```

**Why?** Previous versions required source builds which timeout on Streamlit Cloud. New versions install in 2-5 minutes.

---

### 2. **src/utils.py** - Streamlit Secrets Support
Updated `load_environment()` to support:
- ✅ Streamlit Secrets (for Cloud)
- ✅ Environment variables (for Docker/Servers)
- ✅ .env files (for local development)

**Benefits:**
- Works on Streamlit Cloud without hardcoding API keys
- Still works locally with .env
- Secure API key management

---

### 3. **.streamlit/config.toml** - Configuration
Created configuration for:
- Theme customization
- Security settings (CORS, XSRF)
- Logger and server settings
- Maximum upload size: 200MB

---

### 4. **runtime.txt** - Python Version
Specifies Python 3.11.7 for consistent deployments on Streamlit Cloud.

---

### 5. **.gitignore** - Security
Updated to never commit:
- `.streamlit/secrets.toml` (your API keys)
- `.streamlit/cache/` (temporary files)

---

## 🚀 Deployment Steps

### Step 1: Local Setup & Testing

1. **Create local secrets file:**
   ```bash
   cd Nissan_Recom_Engine
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml` with your API key:**
   ```toml
   openai_api_key = "sk-your-actual-api-key-here"
   ```

3. **Test locally:**
   ```bash
   streamlit run app.py
   ```
   
   You should see:
   - ✅ No configuration errors
   - ✅ "Upload a data file in the sidebar to get started!"
   - ✅ Upload and query works with sample data

### Step 2: Prepare Repository

1. **Commit changes:**
   ```bash
   git add requirements.txt src/utils.py .streamlit/ runtime.txt .gitignore
   git commit -m "Configure for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Verify on GitHub:**
   - Go to your repo on GitHub
   - Confirm files are pushed
   - Check `.streamlit/secrets.toml` is NOT in the repo (should be ignored)

### Step 3: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud:** https://streamlit.io/cloud

2. **Create new app:**
   - Click "New app"
   - Select your GitHub repository
   - Branch: `main`
   - Main file path: `Nissan_Recom_Engine/app.py`
   - Click "Deploy"

3. **Wait for build:**
   - Should take 2-5 minutes
   - You'll see build logs
   - When complete, app URL will appear

### Step 4: Add Secrets to Streamlit Cloud

1. **After deployment starts**, click the **Settings** button (⚙️ icon)

2. **Go to "Secrets" tab**

3. **Add your OpenAI API key:**
   ```
   openai_api_key = "sk-your-actual-api-key-here"
   ```

4. **Save** - the app will refresh automatically

---

## ✅ Verification Checklist

After deployment:

- [ ] App loads without errors
- [ ] "Upload a data file" message appears
- [ ] Can upload a CSV/JSON/Parquet file
- [ ] Can ask questions about the data
- [ ] Responses appear correctly
- [ ] Query details are visible in expandable section

---

## 🔧 Troubleshooting

### Problem: "OpenAI API key not found"
**Solution:**
1. Go to Settings → Secrets
2. Verify `openai_api_key` is added (exact spelling)
3. Click Save - app will restart
4. Try again

### Problem: "Deployment still slow"
**Solution:**
1. Check you're using updated `requirements.txt`
2. Look for `.tar.gz` files in build logs (means source building)
3. If so, clear cache:
   - Delete app
   - Wait 5 minutes
   - Redeploy

### Problem: "Can't find module 'streamlit'"
**Solution:**
1. Ensure you're in `Nissan_Recom_Engine` directory
2. Main file path should be: `Nissan_Recom_Engine/app.py`
3. Check `requirements.txt` is in `Nissan_Recom_Engine/`

### Problem: "File upload fails"
**Solution:**
1. Check max upload size in `.streamlit/config.toml` (currently 200MB)
2. Try with smaller file first
3. Ensure file format is CSV, JSON, or Parquet

---

## 📚 Local Development

### Run locally:
```bash
cd Nissan_Recom_Engine
streamlit run app.py
```

### Environment Variables (optional):
Instead of `.streamlit/secrets.toml`, you can use:
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4-turbo"
streamlit run app.py
```

---

## 📋 File Structure

```
Nissan_Recom_Engine/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies (UPDATED)
├── runtime.txt                     # Python version (NEW)
├── STREAMLIT_CLOUD_DEPLOYMENT.md   # This file
│
├── .streamlit/
│   ├── config.toml                 # Configuration (NEW)
│   ├── secrets.toml                # LOCAL ONLY - API keys (never commit)
│   └── secrets.toml.example        # Template (NEW)
│
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── utils.py                    # UPDATED - Secrets support
│   ├── duckdb_handler.py
│   ├── llm_handler.py
│   ├── rag_pipeline.py
│   └── data_dictionary.py
```

---

## 🔐 Security Best Practices

✅ **DO:**
- Use Streamlit Secrets for API keys (Cloud)
- Use environment variables for Docker/Servers
- Use .env files for local development only
- Never commit `.streamlit/secrets.toml`
- Rotate API keys regularly

❌ **DON'T:**
- Hardcode API keys in code
- Commit `.env` or `secrets.toml`
- Share API keys via email/chat
- Use the same API key for multiple apps

---

## 📞 Support

If you encounter issues:

1. Check [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-cloud/deploy-your-app)
2. Check [OpenAI API Docs](https://platform.openai.com/docs)
3. Review build logs in Streamlit Cloud dashboard
4. Check `.streamlit/config.toml` for syntax errors

---

## ✨ Next Steps

1. ✅ Test locally with `streamlit run app.py`
2. ✅ Push to GitHub
3. ✅ Deploy via Streamlit Cloud
4. ✅ Add API key secret
5. ✅ Share app URL with users!

**Expected deployment time: 2-5 minutes** ⏱️

Good luck! 🚀
