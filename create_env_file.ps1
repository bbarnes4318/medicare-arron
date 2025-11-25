# Create .env file with correct format
$envContent = @"
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account","project_id":"YOUR_PROJECT_ID","private_key_id":"YOUR_PRIVATE_KEY_ID","private_key":"-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_HERE\\n-----END PRIVATE KEY-----\\n","client_email":"YOUR_SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com","client_id":"YOUR_CLIENT_ID","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/..."}

GOOGLE_SHEETS_SPREADSHEET_ID=1l48px8Sj9JiqbfW8aLgMeWMMGAVYQFjbKnZWZkVmDCE

GOOGLE_SHEETS_WORKSHEET_NAME=medicare-form

# Landing Page Configuration
LANDING_PAGE_URL=https://lowinsurancecost.com
LANDING_PAGE_FORM_ENDPOINT=

# Proxy Configuration (for local testing)
PROXY_HOST=geo.iproyal.com
PROXY_PORT=12321
PROXY_USERNAME=your_iproyal_username
PROXY_PASSWORD=your_iproyal_password
"@

$envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline
Write-Host ".env file created successfully!" -ForegroundColor Green
