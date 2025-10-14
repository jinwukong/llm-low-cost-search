import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SearchConfig:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            possible_paths = [
                Path(__file__).parent / "search_config.yaml",
                Path(__file__).parent.parent / "search" / "search_config.yaml",
                Path.cwd() / "search_config.yaml",
                Path.cwd() / "search" / "search_config.yaml",
            ]

            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break

            if config_path is None:
                raise FileNotFoundError(f"search_config.yaml not found. Searched paths: {possible_paths}")

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def get_brave_config(self) -> Dict[str, Any]:
        return self.config.get("brave_search", {})

    def get_extraction_config(self) -> Dict[str, Any]:
        return self.config.get("content_extraction", {})

    def get_brave_api_key(self) -> str:
        api_key = self.config.get("brave_search", {}).get("api_key", "")

        if not api_key or api_key == "YOUR_BRAVE_API_KEY_HERE":
            raise ValueError(
                "Brave API key not configured!\n"
                "Please edit search_config.yaml and replace 'YOUR_BRAVE_API_KEY_HERE' "
                "with your actual API key.\n"
                "Get your API key from: https://brave.com/search/api/"
            )

        return api_key
    
    def get_search_params(self, profile: Optional[str] = None) -> Dict[str, Any]:
        brave_config = self.get_brave_config()
        params = brave_config.get("default_params", {}).copy()
        
        if profile:
            profiles = brave_config.get("profiles", {})
            if profile in profiles:
                params.update(profiles[profile])
        
        return params
    
    def get_rate_limit(self) -> float:
        return self.config.get("brave_search", {}).get("rate_limit", {}).get("requests_per_second", 1.0)

_global_config = None

def get_config(config_path: Optional[str] = None) -> SearchConfig:
    global _global_config
    if _global_config is None:
        _global_config = SearchConfig(config_path)
    return _global_config
