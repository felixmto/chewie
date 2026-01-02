import requests

def test_search(query):
    # UC Berkeley ID from app.py
    university_id = "I95457486" 
    authors_url = "https://api.openalex.org/authors"
    
    print(f"Testing query: '{query}'")
    params = {
        'filter': f'display_name.search:{query},last_known_institution.id:{university_id}',
        'per_page': 50
    }
    
    try:
        response = requests.get(authors_url, params=params, timeout=10)
        print(f"URL: {response.url}")
        response.raise_for_status()
        data = response.json()
        print(f"Success! Found {len(data['results'])} results.")
        for r in data['results']:
            print(f" - {r['display_name']} ({r['id']})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 1. Reproduce the error
    print("--- TRACE 1: Full Name ---")
    test_search("Jay Keasling")

    # 2. Try Last Name Only
    print("\n--- TRACE 2: Last Name Only ---")
    test_search("Keasling")
