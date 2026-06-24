
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo
from app.rules.registry import get_rules_config


class MassMissingRule(GovernanceRule):
    """GOV-009: Flags folders that are missing merges for a large number of expected Jiras."""

    @property
    def rule_id(self) -> str:
        return "GOV-009"

    @property
    def name(self) -> str:
        return "Mass missing"

    @property
    def severity(self) -> str:
        return "HIGH"

    @property
    def category(self) -> str:
        return "COVERAGE"

    def evaluate(self, context: RuleContext) -> list[RuleViolationInfo]:
        violations = []
        config = get_rules_config().get(self.rule_id, {})
        threshold = config.get("threshold_jiras", 5)

        expected_folders = context.coverage_matrix.folders_list
        initial_folder = expected_folders[0] if expected_folders else "vanilla"

        for folder in expected_folders:
            if folder == initial_folder:
                continue

            missing_count = sum(
                1 for row in context.coverage_matrix.rows
                for f_detail in row.folders
                if f_detail.folder_name == folder and not f_detail.is_merged
            )

            if missing_count >= threshold:
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        folder_name=folder,
                        description=(
                            f"Folder '{folder}' is missing merges for {missing_count} Jiras, "
                            f"which meets or exceeds the critical threshold of {threshold} missing merges."
                        ),
                        details={
                            "folder_name": folder,
                            "missing_jiras_count": missing_count,
                            "threshold_jiras": threshold
                        }
                    )
                )

        return violations
