# 📋 User Guide: Submitting Medicare Leads

This guide explains how to submit leads using the Medicare Portal. The system automatically handles IP masking and TrustedForm certificate generation for you.

## ✅ How to Submit a Lead

1.  **Login** to the Portal.
2.  Click **"Submit Form"** in the navigation menu.
3.  **Fill out the form** with the lead's information (Name, Phone, Zip, etc.).
4.  Click the **"Submit Form"** button.
5.  **WAIT.** You will see a loading message: _"Generating TrustedForm Certificate..."_
    - _Do not close the tab._
    - _Do not click back._
    - The server is launching a secure browser in the background to visit `lowinsurancecost.com` and capture the certificate. This takes about 10-15 seconds.
6.  You will see a **"Success!"** message once the lead is submitted.

## 🔍 How to Verify

1.  Go to **"Dashboard"** or **"View Leads"**.
2.  Find the lead you just submitted.
3.  Look at the **TrustedForm URL** column.
4.  Click the link to view the certificate.
    - **URL:** It will show `https://lowinsurancecost.com/`.
    - **IP:** It will show the **Proxy IP Address** (not your office IP).

## ❓ FAQ

**Q: Do I need to run any scripts?**
A: **NO.** The server handles everything. You just use the web form.

**Q: Why does it take a few seconds to submit?**
A: The system is performing a real-time browser session in the background to ensure the TrustedForm certificate is 100% valid and compliant.

**Q: What if I get an error?**
A: If you see an error, try submitting again. If the problem persists, contact support.
