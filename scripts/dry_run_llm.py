# tests/local_ollama_dry_run.py
import json
import requests

from llm_client import extract_json

# One concrete Hyderabad eco-friendly autos policy/news URL
TEST_URL = "https://cleanmobilityshift.com/policy-regulation/electrification-of-three-wheelers-via-retrofitting-the-telangana-case-study/"

# Simple schema describing what we want back from the model
AUTO_SCHEMA = """
{
  "type": "object",
  "properties": {
    "total_new_eco_autos": { "type": "integer" },
    "electric_autos_cap": { "type": "integer" },
    "cng_autos_cap": { "type": "integer" },
    "lpg_autos_cap": { "type": "integer" },
    "retrofit_autos_cap": { "type": "integer" },
    "city": { "type": "string" },
    "state": { "type": "string" },
    "policy_reference": { "type": "string" }
  },
  "required": ["total_new_eco_autos", "city", "state"]
}
"""

def fetch_page_text(url: str) -> str:
    """
    Fetch raw HTML for the test URL.
    For a first dry run, we just pass HTML directly to the model.
    Later you can replace this with a cleaner HTML->text step.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text

def main():
    print(f"Fetching page: {TEST_URL}")
    html = fetch_page_text(TEST_URL)

    system_prompt = (
        "You are a strict data-extraction engine for transport policy.\n"
        "From this news article, extract the number of new eco-friendly auto permits "
        "for Hyderabad (total, and split into electric, CNG, LPG, and retrofitted autos), "
        "plus the city, state, and a short policy_reference.\n"
        "Follow the schema exactly and respond with ONE JSON object only."
    )

    data = extract_json(html, AUTO_SCHEMA, system_prompt)

    print("=== Extracted JSON from Ollama ===")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()