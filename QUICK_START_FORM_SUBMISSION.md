# 🚀 Quick Start: Form Submission System

## ✅ What's Been Added

Your application now includes a complete form submission system that:

1. ✅ Allows agents to submit forms through a web interface
2. ✅ Routes submissions through IPRoyal proxy (masks agent IP)
3. ✅ Automatically saves data to Google Sheets
4. ✅ Generates TrustedForm certificate URLs
5. ✅ Submits forms to https://lowinsurancecost.com

## 🎯 Quick Setup (3 Steps)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Google Sheets

1. Create a Google Cloud service account (see `FORM_SUBMISSION_SETUP.md`)
2. Share your Google Sheet with the service account email
3. Set environment variables:
   ```bash
   GOOGLE_SHEETS_CREDENTIALS_JSON='{...your-json-credentials...}'
   GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id'
   ```

### Step 3: Find Landing Page Form Endpoint

1. Visit https://lowinsurancecost.com
2. Inspect the form to find the submission endpoint
3. Set environment variable:
   ```bash
   LANDING_PAGE_FORM_ENDPOINT='/submit'  # or whatever the actual endpoint is
   ```

## 🎬 How Agents Use It

1. Agent logs in (agent1, agent2, etc.)
2. Clicks **"Submit Form"** from dashboard
3. Fills out form with lead information
4. Clicks **"Submit Form"** button
5. System automatically:
   - Submits through proxy (IP masked)
   - Saves to Google Sheets
   - Shows success message

## 📋 Form Fields Included

- First Name \*
- Last Name \*
- Email \*
- Phone \*
- Zip Code \*
- Date of Birth \*
- Address
- City
- State
- Additional Information

**Note:** You may need to adjust field names in `app.py` if the landing page uses different names.

## 🔧 Important Configuration

### Environment Variables Needed:

```bash
# Google Sheets (Required for data saving)
GOOGLE_SHEETS_CREDENTIALS_JSON='{...}'
GOOGLE_SHEETS_SPREADSHEET_ID='...'
GOOGLE_SHEETS_WORKSHEET_NAME='Form Submissions'  # Optional

# Landing Page (Required for form submission)

2. **Field Names:** The landing page form may use different field names. Check the form HTML and update the `payload` dictionary in `submit_form_through_proxy()` function if needed.

3. **Google Sheets:** The system will create a worksheet named "Form Submissions" automatically if it doesn't exist.

4. **TrustedForm:** Currently generates certificate URLs. For full TrustedForm compliance, you may need additional integration.

## 🐛 Testing

1. **Test the form page:**
   - Login as agent1
   - Go to "Submit Form"
   - Fill out and submit

2. **Check Google Sheets:**
   - Verify data appears in your spreadsheet
   - Check that TrustedForm URL is included

3. **Verify proxy IP:**
   - Check the success message shows a proxy IP
   - The landing page should see the proxy IP, not agent's real IP

## 📚 Full Documentation

See `FORM_SUBMISSION_SETUP.md` for detailed setup instructions.

## 🆘 Troubleshooting

**"Form submission failed"**
- Check `LANDING_PAGE_FORM_ENDPOINT` is correct
- Verify proxy is working
- Check form field names match landing page

**"Data not saving to Google Sheets"**
- Verify `GOOGLE_SHEETS_CREDENTIALS_JSON` is set correctly
- Check service account has access to spreadsheet
- Verify spreadsheet ID is correct

**"IP not masking"**
- Test proxy connection from dashboard
- Verify proxy credentials are correct

---

**You're ready to go!** Configure the environment variables and start submitting forms through your proxy.

```
