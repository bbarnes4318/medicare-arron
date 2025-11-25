# Landing Page Form Field Mapping

## ✅ Form Fields Updated

Based on the landing page HTML analysis, the form has been updated to match the exact field structure:

### Form Fields (Matching Landing Page):

1. **State** (`state`) - Required
2. **Zip Code** (`zip_code`) - Required  
3. **First Name** (`first_name`) - Required
4. **Last Name** (`last_name`) - Required
5. **Phone** (`phone`) - Required
6. **Email** (`email`) - Optional
7. **Disclosure** (`disclosure`) - Required checkbox (TCPA consent)

### Hidden Fields (Automatically Added):

- **universal_leadid** - LeadID token (UUID format, auto-generated)
- **xxTrustedFormCertUrl** - TrustedForm certificate URL
- **xxTrustedFormToken** - TrustedForm token (same as cert URL)
- **xxTrustedFormPingUrl** - TrustedForm ping URL

## 🔧 Changes Made

### 1. Form Template (`templates/submit_form.html`)
- ✅ Removed: date_of_birth, address, city, additional_info fields
- ✅ Updated field order to match landing page: State, Zip Code, First Name, Last Name, Phone, Email
- ✅ Added TCPA disclosure checkbox with full consent text
- ✅ Made email optional (matching landing page)

### 2. Backend Submission (`app.py`)
- ✅ Updated payload to match exact field names
- ✅ Added LeadID token generation (`universal_leadid`)
- ✅ Added TrustedForm fields in correct format:
  - `xxTrustedFormCertUrl`
  - `xxTrustedFormToken` 
  - `xxTrustedFormPingUrl`
- ✅ Updated headers for Angular app (JSON submission with fallback)
- ✅ Updated Google Sheets columns to match new structure

### 3. Google Sheets Structure
Updated columns:
- Timestamp
- Agent
- State
- Zip Code
- First Name
- Last Name
- Phone
- Email
- Disclosure (TCPA Consent)
- LeadID Token
- TrustedForm Certificate URL
- TrustedForm Token
- TrustedForm Ping URL
- Proxy IP
- Submission Status
- Landing Page Response

## ⚠️ Important Notes

### Form Submission Endpoint
The landing page is an **Angular application** without an explicit form `action` attribute. This means:

1. **The form is submitted via JavaScript/AJAX** to an API endpoint
2. **You need to find the actual API endpoint** by:
   - Opening browser DevTools (F12)
   - Going to Network tab
   - Submitting the form on the actual landing page
   - Finding the POST request and noting the endpoint URL

3. **Set the endpoint** in environment variable:
   ```bash
   LANDING_PAGE_FORM_ENDPOINT='/api/submit'  # or whatever the actual endpoint is
   ```

### Submission Format
The code now tries:
1. **JSON submission first** (Angular apps typically use JSON)
2. **Form-urlencoded fallback** if JSON fails

### TrustedForm Integration
- TrustedForm certificate URLs are automatically generated
- The format matches the landing page: `https://cert.trustedform.com/{cert_id}`
- All three TrustedForm fields are included in submissions

## 🧪 Testing

To test the form:
1. Login to the portal
2. Go to "Submit Form"
3. Fill out all required fields
4. Check the TCPA disclosure checkbox
5. Submit

The system will:
- ✅ Generate TrustedForm certificate
- ✅ Generate LeadID token
- ✅ Submit through proxy (IP masked)
- ✅ Save to Google Sheets (if configured)

## 📝 Next Steps

1. **Find the API endpoint:**
   - Visit https://lowinsurancecost.com
   - Submit the form while watching Network tab
   - Note the POST endpoint URL
   - Set `LANDING_PAGE_FORM_ENDPOINT` environment variable

2. **Configure Google Sheets** (if not already done)

3. **Test a submission** and verify:
   - Form data reaches the landing page
   - IP is masked (check landing page logs)
   - Data appears in Google Sheets

---

**Form is now configured to match the landing page structure exactly!** 🎉

