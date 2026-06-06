from datetime import datetime, timezone
from typing import List
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo
from app.rules.registry import get_rules_config


class StaleJiraRule(GovernanceRule):
    """GOV-005: Flags Jiras that have been inactive for more than the threshold (default 60 days)."""

    @property
    def rule_id(self) -> str:
        return "GOV-005"

    @property
    def name(self) -> str:
        return "Stale Jira"

    @property
    def severity(self) -> str:
        return "MEDIUM"

    @property
    def category(self) -> str:
        return "PROPAGATION"

    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        violations = []
        config = get_rules_config().get(self.rule_id, {})
        threshold = config.get("threshold_days", 60.0)
        now = datetime.now(timezone.utc)

        for summary in context.jira_summaries:
            last_updated = summary.get("last_updated")
            if not last_updated:
                continue

            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)

            elapsed_days = (now - last_updated).total_seconds() / 86400.0
            if elapsed_days >= threshold:
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        jira_id=summary["jira_id"],
                        description=(
                            f"Jira {summary['jira_id']} has been inactive for {round(elapsed_days, 1)} "
                            f"days, exceeding the threshold of {threshold} days."
                        ),
                        details={
                            "jira_id": summary["jira_id"],
                            "last_updated": last_updated,
                            "elapsed_days": round(elapsed_days, 2),
                            "threshold_days": threshold
                        }
                    )
                )

        return violations
