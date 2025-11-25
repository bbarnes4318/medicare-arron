# 📋 Form Submission Setup Guide

This guide will help you configure the form submission system that allows your agents to submit forms to the landing page through your IPRoyal proxy, with automatic Google Sheets logging and TrustedForm certificate generation.

## 🎯 What This Does

1. **Agent submits form** → Your portal form page
2. **Form data is sent** → Through IPRoyal proxy (IP masked)
3. **Submitted to landing page** → https://lowinsurancecost.com
4. **Data saved** → Google Sheets with TrustedForm certificate URL
5. **IP masked** → Landing page sees proxy IP, not agent's real IP

## ⚙️ Configuration Steps

### Step 1: Set Up Google Sheets API

1. **Create a Google Cloud Project:**
   - Go to https://console.cloud.google.com
   - Create a new project or select an existing one

2. **Enable Google Sheets API:**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and enable it
   - Search for "Google Drive API" and enable it

3. **Create Service Account:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name it (e.g., "form-submission-service")
   - Click "Create and Continue"
   - Skip optional steps and click "Done"

4. **Create Service Account Key:**
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose "JSON" format
   - Download the JSON file

5. **Share Google Sheet with Service Account:**
   - Create a new Google Spreadsheet or use an existing one
   - Click "Share" button
   - Add the service account email (found in the JSON file, looks like `xxx@xxx.iam.gserviceaccount.com`)
   - Give it "Editor" permissions
   - Copy the Spreadsheet ID from the URL:
     - URL format: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
     - The `SPREADSHEET_ID` is the long string between `/d/` and `/edit`

### Step 2: Configure Environment Variables

Set these environment variables in your deployment platform (DigitalOcean, Heroku, etc.):

```bash
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id-here'
GOOGLE_SHEETS_WORKSHEET_NAME='Form Submissions'  # Optional, defaults to "Form Submissions"

# Landing Page Configuration
LANDING_PAGE_URL='https://lowinsurancecost.com'
LANDING_PAGE_FORM_ENDPOINT='/submit'  # Change this to the actual form endpoint
```

**Important Notes:**
- `GOOGLE_SHEETS_CREDENTIALS_JSON` should be the entire contents of the downloaded JSON file as a single-line string
- You may need to escape quotes if setting via command line
- For DigitalOcean, set these in the App Platform environment variables section

### Step 3: Find the Landing Page Form Endpoint

You need to determine the exact endpoint where the landing page form submits to:

1. **Inspect the landing page form:**
   - Go to https://lowinsurancecost.com
   - Right-click on the form and select "Inspect"
   - Look for the `<form>` tag and find the `action` attribute
   - Common endpoints: `/submit`, `/form-handler`, `/contact`, `/lead`, etc.

2. **Check browser network tab:**
   - Open browser DevTools (F12)
   - Go to "Network" tab
   - Submit the form on the landing page
   - Look for the POST request and note the endpoint URL

3. **Set the endpoint:**
   - Update `LANDING_PAGE_FORM_ENDPOINT` environment variable with the correct path
   - If the form submits to the same page (no action), leave it empty or set to `/`

### Step 4: Map Form Fields (If Needed)

The current form includes these fields:
- `first_name`
- `last_name`
- `email`
- `phone`
- `zip_code`
- `date_of_birth`
- `address`
- `city`
- `state`
- `additional_info`

**If the landing page form uses different field names**, you'll need to update the `submit_form_through_proxy()` function in `app.py` to map your fields to their field names.

Example mapping:
```python
payload = {
    'fname': form_data.get('first_name', ''),  # Their field name: your field name
    'lname': form_data.get('last_name', ''),
    # ... etc
}
```

## 🚀 Using the System

1. **Agent logs in** to the portal (agent1, agent2, etc.)
2. **Clicks "Submit Form"** from the dashboard
3. **Fills out the form** with lead information
4. **Submits the form**
5. **System automatically:**
   - Generates TrustedForm certificate
   - Submits form through proxy (IP masked)
   - Saves data to Google Sheets
   - Shows success/error message

## 📊 Google Sheets Output

Each submission creates a row with:
- Timestamp
- Agent username
- All form fields
- TrustedForm Certificate URL
- Proxy IP used
- Submission status
- Landing page response

## 🔧 Troubleshooting

### Form submission fails
- Check that `LANDING_PAGE_FORM_ENDPOINT` is correct
- Verify proxy credentials are working
- Check that form field names match the landing page expectations
- Review server logs for error messages

### Google Sheets not saving
- Verify `GOOGLE_SHEETS_CREDENTIALS_JSON` is set correctly (entire JSON as string)
- Check that `GOOGLE_SHEETS_SPREADSHEET_ID` is correct
- Ensure service account has "Editor" access to the spreadsheet
- Verify Google Sheets API and Drive API are enabled

### TrustedForm certificate not generating
- The system generates a certificate URL automatically
- If you need real TrustedForm integration, you may need to implement their JavaScript SDK on the form page
- Current implementation generates a certificate URL format that can be customized

### IP not masking
- Verify proxy credentials in `PROXY_CONFIG`
- Test proxy connection using the "Test Connection" feature
- Check that proxy is active and working

## 📝 Notes

- **Form field mapping:** You may need to adjust field names in `app.py` to match the landing page form exactly
- **TrustedForm:** The current implementation generates a certificate URL. For full TrustedForm compliance, you may need to integrate their JavaScript SDK
- **Rate limiting:** Be aware of rate limits on both the proxy service and the landing page
- **Error handling:** Failed submissions are still saved to Google Sheets for record-keeping

## 🔐 Security

- Keep your Google service account JSON credentials secure
- Never commit credentials to version control
- Use environment variables for all sensitive configuration
- Regularly rotate service account keys if needed

## 📞 Support

If you encounter issues:
1. Check server logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test proxy connection independently
4. Verify Google Sheets API access

---

**Ready to use!** Once configured, your agents can start submitting forms through the proxy with automatic Google Sheets logging.

