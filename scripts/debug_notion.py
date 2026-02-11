import os
import sys
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

if not NOTION_API_KEY:
    print("❌ NOTION_API_KEY is missing")
    sys.exit(1)

client = Client(auth=NOTION_API_KEY)

print(f"🔑 Using Key: {NOTION_API_KEY[:4]}...{NOTION_API_KEY[-4:]}")

try:
    print("\n🔍 Searching for ALL accessible objects...")
    # Search for everything
    response = client.search()
    results = response.get("results", [])
    
    if not results:
        print("⚠️  No results found!")
        print("   The integration has no access to any pages or databases.")
    
    for item in results:
        obj_type = item.get("object")
        title = "Untitled"
        
        if obj_type == "database":
            title = item.get("title", [{}])[0].get("plain_text", "Untitled")
        elif obj_type == "page":
             # Page titles are in properties, harder to get generically, usually "title" property
             props = item.get("properties", {})
             for key, val in props.items():
                 if val.get("type") == "title":
                     title = val.get("title", [{}])[0].get("plain_text", "Untitled")
                     break
        
        print(f"\n✅ FOUND {obj_type.upper()}:")
        print(f"   Name: {title}")
        print(f"   ID:   {item.get('id')}")
        print(f"   URL:  {item.get('url')}")

except Exception as e:
    print(f"❌ API Error: {e}")
