# 🚀 Deploy to DigitalOcean App Platform

## ✅ Pre-Deployment Checklist:

- [x] Code is ready
- [x] .env file created (for local use)
- [x] .gitignore excludes .env (security)
- [x] DigitalOcean config updated

## 📋 Step 1: Push to GitHub

### Option A: Use Git Commands

```bash
# Initialize git if not already done
git init

# Add remote repository
git remote add origin https://github.com/bbarnes4318/medicare-form.git

# Add all files
git add .

# Commit
git commit -m "Initial commit - Medicare form submission portal"

# Push to GitHub
git push -u origin main
```

### Option B: Use Provided Script (Windows)

```bash
# Run the push script
.\PUSH_TO_GITHUB.bat
```

## 📋 Step 2: Deploy to DigitalOcean

1. **Go to:** https://cloud.digitalocean.com/apps

2. **Click:** "Create App"

3. **Connect GitHub:**
   - Select "GitHub" as source
   - Authorize DigitalOcean if needed
   - Select repository: `bbarnes4318/medicare-form`
   - Branch: `main`

4. **Configure App:**
   - DigitalOcean will detect `.do/app.yaml`
   - Review the configuration
   - Click "Next"

5. **Set Environment Variables:**
   - **IMPORTANT:** Set `GOOGLE_SHEETS_CREDENTIALS_JSON` manually in DigitalOcean dashboard
   - Go to your app → Settings → App-Level Environment Variables
   - Add:
     ```
     GOOGLE_SHEETS_CREDENTIALS_JSON = {"type":"service_account",...your full JSON...}
     ```
   - Make sure it's the ENTIRE JSON on ONE LINE

6. **Deploy:**
   - Click "Create Resources"
   - Wait 3-5 minutes for deployment

## ⚠️ CRITICAL: Set Google Sheets Credentials in DigitalOcean

**You MUST set `GOOGLE_SHEETS_CREDENTIALS_JSON` in DigitalOcean dashboard:**

1. Go to your app in DigitalOcean
2. Click "Settings" → "App-Level Environment Variables"
3. Click "Edit" or "Add Variable"
4. Add:
   - **Key:** `GOOGLE_SHEETS_CREDENTIALS_JSON`
   - **Value:** Your entire JSON (single line, escaped)
   - **Scope:** Run Time
5. Click "Save"

**The JSON must be on ONE LINE with escaped newlines (`\\n`)**

## ✅ After Deployment:

1. **Get your app URL:** `https://your-app-name.ondigitalocean.app`

2. **Test the app:**
   - Visit the URL
   - Login with `agent1` / `password123`
   - Test form submission

3. **Verify Google Sheets:**
   - Check your "medicare-form" spreadsheet
   - Should see form submissions appearing

## 🔧 Environment Variables in DigitalOcean:

These are already set in `.do/app.yaml`:
- ✅ `GOOGLE_SHEETS_SPREADSHEET_ID`
- ✅ `GOOGLE_SHEETS_WORKSHEET_NAME`
- ✅ `LANDING_PAGE_URL`
- ✅ `PROXY_HOST`, `PROXY_PORT`, `PROXY_USERNAME`, `PROXY_PASSWORD`

**You need to set manually:**
- ⚠️ `GOOGLE_SHEETS_CREDENTIALS_JSON` (set in dashboard)

## 🎯 Quick Push Script:

I've updated `PUSH_TO_GITHUB.bat` - just run it to push to GitHub!

---

**Ready to deploy!** Push to GitHub, then deploy on DigitalOcean! 🚀

