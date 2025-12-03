# Login Tracking Setup Guide

This guide explains how to set up Google Sheets login tracking for your Streamlit app.

## What Gets Tracked

Every successful login will record:
- **Timestamp**: Date and time of login
- **Username**: Which account logged in
- **User Agent**: Browser/session information

## Setup Steps

### 1. Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it "Portfolio Login Tracking" (or any name you prefer)
4. In the first row, add these column headers:
   - Column A: `Timestamp`
   - Column B: `Username`
   - Column C: `User Agent`
5. Copy the URL of this spreadsheet (you'll need it later)

### 2. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Name it something like "Portfolio Tracker"

### 3. Enable Google Sheets API

1. In your Google Cloud project, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it and press "Enable"
4. Also enable "Google Drive API" (search and enable it)

### 4. Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Give it a name like "portfolio-login-tracker"
4. Click "Create and Continue"
5. Skip the optional steps (click "Continue" then "Done")

### 5. Create Service Account Key

1. In the Service Accounts list, click on the email of the account you just created
2. Go to the "Keys" tab
3. Click "Add Key" → "Create New Key"
4. Choose "JSON" format
5. Click "Create" - this will download a JSON file
6. **Keep this file safe!** It contains credentials

### 6. Share Google Sheet with Service Account

1. Open the JSON file you downloaded
2. Find the `client_email` field (looks like: `portfolio-login-tracker@xxx.iam.gserviceaccount.com`)
3. Copy this email address
4. Go back to your Google Sheet
5. Click "Share" (top right)
6. Paste the service account email
7. Give it "Editor" permissions
8. Uncheck "Notify people"
9. Click "Share"

### 7. Configure Streamlit Secrets

On **Streamlit Cloud**:

1. Go to your app's dashboard on Streamlit Cloud
2. Click on "Settings" (⚙️)
3. Click on "Secrets"
4. Add the following secrets:

```toml
# Contents of the JSON file you downloaded
[gsheet_credentials]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC... (your full private key)
...
-----END PRIVATE KEY-----
"""
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project.iam.gserviceaccount.com"

# URL of your Google Sheet
login_sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**IMPORTANT for the `private_key` field:**
- Use **triple quotes** (`"""`) to wrap the private key
- Copy the ENTIRE private key from your JSON file, including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines
- Keep the line breaks as they are in the original JSON file
- Don't replace `\n` with actual newlines - copy it exactly as it appears in the JSON

**Example of correct format:**
```toml
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7xQxVwzEKwaQT
(many more lines of the key)
xQxVwzEKwaQTMIIEvQIBADANBgkqhkiG9w0BAQE
-----END PRIVATE KEY-----
"""
```

**For local development**, create a file called `.streamlit/secrets.toml` in your project directory with the same content.

### 8. Important Notes

- The `private_key` in the secrets should have newlines as `\n`
- Make sure the Google Sheet URL is correct
- Don't commit the `secrets.toml` file to git (it's already in `.gitignore`)
- The app will work fine even if tracking is not configured - it just won't log logins

## Verification

After deploying, you can verify it's working by:
1. Logging into your portfolio app
2. Checking your Google Sheet - you should see a new row with your login info

## Viewing Login Stats

Currently, login data is only stored in the Google Sheet. You can:
- View the sheet directly in Google Sheets
- Export to Excel for analysis
- Use Google Sheets' built-in charts and pivot tables

## Privacy & Security

- Login tracking data includes only: timestamp, username, and basic session info
- No passwords are ever logged
- The data is stored in your private Google Sheet
- Only you (and the service account) have access to the sheet
- The service account credentials should be kept secure in Streamlit Secrets

## Troubleshooting

**"Login tracking not configured" in logs:**
- This is normal if you haven't set up the secrets yet
- The app will still work normally

**Logins not appearing in sheet:**
- Verify the service account email has Editor access to the sheet
- Check that the `login_sheet_url` in secrets is correct
- Verify all credentials in the secrets file match your JSON file
- Check Streamlit Cloud logs for error messages
