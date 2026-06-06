from datetime import datetime, timezone
from typing import List
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo
from app.rules.registry import get_rules_config


class ZeroPropagationRule(GovernanceRule):
    """GOV-010: Flags Jiras that have remained merged in exactly one folder for 14+ days."""

    @property
    def rule_id(self) -> str:
        return "GOV-010"

    @property
    def name(self) -> str:
        return "Zero propagation"

    @property
    def severity(self) -> str:
        return "CRITICAL"

    @property
    def category(self) -> str:
        return "PROPAGATION"

    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        violations = []
        config = get_rules_config().get(self.rule_id, {})
        threshold = config.get("threshold_days", 14.0)
        now = datetime.now(timezone.utc)

        for d in context.delays:
            merged_folders = [f for f, m_date in d.folder_merge_dates.items() if m_date is not None]
            
            if len(merged_folders) == 1:
                init_date = d.initial_commit_date
                if init_date.tzinfo is None:
                    init_date = init_date.replace(tzinfo=timezone.utc)
                
                elapsed_days = (now - init_date).total_seconds() / 86400.0
                if elapsed_days >= threshold:
                    folder_name = merged_folders[0]
                    violations.append(
                        RuleViolationInfo(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            category=self.category,
                            jira_id=d.jira_id,
                            description=(
                                f"Jira {d.jira_id} has zero propagation: it has resided in folder '{folder_name}' "
                                f"for {round(elapsed_days, 1)} days without propagating to any other environment."
                            ),
                            details={
                                "jira_id": d.jira_id,
                                "residing_folder": folder_name,
                                "elapsed_days": round(elapsed_days, 2),
                                "threshold_days": threshold
                            }
                        )
                    )

        return violations
