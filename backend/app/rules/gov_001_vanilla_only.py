from typing import List
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo


class VanillaOnlyRule(GovernanceRule):
    """GOV-001: Flags commits that reside only in the vanilla folder and haven't propagated."""

    @property
    def rule_id(self) -> str:
        return "GOV-001"

    @property
    def name(self) -> str:
        return "Vanilla-only commit"

    @property
    def severity(self) -> str:
        return "CRITICAL"

    @property
    def category(self) -> str:
        return "COVERAGE"

    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        violations = []
        expected_folders = context.coverage_matrix.folders_list
        
        # If there's only vanilla or no folders, propagation is not expected/possible
        if len(expected_folders) <= 1:
            return violations

        for row in context.coverage_matrix.rows:
            vanilla_merged = False
            others_merged = False
            
            for f_detail in row.folders:
                if f_detail.folder_name == "vanilla":
                    if f_detail.is_merged:
                        vanilla_merged = True
                else:
                    if f_detail.is_merged:
                        others_merged = True

            if vanilla_merged and not others_merged:
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        jira_id=row.jira_id,
                        description=(
                            f"Jira {row.jira_id} contains commits only in 'vanilla' and has "
                            "not propagated to other target environment folders."
                        ),
                        details={
                            "jira_id": row.jira_id,
                            "expected_folders": expected_folders,
                            "vanilla_merged": vanilla_merged,
                            "others_merged": others_merged
                        }
                    )
                )

        return violations
