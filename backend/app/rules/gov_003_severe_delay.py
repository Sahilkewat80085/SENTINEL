from datetime import datetime, timezone

from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo
from app.rules.registry import get_rules_config


class SevereDelayRule(GovernanceRule):
    """GOV-003: Flags Jiras with merge propagation delays exceeding configured limits (default 30 days)."""

    @property
    def rule_id(self) -> str:
        return "GOV-003"

    @property
    def name(self) -> str:
        return "Severe delay"

    @property
    def severity(self) -> str:
        return "HIGH"

    @property
    def category(self) -> str:
        return "DELAY"

    def evaluate(self, context: RuleContext) -> list[RuleViolationInfo]:
        violations = []
        config = get_rules_config().get(self.rule_id, {})
        threshold = config.get("threshold_days", 30.0)
        now = datetime.now(timezone.utc)

        for d in context.delays:
            days = d.propagation_delay_days
            is_active_drift = False

            if days is None:
                # Still propagating/partial, calculate current elapsed time
                init_date = d.initial_commit_date
                if init_date.tzinfo is None:
                    init_date = init_date.replace(tzinfo=timezone.utc)
                days = (now - init_date).total_seconds() / 86400.0
                is_active_drift = True

            if days > threshold:
                status_text = "overdue propagation" if is_active_drift else "total merge delay"
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        jira_id=d.jira_id,
                        description=(
                            f"Jira {d.jira_id} has a severe {status_text} of "
                            f"{round(days, 2)} days, which exceeds the threshold of {threshold} days."
                        ),
                        details={
                            "jira_id": d.jira_id,
                            "propagation_delay_days": round(days, 2) if d.propagation_delay_days is not None else None,
                            "elapsed_days_current": round(days, 2),
                            "is_merged_complete": not is_active_drift,
                            "threshold_days": threshold
                        }
                    )
                )

        return violations
