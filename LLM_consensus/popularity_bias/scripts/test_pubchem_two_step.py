"""
Test two-step PubChem strategy:
1. Get CID: /rest/pug/compound/name/{material_name}/cids/JSON
2. Get PubMed refs: /rest/pug/compound/cid/{cid}/xrefs/PubMedID/JSON
"""

import requests
import json

def test_two_step_pubchem():
    # Test with gelatin
    material = "gelatin"

    # Step 1: Get CID
    cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{material}/cids/JSON"
    print(f"Step 1: Getting CID from {cid_url}")

    response = requests.get(cid_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Status: {response.status_code}")
    cid_data = response.json()
    print(f"Response: {json.dumps(cid_data, indent=2)}")

    # Step 2: Get PubMed refs (if CID available)
    if 'InformationList' in cid_data and 'Information' in cid_data['InformationList']:
        cid = cid_data['InformationList']['Information'][0]['CID']
        print(f"\nCID found: {cid}")

        pmid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/xrefs/PubMedID/JSON"
        print(f"\nStep 2: Getting PubMed refs from {pmid_url}")

        response = requests.get(pmid_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"Status: {response.status_code}")
        pmid_data = response.json()
        print(f"Response preview: {json.dumps(pmid_data, indent=2)[:1000]}")

        if 'InformationList' in pmid_data and 'Information' in pmid_data['InformationList']:
            refs = pmid_data['InformationList']['Information'][0]['PubMedID']
            print(f"\nPubMed references count: {len(refs) if refs else 0}")
        else:
            print("\nNo PubMed references found")
    else:
        print("\nNo CID found")

if __name__ == "__main__":
    test_two_step_pubchem()
