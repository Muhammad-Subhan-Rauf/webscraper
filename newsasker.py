import requests
import json
from InquirerPy import inquirer

def fetch_and_display_news() -> str:
    """
    Prompts the user to select a NewsAPI endpoint and query parameters,
    fetches the news, and displays the results.
    
    Returns:
        JSON-formatted string indicating success or failure, including
        article titles and URLs.
    """
    # Step 1: Select endpoint
    endpoint = inquirer.select(
        message="Select endpoint:",
        choices=["top-headlines", "everything"],
        default="top-headlines",
        pointer="👉",
        instruction="Use ↑/↓ and Enter"
    ).execute()

    # Step 2: Build query params
    api_key = inquirer.text(message="Enter your NewsAPI.org API key:").execute()
    params = {"apiKey": api_key}

    if endpoint == "top-headlines":
        country = inquirer.text(
            message="Country code (2‑letter, e.g., 'us') [optional]:",
            default=""
        ).execute()
        if country:
            params["country"] = country
        category = inquirer.text(
            message="Category (business, sports, technology...) [optional]:",
            default=""
        ).execute()
        if category:
            params["category"] = category
    elif endpoint == "everything":
        query = inquirer.text(message="Search keywords (e.g., 'bitcoin'):").execute()
        params["q"] = query
        from_date = inquirer.text(
            message="From date (YYYY‑MM‑DD) [optional]:",
            default=""
        ).execute()
        if from_date:
            params["from"] = from_date

    page_size = inquirer.text(
        message="Number of articles to fetch (max 100):",
        default="5",
        validate=lambda val: val.isdigit() and 1 <= int(val) <= 100
    ).execute()
    params["pageSize"] = int(page_size)

    # Step 3: Make request
    base_url = f"https://newsapi.org/v2/{endpoint}"
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"API request failed: {e}"
        })

    # Step 4: Check response
    status = data.get("status")
    if status != "ok":
        return json.dumps({
            "status": "error",
            "message": f"API returned status '{status}': {data.get('message')}"
        })

    articles = data.get("articles", [])
    results = [
        {"title": art.get("title"), "url": art.get("url")}
        for art in articles
    ]

    # Step 5: Display
    for idx, art in enumerate(results, start=1):
        print(f"{idx}. {art['title']}")
        print(f"   {art['url']}")
        print()

    return json.dumps({
        "status": "success",
        "endpoint": endpoint,
        "params": params,
        "articles": results
    })

if __name__ == "__main__":
    print(fetch_and_display_news())
