# Deployment Guide for DigitalOcean App Platform

## Prerequisites

1. A GitHub account with the repository: `https://github.com/bbarnes4318/medicare-arron.git`
2. A DigitalOcean account
3. Git installed on your local machine

---

## Step 1: Push Code to GitHub

From your local project directory, run these commands:

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit the changes
git commit -m "Initial commit - Proxy Access Portal"

# Add your GitHub repository as remote
git remote add origin https://github.com/bbarnes4318/medicare-arron.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to DigitalOcean App Platform

### Option A: Using the Web Interface (Recommended)

1. **Go to DigitalOcean App Platform:**

   - Visit: https://cloud.digitalocean.com/apps
   - Click "Create App"

2. **Connect Your GitHub Repository:**

   - Select "GitHub" as the source
   - Authorize DigitalOcean to access your GitHub account
   - Select repository: `bbarnes4318/medicare-arron`
   - Select branch: `main`
   - Check "Autodeploy" to automatically deploy on push

3. **Configure Your App:**

   - DigitalOcean will auto-detect the `.do/app.yaml` configuration
   - Review the settings:
     - **Name:** proxy-access-portal
     - **Region:** Choose closest to your users
     - **Plan:** Basic ($5/month recommended)

4. **Environment Variables (Optional):**

   - You can add custom environment variables if needed
   - The app will work with the defaults

5. **Review and Launch:**

   - Review the configuration
   - Click "Create Resources"
   - Wait 3-5 minutes for deployment

6. **Access Your App:**
   - Once deployed, you'll get a URL like: `https://proxy-access-portal-xxxxx.ondigitalocean.app`
   - Share this URL with your team!

### Option B: Using the DigitalOcean CLI (doctl)

```bash
# Install doctl (if not installed)
# Windows: choco install doctl
# Mac: brew install doctl
# Linux: snap install doctl

# Authenticate
doctl auth init

# Create the app
doctl apps create --spec .do/app.yaml

# Get app ID and monitor deployment
doctl apps list
doctl apps logs <APP_ID>
```

---

## Step 3: Configure Your Deployment

### Custom Domain (Optional)

1. Go to your app in the DigitalOcean dashboard
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Update DNS records as instructed

### Environment Variables

If you need to add environment variables:

1. Go to your app in the DigitalOcean dashboard
2. Click "Settings" → "App-Level Environment Variables"
3. Add variables like:
   - `SECRET_KEY` - Custom secret key for Flask
   - `DATABASE_URL` - **REQUIRED** for data persistence. Use the connection string provided by your DigitalOcean Database.
     - Example: `postgresql://doadmin:PASSWORD@HOST:PORT/defaultdb?sslmode=require`
   - Custom user credentials (if you want to avoid hardcoding)

### Scaling

To handle more traffic:

1. Go to your app settings
2. Adjust the instance size or count
3. Plans available:
   - Basic ($5/month) - 512MB RAM
   - Professional ($12/month) - 1GB RAM
   - With auto-scaling available

---

## Step 4: Update Your Application

After making changes locally:

```bash
# Make your changes
# Then commit and push

git add .
git commit -m "Description of changes"
git push origin main

# DigitalOcean will automatically redeploy!
```

---

## Important Security Notes for Production

### 1. Change Default Passwords

Before deploying, edit `app.py` and change the default passwords:

```python
USERS = {
    'agent1': generate_password_hash('STRONG_PASSWORD_HERE'),
    'agent2': generate_password_hash('STRONG_PASSWORD_HERE'),
    'agent3': generate_password_hash('STRONG_PASSWORD_HERE'),
    'admin': generate_password_hash('STRONG_ADMIN_PASSWORD_HERE'),
}
```

### 2. Set a Secret Key

Add a strong secret key for Flask sessions:

```python
app.secret_key = os.environ.get('SECRET_KEY', 'your-super-secret-key-here-change-this')
```

Or set it as an environment variable in DigitalOcean.

### 3. Enable HTTPS

DigitalOcean App Platform automatically provides HTTPS, but you should:

- Force HTTPS redirects (optional, see code below)
- Use secure session cookies

### 4. Consider Database for Users

For production with many users, replace the in-memory `USERS` dictionary with a proper database:

- PostgreSQL (DigitalOcean managed)
- SQLite (for smaller deployments)

---

## Configuration Files Explained

### `.do/app.yaml`

Main configuration for DigitalOcean App Platform:

- Defines the service type (web)
- Sets Python environment
- Configures health checks
- Sets instance size and count

### `gunicorn_config.py`

Production WSGI server configuration:

- Worker processes
- Timeout settings
- Logging configuration
- Optimal for production use

### `Procfile`

Defines how to run the application:

- Used by some platforms as fallback
- Specifies the web server command

### `runtime.txt`

Specifies Python version for deployment

---

## Monitoring and Logs

### View Logs:

1. **Via Dashboard:**

   - Go to your app
   - Click "Runtime Logs"
   - View real-time logs

2. **Via CLI:**
   ```bash
   doctl apps logs <APP_ID> --follow
   ```

### Monitor Performance:

1. Go to your app dashboard
2. Check "Insights" tab
3. Monitor:
   - CPU usage
   - Memory usage
   - HTTP requests
   - Response times

---

## Troubleshooting

### App Won't Start

1. Check logs: `doctl apps logs <APP_ID>`
2. Verify `requirements.txt` is correct
3. Ensure Python version is compatible
4. Check for syntax errors

### Port Binding Issues

The app is configured to use `PORT` environment variable:

```python
port = int(os.environ.get('PORT', 5000))
```

DigitalOcean automatically sets this.

### Module Not Found Errors

Ensure `requirements.txt` includes all dependencies:

```
Flask==3.0.0
requests==2.31.0
Werkzeug==3.0.1
gunicorn==21.2.0
```

### Session/Login Issues

Check that the secret key is set properly and consistent across restarts.

---

## Costs

DigitalOcean App Platform pricing:

- **Basic:** $5/month (512MB RAM, 1 vCPU)
- **Professional:** $12/month (1GB RAM, 1 vCPU)
- **First $200 free** for new accounts (60 days)

---

## Next Steps After Deployment

1. **Test the Application:**

   - Visit your app URL
   - Login with credentials
   - Test proxy connection

2. **Share with Your Team:**

   - Give them the app URL
   - Provide login credentials
   - Monitor usage

3. **Set Up Monitoring:**

   - Enable alerts in DigitalOcean
   - Monitor resource usage
   - Check error logs regularly

4. **Consider Enhancements:**
   - Custom domain
   - Database for user management
   - Rate limiting
   - Additional security features

---

## Support

- **DigitalOcean Docs:** https://docs.digitalocean.com/products/app-platform/
- **App Platform Tutorial:** https://docs.digitalocean.com/products/app-platform/how-to/
- **Community Support:** https://www.digitalocean.com/community/

---

## Quick Reference Commands

```bash
# Push to GitHub
git add .
git commit -m "Update"
git push origin main

# View logs
doctl apps logs <APP_ID> --follow

# List apps
doctl apps list

# Get app info
doctl apps get <APP_ID>

# Restart app
doctl apps restart <APP_ID>
```

---

**Your Proxy Access Portal is now production-ready and can be deployed to DigitalOcean App Platform!** 🚀
