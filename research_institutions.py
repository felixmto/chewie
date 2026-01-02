import requests

def search_institutions(query):
    url = "https://api.openalex.org/institutions"
    params = {
        'filter': f'display_name.search:{query}',
        'per_page': 10
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"\n--- Results for '{query}' ---")
        for result in data.get('results', []):
            print(f"ID: {result['id']}, Name: {result['display_name']}, Works count: {result['works_count']}")
    except Exception as e:
        print(f"Error searching '{query}': {e}")

queries = [
    "University of California San Francisco",
    "UCSF"
]

for q in queries:
    search_institutions(q)
