
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

    def evaluate(self, context: RuleContext) -> list[RuleViolationInfo]:
        violations = []
        expected_folders = context.coverage_matrix.folders_list
        if not expected_folders:
            return violations
        initial_folder = expected_folders[0]
        non_initial_expected = [f for f in expected_folders if f != initial_folder]

        # If there's only one non-initial folder expected, merging to it is complete propagation
        if len(non_initial_expected) <= 1:
            return violations

        for row in context.coverage_matrix.rows:
            initial_merged = False
            merged_non_initial = []

            for f_detail in row.folders:
                if f_detail.folder_name == initial_folder:
                    if f_detail.is_merged:
                        initial_merged = True
                else:
                    if f_detail.is_merged:
                        merged_non_initial.append(f_detail.folder_name)

            if initial_merged and len(merged_non_initial) == 1:
                flagged_folder = merged_non_initial[0]
                violations.append(
                    RuleViolationInfo(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        category=self.category,
                        jira_id=row.jira_id,
                        description=(
                            f"Jira {row.jira_id} is only merged in '{initial_folder}' and folder '{flagged_folder}'. "
                            "It has not propagated to other expected environment folders."
                        ),
                        details={
                            "jira_id": row.jira_id,
                            "merged_folders": [initial_folder, flagged_folder],
                            "expected_folders": expected_folders
                        }
                    )
                )

        return violations
