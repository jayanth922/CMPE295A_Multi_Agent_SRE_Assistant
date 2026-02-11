import os
import collections
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
client = Client(auth=NOTION_API_KEY)

print("🕵️‍♂️  Scanning for duplicate runbooks via Search API...")

try:
    # Search for all pages
    response = client.search(filter={"value": "page", "property": "object"})
    results = response.get("results", [])
    
    print(f"📄 Found {len(results)} total pages.")
    
    runbooks = collections.defaultdict(list)
    
    for page in results:
        page_id = page["id"]
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
            runbooks[title].append(page)

    # Print summary of what we have
    print(f"\n📚 Inventory:")
    for title, pages in sorted(runbooks.items()):
        print(f" - {title}: {len(pages)} copies")
        
    for title, pages in runbooks.items():
        print(f"🗑️  Archiving all copies of: {title}")
        for page in pages:
             try:
                 client.pages.update(page_id=page["id"], archived=True)
                 print(f"   ✅ Archived: {page['id']}")
             except Exception as e:
                 print(f"   ❌ Failed to archive {page['id']}: {e}")

    print("\n✨ Reset complete. All SRE runbooks archived.")

except Exception as e:
    print(f"❌ Error: {e}")
