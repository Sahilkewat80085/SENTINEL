from typing import List
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo
from app.rules.registry import get_rules_config


class FolderRegressionRule(GovernanceRule):
    """GOV-008: Flags folders that have suffered health score degradation compared to previous state."""

    @property
    def rule_id(self) -> str:
        return "GOV-008"

    @property
    def name(self) -> str:
        return "Folder regression"

    @property
    def severity(self) -> str:
        return "HIGH"

    @property
    def category(self) -> str:
        return "CONSISTENCY"

    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        violations = []
        config = get_rules_config().get(self.rule_id, {})
        threshold = config.get("threshold_points", 10.0)

        for f_health in context.folder_health:
            prev_score = context.previous_health.get(f_health.folder_name)
            if prev_score is None:
                continue

            drop = prev_score - f_health.health_score
            if drop >= threshold:
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        folder_name=f_health.folder_name,
                        description=(
                            f"Folder '{f_health.folder_name}' has suffered a severe health regression: "
                            f"score dropped by {round(drop, 2)} points (from {prev_score} to {f_health.health_score})."
                        ),
                        details={
                            "folder_name": f_health.folder_name,
                            "previous_health_score": prev_score,
                            "current_health_score": f_health.health_score,
                            "regression_drop_points": round(drop, 2),
                            "threshold_points": threshold
                        }
                    )
                )

        return violations
