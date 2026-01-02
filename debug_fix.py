import requests
from urllib.parse import quote

def test_smart_search(full_name):
    university_id = "I95457486" # UC Berkeley
    
    parts = full_name.strip().split()
    if not parts:
        print("Empty name")
        return

    last_name = parts[-1]
    first_name_part = parts[0] if len(parts) > 1 else ""
    
    print(f"\nSearching for Last Name: '{last_name}' (from input '{full_name}')")
    
    # API correct field is plural: last_known_institutions.id
    filter_val = f"display_name.search:{last_name},last_known_institutions.id:{university_id}"
    
    url = f"https://api.openalex.org/authors?filter={filter_val}&per_page=50"
    print(f"Requesting URL: {url}")
    
    try:
        # We use string concatenation for the URL to ensure 'requests' doesn't over-encode the filter value keys if we passed it as a dict.
        # Passing params={'filter': ...} causes encoding of ':' which might be the issue if the server is strict.
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed with {response.status_code}: {response.text}")
            return
            
        data = response.json()
        results = data.get('results', [])
        print(f"Found {len(results)} raw results for last name '{last_name}'.")
        
        # Smart Filter Logic
        matches = []
        for r in results:
            display_name = r['display_name']
            # Check if all parts of the search query are in the display name
            # simple case-insensitive check
            if all(part.lower() in display_name.lower() for part in parts):
                matches.append(r)
                print(f" [MATCH] {display_name} ({r['id']})")
            else:
                # print(f" [SKIP]  {display_name}")
                pass
                
        if not matches:
             print("No exact matches found after filtering.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_smart_search("Jay Keasling")
    test_smart_search("Keasling")
