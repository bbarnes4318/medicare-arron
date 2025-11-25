# 🚀 Proxy Access Portal

A secure web application for managing agent access to IPRoyal proxy services.

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/bbarnes4318/proxy/tree/main)

## 🌟 Features

- 🔐 Secure multi-user authentication system
- 📊 Real-time proxy connection testing
- 🔑 Easy credential management with one-click copying
- 📚 Comprehensive documentation with code examples
- 🎯 RESTful API endpoints for automation
- 🎨 Modern, responsive UI design
- 🚀 Production-ready with Gunicorn WSGI server

## 🏃 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the portal:**
   - Open http://localhost:5000
   - Login with: `agent1` / `password123`

### Deploy to DigitalOcean

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick Deploy:**
1. Push code to GitHub
2. Connect to DigitalOcean App Platform
3. Auto-deploy from `.do/app.yaml` configuration

## 🔑 Default Credentials

**Web Portal Access:**
- Username: `agent1`, `agent2`, `agent3`, or `admin`
- Password: `password123` (or `admin123` for admin)

**⚠️ IMPORTANT:** Change these passwords before production deployment!

## 📋 Project Structure

```
proxy/
├── app.py                    # Main Flask application
├── gunicorn_config.py        # Production WSGI config
├── requirements.txt          # Python dependencies
├── runtime.txt              # Python version
├── Procfile                 # Process configuration
├── .do/
│   └── app.yaml            # DigitalOcean config
├── templates/
│   ├── login.html          # Login page
│   ├── dashboard.html      # Main dashboard
│   ├── credentials.html    # Credentials page
│   └── documentation.html  # Usage documentation
└── DEPLOYMENT.md           # Deployment guide
```

## 🔧 Configuration

### Environment Variables

- `PORT` - Server port (default: 8080 on DigitalOcean, 5000 locally)
- `FLASK_ENV` - Environment (production/development)
- `SECRET_KEY` - Flask session secret (optional, auto-generated)

### Proxy Configuration

Edit `PROXY_CONFIG` in `app.py`:

```python
PROXY_CONFIG = {
    'host': 'geo.iproyal.com',
    'port': 12321,
    'username': 'your-username',
    'password': 'your-password',
    'country': 'United States',
    'rotation': 'Randomize IP'
}
```

## 🛡️ Security

- ✅ Password hashing with Werkzeug
- ✅ Session-based authentication
- ✅ HTTPS support (automatic on DigitalOcean)
- ✅ Secure credential storage
- ⚠️ Change default passwords before production
- ⚠️ Set custom `SECRET_KEY` environment variable

## 📚 API Endpoints

All endpoints require authentication:

- `POST /api/test-proxy` - Test proxy connection
- `POST /api/proxy-request` - Make requests through proxy
- `GET /api/proxy-info` - Get proxy configuration

## 🎯 Usage Example

```python
import requests

proxy_url = 'http://username:password@geo.iproyal.com:12321'
proxies = {'http': proxy_url, 'https': proxy_url}

response = requests.get('https://ipv4.icanhazip.com', proxies=proxies)
print(f"Your IP: {response.text.strip()}")
```

## 📱 Pages

1. **Dashboard** - View status, test connections
2. **Credentials** - Copy proxy details and code snippets
3. **Documentation** - Complete usage guide with examples

## 🚀 Deployment

### DigitalOcean App Platform

1. Push to GitHub
2. Create new app in DigitalOcean
3. Connect repository
4. Deploy automatically

**Cost:** Starting at $5/month

### Other Platforms

- **Heroku:** Use `Procfile`
- **AWS/GCP:** Use `gunicorn_config.py`
- **Docker:** Create Dockerfile with Python 3.11

## 🔄 Updates

To update the deployed application:

```bash
git add .
git commit -m "Update description"
git push origin main
```

DigitalOcean will automatically redeploy.

## 🆘 Troubleshooting

**Can't connect to proxy:**
- Verify credentials are correct
- Check firewall settings
- Ensure internet connectivity

**Login not working:**
- Clear browser cookies
- Check that passwords were set correctly
- Verify Flask secret key is set

**Deployment failed:**
- Check logs in DigitalOcean dashboard
- Verify all files are committed
- Ensure `requirements.txt` is correct

## 📖 Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [In-app Documentation] - Access after login at `/documentation`

## 🤝 Support

For issues or questions:
1. Check the in-app documentation
2. Review deployment logs
3. Verify proxy credentials

## 📄 License

This project is provided as-is for internal use.

---

**Built with Flask, Python, and ❤️**

**Deployed on:** DigitalOcean App Platform  
**Proxy Service:** IPRoyal (US Rotating IPs)
