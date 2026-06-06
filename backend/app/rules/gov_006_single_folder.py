from typing import List
from app.rules.base import GovernanceRule, RuleContext, RuleViolationInfo


class SingleFolderRule(GovernanceRule):
    """GOV-006: Flags Jiras that are only merged in vanilla and exactly one non-vanilla folder."""

    @property
    def rule_id(self) -> str:
        return "GOV-006"

    @property
    def name(self) -> str:
        return "Single folder"

    @property
    def severity(self) -> str:
        return "HIGH"

    @property
    def category(self) -> str:
        return "COVERAGE"

    def evaluate(self, context: RuleContext) -> List[RuleViolationInfo]:
        violations = []
        expected_folders = context.coverage_matrix.folders_list
        non_vanilla_expected = [f for f in expected_folders if f != "vanilla"]

        # If there's only one non-vanilla folder expected, merging to it is complete propagation
        if len(non_vanilla_expected) <= 1:
            return violations

        for row in context.coverage_matrix.rows:
            vanilla_merged = False
            merged_non_vanilla = []

            for f_detail in row.folders:
                if f_detail.folder_name == "vanilla":
                    if f_detail.is_merged:
                        vanilla_merged = True
                else:
                    if f_detail.is_merged:
                        merged_non_vanilla.append(f_detail.folder_name)

            if vanilla_merged and len(merged_non_vanilla) == 1:
                flagged_folder = merged_non_vanilla[0]
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        jira_id=row.jira_id,
                        description=(
                            f"Jira {row.jira_id} is only merged in 'vanilla' and folder '{flagged_folder}'. "
                            "It has not propagated to other expected environment folders."
                        ),
                        details={
                            "jira_id": row.jira_id,
                            "merged_folders": ["vanilla", flagged_folder],
                            "expected_folders": expected_folders
                        }
                    )
                )

        return violations
