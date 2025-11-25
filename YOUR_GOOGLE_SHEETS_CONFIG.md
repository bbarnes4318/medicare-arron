# 📊 Your Google Sheets Configuration

## ✅ Your Setup:

- **Spreadsheet Name:** `medicare-form`
- **Worksheet Name:** `medicare-form`
- **Spreadsheet ID:** (You need to get this from the URL)

## 🔍 How to Get Your Spreadsheet ID:

1. **Open your Google Spreadsheet:** https://sheets.google.com
2. **Open the spreadsheet** named "medicare-form"
3. **Look at the URL** in your browser
4. **It looks like:**
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
   ```
5. **Copy the long string** between `/d/` and `/edit`
   - **Example:** If URL is `https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit`
   - **Your Spreadsheet ID is:** `1a2b3c4d5e6f7g8h9i0j`

## ⚙️ What You Need to Set:

You need to set these **2 environment variables**:

### 1. GOOGLE_SHEETS_CREDENTIALS_JSON
- This is the entire JSON file content from your service account
- See Step 8 in `GOOGLE_SHEETS_SETUP_EXACT_STEPS.md` for how to get this

### 2. GOOGLE_SHEETS_SPREADSHEET_ID
- This is the Spreadsheet ID you copied above
- **Example:** `1a2b3c4d5e6f7g8h9i0j`

### 3. GOOGLE_SHEETS_WORKSHEET_NAME (Optional)
- **Default is now:** `medicare-form` ✅
- You don't need to set this unless you want a different name

## 🚀 Quick Setup (Windows PowerShell):

```powershell
# Set the credentials JSON (replace with your actual JSON)
$env:GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project-id",...}'

# Set your spreadsheet ID (replace with your actual ID)
$env:GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id-here'

# Worksheet name is already set to "medicare-form" by default, so you can skip this
# But if you want to set it explicitly:
$env:GOOGLE_SHEETS_WORKSHEET_NAME='medicare-form'
```

## ✅ Verification:

Once you've set the environment variables:

1. **Start your app:**
   ```bash
   python app.py
   ```

2. **Login** and submit a test form

3. **Check your Google Sheet** "medicare-form"
   - Open the worksheet tab "medicare-form"
   - You should see a new row with all the form data!

## 📝 Notes:

- ✅ Worksheet name is already set to `medicare-form` by default
- ✅ The code will automatically create the worksheet if it doesn't exist
- ✅ Make sure you've shared the spreadsheet with your service account email
- ✅ Make sure the service account has "Editor" permission

---

**Your configuration is ready!** Just set the 2 environment variables (credentials JSON and spreadsheet ID) and you're good to go! 🎉

