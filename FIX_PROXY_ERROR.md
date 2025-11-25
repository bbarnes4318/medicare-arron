# 🔧 Fixing Proxy Error: 402 Payment Required

## What This Error Means:

**"402 Payment Required"** means your IPRoyal proxy account has an issue. This could be:
1. ❌ Account needs payment/credits
2. ❌ Proxy credentials expired
3. ❌ Account suspended or inactive

## How to Fix It:

### Step 1: Check Your IPRoyal Account

1. **Log into your IPRoyal dashboard:**
   - Go to https://iproyal.com
   - Log in with your account

2. **Check your account status:**
   - Look for account balance/credits
   - Check if account is active
   - Verify subscription status

3. **Check proxy credentials:**
   - Go to your proxy settings
   - Verify the username and password are correct
   - Check if credentials have expired

### Step 2: Update Proxy Credentials

If your credentials changed or you need to update them, edit `app.py`:

```python
PROXY_CONFIG = {
    'host': os.environ.get('PROXY_HOST', 'geo.iproyal.com'),
    'port': int(os.environ.get('PROXY_PORT', '12321')),
    'username': os.environ.get('PROXY_USERNAME', 'YOUR_NEW_USERNAME'),
    'password': os.environ.get('PROXY_PASSWORD', 'YOUR_NEW_PASSWORD'),
    ...
}
```

Or set environment variables:
```bash
PROXY_USERNAME='your-username'
PROXY_PASSWORD='your-password'
```

### Step 3: Test the Proxy

You can test if the proxy works by running:

```python
python test_proxy.py
```

Or test from the dashboard by clicking "Test Connection"

### Step 4: Common Issues

**Issue:** Account has no credits
- **Fix:** Add credits to your IPRoyal account

**Issue:** Credentials expired
- **Fix:** Generate new credentials from IPRoyal dashboard

**Issue:** Wrong proxy type
- **Fix:** Make sure you're using the correct proxy type (residential, datacenter, etc.)

**Issue:** IP blocked
- **Fix:** Contact IPRoyal support or try a different proxy location

## Quick Test:

1. Try accessing the proxy directly:
   ```bash
   curl -x http://username:password@geo.iproyal.com:12321 https://ipv4.icanhazip.com
   ```

2. If that fails, the proxy credentials are definitely the issue.

## Still Not Working?

1. **Contact IPRoyal Support** - They can check your account status
2. **Verify credentials** - Double-check username/password are correct
3. **Check account balance** - Make sure you have credits
4. **Try a different proxy** - If you have multiple proxies, try another one

---

**Once you fix the proxy issue, the form submission should work!** ✅

