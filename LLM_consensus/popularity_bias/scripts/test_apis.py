"""
API Test Script - Test all three APIs individually
"""

import requests
import xml.etree.ElementTree as ET
import time


def test_datamuse(material: str):
    """Test Datamuse API"""
    try:
        response = requests.get(
            f"https://api.datamuse.com/words?ml={material}&max=1",
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        print(f"  Datamuse status: {response.status_code}")
        if response.json():
            count = response.json()[0].get('numFound', 0)
            print(f"  Datamuse result: {count}")
            return count
        else:
            print(f"  Datamuse result: Empty response")
            return 0
    except Exception as e:
        print(f"  Datamuse error: {e}")
        return 0


def test_arxiv(material: str):
    """Test ArXiv API"""
    try:
        response = requests.get(
            f"http://export.arxiv.org/api/query?search_query=all:{material}&max_results=1",
            timeout=30,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        print(f"  ArXiv status: {response.status_code}")
        print(f"  ArXiv response text preview: {response.text[:200]}")
        tree = ET.fromstring(response.text)
        count = int(tree.find('.//{http://a9.com/-/spec/opensearch/1.1/}totalResults').text)
        print(f"  ArXiv result: {count}")
        return count
    except Exception as e:
        print(f"  ArXiv error: {e}")
        return 0


def test_pubchem(material: str):
    """Test PubChem API"""
    try:
        response = requests.get(
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{material}/synonyms/JSON",
            timeout=30,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        print(f"  PubChem status: {response.status_code}")
        data = response.json()
        print(f"  PubChem response keys: {list(data.keys())}")
        if 'InformationList' in data and 'Information' in data['InformationList']:
            info = data['InformationList']['Information'][0]
            print(f"  PubChem info keys: {list(info.keys())}")
            if 'Synonym' in info:
                synonyms = info['Synonym']
                if isinstance(synonyms, list):
                    count = len(synonyms)
                elif isinstance(synonyms, str):
                    count = 1
                else:
                    count = 0
                print(f"  PubChem result: {count} synonyms")
                return count
            else:
                print(f"  PubChem result: No synonyms found")
                return 0
        else:
            print(f"  PubChem result: No information found")
            return 0
    except Exception as e:
        print(f"  PubChem error: {e}")
        return 0


def main():
    """Test all APIs"""
    materials = [
        "gelatin",
        "gelatin methacrylate",
        "polyacrylamide",
        "chitosan",
        "silk fibroin",
        "polyethylene glycol",
        "starch",
        "chitin",
        "cellulose",
        "polyvinyl alcohol"
    ]

    for material in materials:
        print(f"\n{'=' * 80}")
        print(f"Testing material: {material}")
        print(f"{'=' * 80}")

        datamuse_result = test_datamuse(material)
        time.sleep(1)

        arxiv_result = test_arxiv(material)
        time.sleep(1)

        pubchem_result = test_pubchem(material)
        time.sleep(1)

        total = datamuse_result + arxiv_result + pubchem_result
        print(f"\n  Total: {total}")


if __name__ == "__main__":
    main()
