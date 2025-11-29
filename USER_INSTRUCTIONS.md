# 🛡️ REQUIRED: How to Generate Valid TrustedForm Certificates

**STOP! READ THIS FIRST.**

If you need a TrustedForm certificate that shows:

1.  **URL:** `https://lowinsurancecost.com`
2.  **IP Address:** A masked Residential Proxy IP (not your real IP)

You **MUST** use the **Proxy Browser Launcher**.

---

## ❌ WRONG WAY: Using the Portal Form

Do **NOT** use the "Submit Form" page on the portal (`http://localhost:5000/submit-form`).

- **Why?** It runs in your regular browser. TrustedForm sees **YOUR IP** and the **PORTAL URL**.
- **Result:** Invalid certificate for your purpose.

---

## ✅ RIGHT WAY: Using the Proxy Browser Launcher

The "Proxy Browser Launcher" is a special script that opens a clean Chrome window, routes all traffic through the IPRoyal proxy, and loads the target website.

### Step 1: Prepare

1.  Ensure you have **Google Chrome** installed.
2.  Ensure your `.env` file has the correct `IPROYAL_USER` and `IPROYAL_PASS`.
3.  Ensure the application is running (`python app.py`).

### Step 2: Launch the Browser

1.  Open a terminal.
2.  Run the launcher script:
    ```bash
    python launch_browser.py
    ```
3.  A new Chrome window will open.
    - **Address Bar:** Will show `https://lowinsurancecost.com`
    - **Network:** All traffic is going through the proxy.

### Step 3: Submit the Form

1.  Fill out the form on the landing page in this specific Chrome window.
2.  Click "See My Options".
3.  **Wait** for the success message.

### Step 4: Verify

1.  Go to your Portal Dashboard (`http://localhost:5000/dashboard`).
2.  Click "View Leads".
3.  Find your submission.
4.  Click the **TrustedForm Certificate URL**.
5.  **Verify:**
    - **URL:** Should be `https://lowinsurancecost.com`
    - **IP:** Should be the Proxy IP (e.g., `38.13.182.181`)

---

## ⚠️ Troubleshooting

- **Browser doesn't open?** Make sure Chrome is installed.
- **Proxy Error / No Internet?** Check your `.env` credentials. The proxy might be expired or invalid.
- **Data not saving?** Ensure `app.py` is running in the background to receive the data.
