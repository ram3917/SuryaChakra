"""
FetchData: Unified data fetching and Perplexity-powered extraction from sources.yaml

This module provides a FetchData class that:
- Reads sources.yaml and selects relevant sources by agent type
- Fetches HTML/PDF content from URLs into data/raw/
- Logs source URLs and fetch timestamps
- Uses Perplexity API to extract structured data from raw content
- Returns validated data matching expected schemas
"""

import yaml
import json
import requests
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

# Import perplexity client from scripts directory
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from scripts.llm_client import extract_json


class FetchData:
    """
    Unified data fetching and Perplexity-powered extraction interface.
    
    Fetches content from sources.yaml URLs, stores raw files with metadata,
    and uses Perplexity API to extract structured data.
    """

    def __init__(self, sources_config_path: str = "configs/sources.yaml"):
        """
        Initialize FetchData with sources configuration.

        Args:
            sources_config_path: Path to sources.yaml configuration file
        """
        self.config_path = Path(sources_config_path)
        self.sources = self._load_sources_config()
        self.raw_data_dir = Path("data/raw")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def _load_sources_config(self) -> Dict:
        """
        Load and parse sources.yaml configuration file.

        Returns:
            Dictionary with sources configuration
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Sources configuration not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing sources.yaml: {e}")

    def _get_relevant_sources(self, agent_type: str) -> Dict[str, Dict]:
        """
        Get source sections relevant to a specific agent type.

        Args:
            agent_type: 'auto_stock', 'charger', 'usage_pattern', or 'cost_comparison'

        Returns:
            Dictionary of relevant source sections with their entries
        """
        sources = self.sources.get('sources', {})
        
        source_mapping = {
            'auto_stock': ['policy', 'autos_policy_hyd', 'retrofit_targets', 'vehicle_stats'],
            'charger': ['charging'],
            'usage_pattern': ['mobility_studies', 'vehicle_stats'],
            'cost_comparison': ['emissions_and_grid'],
        }
        
        relevant_sections = source_mapping.get(agent_type, [])
        relevant_sources = {}
        
        for section in relevant_sections:
            if section in sources:
                relevant_sources[section] = sources[section]
        
        return relevant_sources

    def _fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from URL (HTML or PDF).

        Args:
            url: URL to fetch

        Returns:
            Raw content as string, or None if fetch fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # For HTML, return text; for PDF, return text representation
            if 'application/pdf' in response.headers.get('content-type', ''):
                return f"[PDF Content from {url}]\n[Note: PDF extraction requires additional processing]"
            else:
                return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _save_raw_content(self, url: str, content: str, source_type: str) -> Path:
        """
        Save raw fetched content with metadata.

        Args:
            url: Source URL
            content: Content text
            source_type: Type of source (policy, autos_policy_hyd, charging, etc.)

        Returns:
            Path to saved file
        """
        timestamp = datetime.now()
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{source_type}_{url_hash}_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.raw_data_dir / filename
        
        # Save content with metadata header
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Source Metadata\n")
            f.write(f"URL: {url}\n")
            f.write(f"Type: {source_type}\n")
            f.write(f"Fetched: {timestamp.isoformat()}\n")
            f.write(f"# Content\n\n")
            f.write(content)
        
        return filepath

    def _extract_with_perplexity(self, content: str, schema: Dict, context: str) -> Optional[List[Dict]]:
        """
        Use Perplexity API to extract structured data from content.

        Args:
            content: Raw text content to extract from
            schema: Expected output schema (as dict with field names and types)
            context: Context about what to extract (e.g., 'auto-rickshaw data')

        Returns:
            List of extracted records matching schema, or None on error
        """
        try:
            schema_description = json.dumps(schema, indent=2)
            
            system_prompt = f"""You are a data extraction specialist. 
                    Extract {context} from the provided text.
                    Return a JSON array of objects, each matching the schema.
                    If multiple records are found, return them as an array.
                    If no data matches, return an empty array [].
                    Return ONLY valid JSON, no additional text."""
            
            # Limit content to avoid token limits
            limited_content = content[:3000]
            
            result = extract_json(limited_content, schema_description, system_prompt)
            
            # Ensure result is a list
            if isinstance(result, dict):
                return [result]
            elif isinstance(result, list):
                return result
            
            return None
        except Exception as e:
            print(f"Error during Perplexity extraction: {e}")
            return None

    def fetch_and_extract_autos(self) -> List[Dict]:
        """
        Fetch auto-rickshaw data sources and extract structured data.

        Returns:
            List of auto records with fields:
            - registration_number
            - year_of_registration
            - fuel_type
            - location_zone
            - permit_type (optional)
        """
        relevant_sources = self._get_relevant_sources('auto_stock')
        all_records = []
        
        schema = {
            "registration_number": "string (e.g., TS01AB0001)",
            "year_of_registration": "integer (2008-2024)",
            "fuel_type": "string (petrol, diesel, cng, lpg, electric)",
            "location_zone": "string (inside_orr, outside_orr)",
            "permit_type": "string or null (optional)"
        }
        
        for section, entries in relevant_sources.items():
            for entry_name, entry_data in entries.items():
                url = entry_data.get('url')
                purpose = entry_data.get('purpose', '')
                
                if not url:
                    continue
                
                print(f"[AutoStock] Fetching {entry_name}: {url}")
                content = self._fetch_url(url)
                
                if content:
                    raw_path = self._save_raw_content(url, content, section)
                    print(f"  -> Saved to {raw_path}")
                    
                    # Extract with Perplexity
                    records = self._extract_with_perplexity(
                        content,
                        schema,
                        f"auto-rickshaw registration data from {purpose}"
                    )
                    
                    if records:
                        all_records.extend(records)
                        print(f"  -> Extracted {len(records)} records")
        
        return all_records

    def fetch_and_extract_chargers(self) -> List[Dict]:
        """
        Fetch charger infrastructure data sources and extract structured data.

        Returns:
            List of charger records with fields:
            - name
            - lat
            - lon
            - power_kw (optional)
            - connector_type (optional)
        """
        relevant_sources = self._get_relevant_sources('charger')
        all_records = []
        
        schema = {
            "name": "string (charger name/location)",
            "lat": "float (latitude)",
            "lon": "float (longitude)",
            "power_kw": "float or null (charging power in kW)",
            "connector_type": "string or null (Bharat DC, CCS, CHAdeMO, Type 2, etc.)"
        }
        
        for section, entries in relevant_sources.items():
            for entry_name, entry_data in entries.items():
                url = entry_data.get('url')
                purpose = entry_data.get('purpose', '')
                
                if not url:
                    continue
                
                print(f"[DCCharger] Fetching {entry_name}: {url}")
                content = self._fetch_url(url)
                
                if content:
                    raw_path = self._save_raw_content(url, content, section)
                    print(f"  -> Saved to {raw_path}")
                    
                    # Extract with Perplexity
                    records = self._extract_with_perplexity(
                        content,
                        schema,
                        f"DC charging station data from {purpose}"
                    )
                    
                    if records:
                        all_records.extend(records)
                        print(f"  -> Extracted {len(records)} records")
        
        return all_records

    def fetch_and_extract_usage_patterns(self) -> List[Dict]:
        """
        Fetch usage pattern data sources and extract structured data.

        Returns:
            List of usage pattern records
        """
        relevant_sources = self._get_relevant_sources('usage_pattern')
        all_records = []
        
        schema = {
            "segment": "string (auto-rickshaw operating profile)",
            "km_per_day": "float (kilometers per day)",
            "hours_per_day": "float (operating hours per day)",
            "days_per_month": "float (operating days per month)",
            "energy_use_kwh_per_km": "float (energy consumption)",
        }
        
        for section, entries in relevant_sources.items():
            for entry_name, entry_data in entries.items():
                url = entry_data.get('url')
                purpose = entry_data.get('purpose', '')
                
                if not url:
                    continue
                
                print(f"[UsagePattern] Fetching {entry_name}: {url}")
                content = self._fetch_url(url)
                
                if content:
                    raw_path = self._save_raw_content(url, content, section)
                    print(f"  -> Saved to {raw_path}")
                    
                    records = self._extract_with_perplexity(
                        content,
                        schema,
                        f"auto-rickshaw usage pattern data from {purpose}"
                    )
                    
                    if records:
                        all_records.extend(records)
                        print(f"  -> Extracted {len(records)} records")
        
        return all_records

    @staticmethod
    def validate_auto_record(record: Dict) -> bool:
        """Validate auto record has required fields."""
        required = ['registration_number', 'year_of_registration', 'fuel_type', 'location_zone']
        return all(field in record for field in required)

    @staticmethod
    def validate_charger_record(record: Dict) -> bool:
        """Validate charger record has required fields."""
        required = ['name', 'lat', 'lon']
        return all(field in record for field in required)

    def parse_auto_data(self, data: List[Dict]) -> List[Dict]:
        """Validate and normalize auto records."""
        parsed = []
        for record in data:
            if not self.validate_auto_record(record):
                continue
            try:
                parsed_record = {
                    'registration_number': str(record['registration_number']),
                    'year_of_registration': int(record['year_of_registration']),
                    'fuel_type': str(record['fuel_type']).lower(),
                    'location_zone': str(record['location_zone']).lower(),
                    'permit_type': record.get('permit_type'),
                    'retrofit_status': record.get('retrofit_status', 'not_retrofitted'),
                }
                parsed.append(parsed_record)
            except (ValueError, TypeError):
                continue
        return parsed

    def parse_charger_data(self, data: List[Dict]) -> List[Dict]:
        """Validate and normalize charger records."""
        parsed = []
        for record in data:
            if not self.validate_charger_record(record):
                continue
            try:
                parsed_record = {
                    'name': str(record['name']),
                    'lat': float(record['lat']),
                    'lon': float(record['lon']),
                    'power_kw': float(record.get('power_kw')) if record.get('power_kw') else None,
                    'connector_type': record.get('connector_type'),
                }
                parsed.append(parsed_record)
            except (ValueError, TypeError):
                continue
        return parsed
