# 🔧 Fix "No key could be detected" Error

## ❌ The Problem:

The error `Error saving to Google Sheets: No key could be detected` means the Google Sheets credentials JSON is not set correctly in DigitalOcean.

## ✅ The Fix:

### Step 1: Get Your JSON Credentials

You need your Google Cloud service account JSON file. Get it from:
1. Google Cloud Console → APIs & Services → Credentials
2. Click on your service account
3. Go to "Keys" tab → "Add Key" → "Create new key" → JSON
4. Download the JSON file

### Step 2: Convert to Single Line

**IMPORTANT:** DigitalOcean requires the JSON on **ONE LINE** with **escaped newlines**.

**Option A: Use Your .env File**
- Open your local `.env` file
- Copy the entire `GOOGLE_SHEETS_CREDENTIALS_JSON` value (it's already formatted correctly)

**Option B: Convert Manually**
1. Take your JSON file
2. Remove all line breaks (make it one continuous line)
3. In the `private_key` field, change `\n` to `\\n` (double backslash)

### Step 3: Set in DigitalOcean Dashboard

1. **Go to:** https://cloud.digitalocean.com/apps
2. **Click** on your app: `medicare-form-portal`
3. **Click:** "Settings" tab
4. **Click:** "App-Level Environment Variables"
5. **Find:** `GOOGLE_SHEETS_CREDENTIALS_JSON`
6. **Click:** "Edit" (or "Add Variable" if it doesn't exist)
7. **Value:** Paste your ENTIRE JSON (single line, with `\\n` for newlines)
8. **Scope:** Run Time
9. **Click:** "Save"

### Step 4: Redeploy

After saving, DigitalOcean will automatically redeploy. Or:
1. Go to "Runtime Logs" tab
2. Click "Redeploy" if needed

## ✅ Quick Copy-Paste Format:

**Use your `.env` file!** It's already formatted correctly. Just copy the value from:

```env
GOOGLE_SHEETS_CREDENTIALS_JSON={...your json here...}
```

Or format it manually:
```
{"type":"service_account","project_id":"YOUR_PROJECT_ID","private_key_id":"YOUR_KEY_ID","private_key":"-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n","client_email":"YOUR_SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com","client_id":"YOUR_CLIENT_ID",...}
```

**Key Points:**
- ✅ All on ONE line
- ✅ `\\n` (double backslash) for newlines in private_key
- ✅ No extra spaces
- ✅ Valid JSON format

## 🧪 Test After Fixing:

1. Submit a test form
2. Check DigitalOcean logs - should see "Successfully saved form submission to Google Sheets"
3. Check your Google Sheet - should see new row

---

**Once you set the JSON correctly in DigitalOcean, the error will be fixed!** ✅

