import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    "IPROYAL_HOST",
    "IPROYAL_PORT",
    "IPROYAL_USER",
    "IPROYAL_PASS"
]

print("="*40)
print("ENVIRONMENT VARIABLE CHECK")
print("="*40)

all_present = True
for var in required_vars:
    value = os.getenv(var)
    if value:
        masked = value[:2] + "*" * (len(value)-4) + value[-2:] if len(value) > 4 else "****"
        print(f"✅ {var}: Found")
    else:
        print(f"❌ {var}: MISSING or Empty")
        all_present = False

print("="*40)
if all_present:
    print("✅ All required variables are present.")
else:
    print("❌ Some variables are missing in your local .env file.")
    print("   Please update c:\\Users\\jimbo\\OneDrive\\Desktop\\medicare-form\\.env")
    print("   The 'Launch Proxy Browser' button runs ON YOUR COMPUTER,")
    print("   so it needs these variables locally, not just in DigitalOcean.")
print("="*40)
