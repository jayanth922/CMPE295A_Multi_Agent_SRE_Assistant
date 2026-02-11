import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
client = Client(auth=NOTION_API_KEY)

print("🕵️‍♂️  Final Audit of SRE Runbooks...")

try:
    # Search for all pages
    response = client.search(filter={"value": "page", "property": "object"})
    results = response.get("results", [])
    
    pages = []
    for page in results:
        props = page.get("properties", {})
        title = "Untitled"
        
        # Extract Title
        for key, val in props.items():
            if val["type"] == "title":
                t_list = val.get("title", [])
                if t_list:
                    title = t_list[0].get("plain_text", "Untitled")
                break
        
        # Only care about SRE- runbooks
        if title.startswith("SRE-"):
            pages.append(title)

    pages.sort()
    
    print(f"✅ Found {len(pages)} SRE Runbooks:")
    for p in pages:
        print(f" - {p}")

except Exception as e:
    print(f"❌ Error: {e}")
