import os
import yaml
from typing import Dict, Any, List
from app.rules.base import GovernanceRule

_config: Dict[str, Any] = {}


def get_rules_config() -> Dict[str, Any]:
    """Loads and caches rule configuration from config/rules.yaml."""
    global _config
    if not _config:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root_dir, "config", "rules.yaml")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = yaml.safe_load(f)
                    _config = data.get("rules", {}) if data else {}
            except Exception:
                pass
    return _config


def get_registered_rules() -> List[GovernanceRule]:
    """Returns instantiation of all registered governance rules."""
    # To be populated with rule imports
    from app.rules.gov_001_vanilla_only import VanillaOnlyRule
    from app.rules.gov_002_low_coverage import LowCoverageRule
    from app.rules.gov_003_severe_delay import SevereDelayRule
    from app.rules.gov_004_content_drift import ContentDriftRule
    from app.rules.gov_005_stale_jira import StaleJiraRule
    from app.rules.gov_006_single_folder import SingleFolderRule
    from app.rules.gov_007_author_isolation import AuthorIsolationRule
    from app.rules.gov_008_folder_regression import FolderRegressionRule
    from app.rules.gov_009_mass_missing import MassMissingRule
    from app.rules.gov_010_zero_propagation import ZeroPropagationRule

    config = get_rules_config()
    
    rules = [
        VanillaOnlyRule(),
        LowCoverageRule(),
        SevereDelayRule(),
        ContentDriftRule(),
        StaleJiraRule(),
        SingleFolderRule(),
        AuthorIsolationRule(),
        FolderRegressionRule(),
        MassMissingRule(),
        ZeroPropagationRule(),
    ]
    
    # Filter only enabled rules
    enabled_rules = []
    for r in rules:
        rule_cfg = config.get(r.rule_id, {})
        if rule_cfg.get("enabled", True):
            enabled_rules.append(r)
            
    return enabled_rules
