
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo


class ContentDriftRule(GovernanceRule):
    """GOV-004: Flags drifted/divergent files across folders where their content hashes differ."""

    @property
    def rule_id(self) -> str:
        return "GOV-004"

    @property
    def name(self) -> str:
        return "Content drift"

    @property
    def severity(self) -> str:
        return "CRITICAL"

    @property
    def category(self) -> str:
        return "CONSISTENCY"

    def evaluate(self, context: RuleContext) -> list[RuleViolationInfo]:
        violations = []

        for df in context.drift_report.drifted_files:
            for folder in df.divergent_folders:
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        folder_name=folder,
                        file_path=df.file_path,
                        description=(
                            f"File '{df.file_path}' in folder '{folder}' has drifted "
                            f"from the majority content hash. Drift score: {df.drift_score}."
                        ),
                        details={
                            "file_path": df.file_path,
                            "folder_name": folder,
                            "drift_score": df.drift_score,
                            "divergent_folders": df.divergent_folders,
                            "majority_hash": df.majority_hash,
                            "folder_hashes": df.folder_hashes
                        }
                    )
                )

        return violations
