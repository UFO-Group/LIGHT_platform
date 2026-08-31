"""
Test different PubChem API URL formats
"""

import requests

# Test different URL formats for gelatin
urls = [
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/gelatin/synonyms/JSON",
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/gelatin/property/SynonymCount/JSON",
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/name/gelatin/synonyms/JSON",
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/gelatin/JSON",
]

headers = {'User-Agent': 'Mozilla/5.0'}

for i, url in enumerate(urls, 1):
    print(f"\n{'=' * 80}")
    print(f"URL {i}: {url}")
    print('=' * 80)

    try:
        response = requests.get(url, timeout=30, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response preview: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

# Also try to search first
print("\n\n" + "=" * 80)
print("Testing search then CID lookup")
print("=" * 80)

try:
    # First search for gelatin
    search_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/gelatins/fastidentity/JSON"
    response = requests.get(search_url, timeout=30, headers=headers)
    print(f"\nSearch URL: {search_url}")
    print(f"Status: {response.status_code}")
    print(f"Search response: {response.text[:500]}")

    # Try CID lookup
    cid_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/90088460/synonyms/JSON"
    response = requests.get(cid_url, timeout=30, headers=headers)
    print(f"\nCID URL: {cid_url}")
    print(f"Status: {response.status_code}")
    print(f"CID response preview: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
