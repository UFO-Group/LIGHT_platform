"""
Step 1: Fetch Material Frequencies

Uses ArXiv API (stable source)
Note: PubChem Substance API returns SID counts (mixtures like gelatin, starch, etc.)

Output:
- material_frequencies.json
- api_source_data.json
"""

import json
import os
import time
import xml.etree.ElementTree as ET
from typing import Dict

import requests


def fetch_arxiv_count(material: str) -> int:
    """
    Fetch count from ArXiv API

    Args:
        material: Material name (space separated)

    Returns:
        Count
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(
                f"http://export.arxiv.org/api/query?search_query=all:{material}&max_results=1",
                timeout=30,
                headers=headers
            )
            tree = ET.fromstring(response.text)
            count = int(tree.find('.//{http://a9.com/-/spec/opensearch/1.1/}totalResults').text)
            print(f"  ArXiv: {material} = {count}")
            return count
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ArXiv API retry {attempt + 1}/{max_retries} for {material}: {e}")
                time.sleep(5)
            else:
                print(f"  ArXiv API error for {material}: {e}")
                return 0
    return 0


def fetch_pubchem_substance_count(material: str) -> int:
    """
    Fetch synonym count from PubChem Substance API

    Note: Uses 'substance' endpoint for mixtures (gelatin, starch, etc.)
          Pure compounds use 'compound' endpoint

    Args:
        material: Material name (space separated)

    Returns:
        Synonym count
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            # Use substance endpoint for mixtures/materials
            response = requests.get(
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/name/{material}/synonyms/JSON",
                timeout=30,
                headers=headers
            )
            data = response.json()
            # Returns synonym list, count as popularity metric
            if 'InformationList' in data and 'Information' in data['InformationList']:
                info = data['InformationList']['Information'][0]
                if 'Synonym' in info:
                    synonyms = info['Synonym']
                    # PubChem may return list or string
                    if isinstance(synonyms, list):
                        count = len(synonyms)
                    elif isinstance(synonyms, str):
                        count = 1  # If string, at least one synonym
                    else:
                        count = 0
                else:
                    count = 0
            else:
                count = 0

            print(f"  PubChem (Substance): {material} = {count}")
            return count
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  PubChem API retry {attempt + 1}/{max_retries} for {material}: {e}")
                time.sleep(5)
            else:
                print(f"  PubChem API error for {material}: {e}")
                return 0

    return 0


def calculate_material_frequencies() -> Dict[str, int]:
    """
    Calculate material frequencies

    For each material:
    1. If has alternatives, fetch all and merge results (take max for each API)
    2. material_freq = arxiv_count + pubchem_synonyms (equal weights)

    Returns:
        Material frequency dictionary
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(script_dir), "data")

    # Load formula-material mapping
    formula_materials_path = os.path.join(data_dir, "formula_materials.json")
    if not os.path.exists(formula_materials_path):
        # Fallback to database directory
        formula_materials_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "database", "formula_materials.json")

    with open(formula_materials_path, 'r', encoding='utf-8') as f:
        formula_materials = json.load(f)

    materials = formula_materials["materials"]
    material_frequencies = {}
    api_source_data_dict = {}

    # Material alternatives mapping
    material_alternatives = {
        "gelatin_methacrylate": ["gelatin methacrylate", "gelatin methacryloyl", "gelma"],
        "silk_fibroin": ["silk fibroin", "fibroin"],
        "polyethylene_glycol": ["polyethylene glycol", "peg", "polyethyleneglycol"],
        "polyvinyl_alcohol": ["polyvinyl alcohol", "pva"]
    }

    print("Calculating material frequencies (ArXiv + PubChem Substance, equal weights)...")
    print("=" * 80)

    for material in materials:
        # Get material name (underscore to space)
        material_name = material.replace('_', ' ')

        # Get aliases list
        alternatives = [material_name]
        if material in material_alternatives:
            alternatives.extend(material_alternatives[material])

        # Initialize API data for this material
        api_source_data = {
            'arxiv_count': 0,
            'pubchem_substance_count': 0
        }

        # Fetch API data for all alternatives, take max
        for alt in alternatives:
            # ArXiv
            arxiv_count = fetch_arxiv_count(alt)
            api_source_data['arxiv_count'] = max(api_source_data['arxiv_count'], arxiv_count)

            # PubChem Substance
            pubchem_count = fetch_pubchem_substance_count(alt)
            api_source_data['pubchem_substance_count'] = max(api_source_data['pubchem_substance_count'], pubchem_count)

            time.sleep(0.5)  # Rate limiting

        # Calculate equal-weighted frequency
        frequency = int(api_source_data['arxiv_count'] + api_source_data['pubchem_substance_count'])
        material_frequencies[material] = frequency
        api_source_data_dict[material] = {
            'arxiv_count': api_source_data['arxiv_count'],
            'pubchem_substance_count': api_source_data['pubchem_substance_count'],
            'total_frequency': frequency
        }

        print(f"  {material}: ArXiv={api_source_data['arxiv_count']}, "
              f"PubChem={api_source_data['pubchem_substance_count']}, Total={frequency}")
        print("-" * 80)

    # Create data directory
    os.makedirs(data_dir, exist_ok=True)

    # Save material frequencies
    with open(os.path.join(data_dir, "material_frequencies.json"), 'w', encoding='utf-8') as f:
        json.dump(material_frequencies, f, indent=2, ensure_ascii=False)

    # Save API source data
    with open(os.path.join(data_dir, "api_source_data.json"), 'w', encoding='utf-8') as f:
        json.dump(api_source_data_dict, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("Material frequencies saved to:")
    print(f"  {data_dir}/material_frequencies.json")
    print(f"  {data_dir}/api_source_data.json")
    print("=" * 80)

    return material_frequencies


if __name__ == "__main__":
    calculate_material_frequencies()
