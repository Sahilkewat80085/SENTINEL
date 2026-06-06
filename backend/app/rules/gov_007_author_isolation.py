from typing import List
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo
from app.rules.registry import get_rules_config


class AuthorIsolationRule(GovernanceRule):
    """GOV-007: Flags Jiras with high commit counts from only one author (single point of failure)."""

    @property
    def rule_id(self) -> str:
        return "GOV-007"

    @property
    def name(self) -> str:
        return "Author isolation"

    @property
    def severity(self) -> str:
        return "MEDIUM"

    @property
    def category(self) -> str:
        return "PROPAGATION"

    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        violations = []
        config = get_rules_config().get(self.rule_id, {})
        threshold = config.get("threshold_commits", 10)

        for summary in context.jira_summaries:
            authors_count = summary.get("authors_count", 0)
            commits_count = summary.get("commits_count", 0)

            if authors_count == 1 and commits_count >= threshold:
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        jira_id=summary["jira_id"],
                        description=(
                            f"Jira {summary['jira_id']} has high contribution isolation: "
                            f"{commits_count} commits authored by a single developer."
                        ),
                        details={
                            "jira_id": summary["jira_id"],
                            "commits_count": commits_count,
                            "authors_count": authors_count,
                            "threshold_commits": threshold
                        }
                    )
                )

        return violations
