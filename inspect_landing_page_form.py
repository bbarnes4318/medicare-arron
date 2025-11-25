"""
Helper script to inspect the landing page form and find:
1. Form submission endpoint
2. Form field names
3. Form method (GET/POST)

Usage: python inspect_landing_page_form.py
"""
import requests
from bs4 import BeautifulSoup
import re

LANDING_PAGE_URL = 'https://lowinsurancecost.com'

def inspect_form():
    """Inspect the landing page form"""
    try:
        print("="*60)
        print("Inspecting Landing Page Form")
        print("="*60)
        print(f"\nFetching: {LANDING_PAGE_URL}\n")
        
        # Fetch the page
        response = requests.get(LANDING_PAGE_URL, timeout=30)
        
        if response.status_code != 200:
            print(f"Error: Could not fetch page. Status code: {response.status_code}")
            return
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all forms
        forms = soup.find_all('form')
        
        if not forms:
            print("No forms found on the page.")
            print("\nThe form might be loaded via JavaScript.")
            print("Try inspecting the page in a browser with DevTools open.")
            return
        
        print(f"Found {len(forms)} form(s) on the page:\n")
        
        for i, form in enumerate(forms, 1):
            print(f"{'='*60}")
            print(f"FORM {i}")
            print(f"{'='*60}")
            
            # Form action (endpoint)
            action = form.get('action', '')
            if action:
                if action.startswith('http'):
                    print(f"Action (Full URL): {action}")
                else:
                    print(f"Action (Endpoint): {action}")
                    if not action.startswith('/'):
                        action = '/' + action
                    print(f"Full URL would be: {LANDING_PAGE_URL}{action}")
            else:
                print("Action: (empty - form submits to same page)")
            
            # Form method
            method = form.get('method', 'GET').upper()
            print(f"Method: {method}")
            
            # Find all input fields
            inputs = form.find_all(['input', 'select', 'textarea'])
            
            if inputs:
                print(f"\nForm Fields ({len(inputs)} total):")
                print("-" * 60)
                
                for inp in inputs:
                    field_type = inp.get('type', inp.name)
                    field_name = inp.get('name', '')
                    field_id = inp.get('id', '')
                    required = 'required' in inp.attrs or inp.get('required') == ''
                    
                    if field_name:
                        req_marker = " *" if required else ""
                        print(f"  Name: {field_name:<30} Type: {field_type:<15} ID: {field_id}{req_marker}")
                    elif field_id:
                        print(f"  ID: {field_id:<30} Type: {field_type:<15} (no name attribute)")
            
            print()
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        print("\n1. Set LANDING_PAGE_FORM_ENDPOINT environment variable:")
        if forms[0].get('action'):
            action = forms[0].get('action')
            if not action.startswith('http'):
                if not action.startswith('/'):
                    action = '/' + action
                print(f"   LANDING_PAGE_FORM_ENDPOINT='{action}'")
            else:
                print(f"   (Form uses full URL: {action})")
        else:
            print("   LANDING_PAGE_FORM_ENDPOINT='' (form submits to same page)")
        
        print("\n2. Update field names in app.py if they differ:")
        print("   Check the 'name' attributes above and update the payload")
        print("   dictionary in submit_form_through_proxy() function")
        
        print("\n3. If form is loaded via JavaScript:")
        print("   - Open the page in a browser")
        print("   - Open DevTools (F12)")
        print("   - Go to Network tab")
        print("   - Submit the form")
        print("   - Look for the POST request to find the endpoint")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        print("\nTry:")
        print("1. Check your internet connection")
        print("2. Verify the URL is correct")
        print("3. The site might be blocking automated requests")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    try:
        import bs4
    except ImportError:
        print("BeautifulSoup4 is required for this script.")
        print("Install it with: pip install beautifulsoup4")
        print("\nAlternatively, manually inspect the form:")
        print("1. Visit https://lowinsurancecost.com")
        print("2. Right-click the form > Inspect")
        print("3. Look for the <form> tag's 'action' attribute")
        print("4. Check all <input> tags for 'name' attributes")
    else:
        inspect_form()

