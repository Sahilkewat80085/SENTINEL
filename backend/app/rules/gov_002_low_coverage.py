from typing import List
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo
from app.rules.registry import get_rules_config


class LowCoverageRule(GovernanceRule):
    """GOV-002: Flags folders whose coverage falls below the configured threshold."""

    @property
    def rule_id(self) -> str:
        return "GOV-002"

    @property
    def name(self) -> str:
        return "Low coverage"

    @property
    def severity(self) -> str:
        return "HIGH"

    @property
    def category(self) -> str:
        return "COVERAGE"

    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        violations = []
        config = get_rules_config().get(self.rule_id, {})
        threshold = config.get("threshold_pct", 25.0)

        expected_folders = context.coverage_matrix.folders_list
        initial_folder = expected_folders[0] if expected_folders else "vanilla"

        for f_health in context.folder_health:
            if f_health.folder_name == initial_folder:
                # Typically, initial folder is the baseline source folder so it won't be flagged for low coverage
                continue
                
            if f_health.coverage_score < threshold:
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        folder_name=f_health.folder_name,
                        description=(
                            f"Folder '{f_health.folder_name}' has low coverage of "
                            f"{f_health.coverage_score}%, which is below the threshold of {threshold}%."
                        ),
                        details={
                            "folder_name": f_health.folder_name,
                            "coverage_score": f_health.coverage_score,
                            "threshold_pct": threshold
                        }
                    )
                )

        return violations
