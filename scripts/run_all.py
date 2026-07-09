import sys
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.auto_stock_retrofit_agent import run as run_auto
from agents.dc_charger_locator_agent import run as run_dc
from agents.summary_agent import run as run_summary

def load_config(config_path):
    """Load YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    """Run all agents with configuration from settings.yaml."""
    config = load_config("configs/settings.yaml")
    db_path = config['database']['path']
    
    print("Running Auto Stock & Retrofit Agent...")
    run_auto(db_path, config)
    
    print("Running DC Charger Locator Agent...")
    run_dc(db_path, config)
    
    print("Running Summary Agent...")
    run_summary(db_path, config)


if __name__ == "__main__":
    main()