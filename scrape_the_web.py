# VIGI_FUNCTIONS_PATH/scrapeweb.py

import json
import re
from urllib.parse import urlparse, urlunparse
import requests
from bs4 import BeautifulSoup

# Ensure 'requests' and 'beautifulsoup4' are installed in your environment:
# pip install requests beautifulsoup4

def scrapeweb(url: str) -> str:  # RENAMED function to match filename "scrapeweb"
    """
    Fetches and returns the textual content from a given URL.
    It attempts to autocomplete partial URLs to valid HTTP/HTTPS URLs.
    Returns the scraped text or an error message, formatted as a JSON string.

    Args:
        url (str): The URL of the website to scrape (e.g., 'example.com', 'http://example.com', 'www.example.com/path').
                   Partial URLs will be autocompleted.
    """

    def _autocomplete_url(partial_url: str) -> str:
        partial_url = partial_url.strip()
        if not partial_url:
            return ""

        if partial_url.startswith(("http://", "https://", "ftp://", "ftps://")):
            try:
                parsed = urlparse(partial_url)
                if parsed.netloc:
                    return urlunparse(parsed)
                else:
                    domain_part = partial_url.split('//', 1)[-1]
                    if not domain_part:
                        return f"https://{domain_part}" # Will likely be invalid, handled later
                    return f"https://{domain_part}" if '.' in domain_part else f"https://{domain_part}.com"
            except ValueError:
                return f"https://{partial_url}"

        parsed = urlparse(f"//{partial_url}")
        scheme = "https"
        netloc = parsed.netloc
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment

        if not netloc:
            first_segment = partial_url.split('/')[0]
            if first_segment and '.' in first_segment:
                netloc = first_segment
                path_parts = partial_url.split('/')[1:]
                path = "/" + "/".join(path_parts) if path_parts else ''
            elif first_segment:
                netloc = f"{first_segment}.com"
                path_parts = partial_url.split('/')[1:]
                path = "/" + "/".join(path_parts) if path_parts else ''
            else:
                netloc = "example.com" # Placeholder

        if netloc and path and not path.startswith('/'):
            path = '/' + path
        if netloc and not path:
            path = '/'
        
        return urlunparse((scheme, netloc, path, '', query, fragment))

    # --- Main logic of scrapeweb ---
    if not url or not url.strip():
        return json.dumps({"status": "error", "message": "URL cannot be empty."})

    completed_url = _autocomplete_url(url)

    try:
        parsed_final_url = urlparse(completed_url)
        if not parsed_final_url.scheme or not parsed_final_url.netloc:
            return json.dumps({
                "status": "error", "original_url": url, "attempted_url": completed_url,
                "message": "Failed to construct a valid, absolute URL. Scheme or domain is missing."
            })
    except ValueError:
        return json.dumps({
            "status": "error", "original_url": url, "attempted_url": completed_url,
            "message": "The constructed URL is invalid and cannot be parsed."
        })

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 VigiScraper/1.0"
    }

    try:
        response = requests.get(completed_url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        for script_or_style in soup(["script", "style", "nav", "footer", "aside"]):
            script_or_style.decompose()

        text_content = soup.get_text(separator="\n", strip=True)
        text_content = re.sub(r'\n\s*\n', '\n', text_content).strip()

        max_len = 5000
        if len(text_content) > max_len:
            text_content = text_content[:max_len] + "\n... (content truncated)"

        return json.dumps({
            "status": "success", "original_url": url, "scraped_url": completed_url,
            "content_preview": text_content[:200] + ("..." if len(text_content) > 200 else ""),
            "full_content": text_content
        }, ensure_ascii=False)

    except requests.exceptions.HTTPError as e:
        error_response = {"status": "error", "original_url": url, "scraped_url": completed_url, "message": f"HTTP error occurred: {str(e)}"}
    except requests.exceptions.ConnectionError as e:
        error_response = {"status": "error", "original_url": url, "scraped_url": completed_url, "message": f"Connection error: {str(e)}"}
    except requests.exceptions.Timeout as e:
        error_response = {"status": "error", "original_url": url, "scraped_url": completed_url, "message": f"Request timed out: {str(e)}"}
    except requests.exceptions.RequestException as e:
        error_response = {"status": "error", "original_url": url, "scraped_url": completed_url, "message": f"Error during web request: {str(e)}"}
    except Exception as e:
        error_response = {"status": "error", "original_url": url, "scraped_url": completed_url, "message": f"An unexpected error occurred: {str(e)}"}
    
    return json.dumps(error_response)


# Example Usage (for testing this file directly):
if __name__ == "__main__":
    print(f"--- Testing function: scrapeweb ---") # Updated print statement

    test_urls = [
        "google.com", "http://example.com", "www.github.com/features", "openai",
        "nonexistentdomain12345.org", "http://localhost:12345/notrunning",
        "badscheme://example.com", "example.com/some/path?query=1#fragment",
        "  whitespace.com/test  ", "news.ycombinator.com", "slashdot.org",
        "//broken.url/path", "/just/a/path"
    ]

    for test_url in test_urls:
        print(f"\n--- Testing URL: '{test_url}' ---")
        result_json_str = scrapeweb(url=test_url) # Updated function call
        try:
            result_data = json.loads(result_json_str)
            print(f"Original URL: {result_data.get('original_url')}")
            print(f"Attempted/Scraped URL: {result_data.get('scraped_url')}")
            print(f"Status: {result_data.get('status')}")
            if result_data.get('status') == 'success':
                print(f"Content Preview (first ~100 chars): {result_data.get('full_content', '')[:100]}...")
            else:
                print(f"Message: {result_data.get('message')}")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON response: {result_json_str}")
        print("-" * 20)
