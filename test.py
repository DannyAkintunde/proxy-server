import requests

# Proxy server details
# 65.21.202.154
proxy = {
    "http": "http://127.0.0.1:8080",  # For HTTP connections
    "https": "http://127.0.0.1:8080",  # For HTTPS connections
}

# URL to test
url = "http://youtube.com"

try:
    # Make a request through the proxy
    response = requests.get(url, proxies=proxy, verify=False)  # verify=False to skip SSL cert verification

    # Print response details
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Content: {response.text[:500]}")  # Limiting content to 500 chars for readability

except requests.exceptions.ProxyError as e:
    print(f"Proxy Error: {e}")
except requests.exceptions.SSLError as e:
    print(f"SSL Error: {e}")
except Exception as e:
    print(f"Error: {e}")

