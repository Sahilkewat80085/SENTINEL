"""
Module 10: Reporting Engine - PDF Builder
Generates an executive-ready PDF report using WeasyPrint with HTML/CSS templates.
Falls back to a detailed text manifest if WeasyPrint is unavailable.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from html import escape

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.services.governance_score import GovernanceScoreService
from app.services.folder_health import FolderHealthService
from app.services.folder_coverage import FolderCoverageService
from app.services.merge_delay import MergeDelayService
from app.services.exception_detection import ExceptionDetectionService

try:
    import weasyprint
    HAS_WEASYPRINT = True
except (ImportError, OSError) as e:
    HAS_WEASYPRINT = False
    logger.warning(f"WeasyPrint or its dependencies (e.g. GObject/Pango) are not available. PDF reports will fall back to HTML mode. Details: {e}")


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

GRADE_COLORS = {
    "A": "#10B981",
    "B": "#22C55E",
    "C": "#F59E0B",
    "D": "#F97316",
    "E": "#F43F5E",
    "F": "#F43F5E",
}

SEVERITY_COLORS = {
    "CRITICAL": ("#F43F5E", "#fff"),
    "HIGH": ("#F59E0B", "#0D1526"),
    "MEDIUM": ("#7C3AED", "#fff"),
    "LOW": ("#0EA5E9", "#fff"),
}

HEALTH_COLORS = {
    "EXCELLENT": "#10B981",
    "GOOD": "#22C55E",
    "WARNING": "#F59E0B",
    "POOR": "#F97316",
    "CRITICAL": "#F43F5E",
}


def _badge(text: str, bg: str, fg: str = "#fff") -> str:
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:4px;'
        f'font-size:10px;font-weight:700;letter-spacing:0.5px;">{escape(str(text))}</span>'
    )


def _severity_badge(sev: str) -> str:
    bg, fg = SEVERITY_COLORS.get(sev.upper(), ("#334155", "#fff"))
    return _badge(sev.upper(), bg, fg)


def _health_badge(cls: str) -> str:
    bg = HEALTH_COLORS.get(cls.upper(), "#334155")
    return _badge(cls, bg)


class PDFReportBuilder:
    """Builds an executive-ready PDF using WeasyPrint from a styled HTML template."""

    def __init__(self):
        self.governance_score_service = GovernanceScoreService()
        self.folder_health_service = FolderHealthService()
        self.coverage_service = FolderCoverageService()
        self.delay_service = MergeDelayService()
        self.violation_service = ExceptionDetectionService()

    async def build(
        self,
        db: AsyncSession,
        repository_id: uuid.UUID,
        config: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Generate the PDF and return raw bytes."""
        config = config or {}
        now = datetime.now(timezone.utc)

        html_content = await self._build_html(db, repository_id, now, config)

        if HAS_WEASYPRINT:
            doc = weasyprint.HTML(string=html_content)
            return doc.write_pdf()
        else:
            # Fallback: return HTML as bytes (browsers can print to PDF)
            logger.info("WeasyPrint unavailable – returning HTML fallback for PDF report")
            return html_content.encode("utf-8")

    async def _build_html(
        self,
        db: AsyncSession,
        repo_id: uuid.UUID,
        now: datetime,
        config: Dict[str, Any],
    ) -> str:
        """Assemble the full HTML string for the PDF report."""
        # ── Fetch all data ──────────────────────────────────────────────
        score_res = await self.governance_score_service.compute_repository_score(db, repo_id)
        score = score_res.value if score_res.is_success else None

        health_res = await self.folder_health_service.compute_all_health(db, repo_id)
        health_list = sorted(health_res.value or [], key=lambda x: x.health_score, reverse=True)

        coverage_res = await self.coverage_service.get_coverage_summary_data(db, repo_id)
        coverage = coverage_res.value if coverage_res.is_success else None

        delay_res = await self.delay_service.get_delay_statistics_data(db, repo_id)
        delays = delay_res.value if delay_res.is_success else None

        violations_res = await self.violation_service.get_violations(
            db, repository_id=repo_id, is_acknowledged=False
        )
        violations = violations_res.value if violations_res.is_success else []
        violations = violations[:20]  # Cap to top 20

        summary_res = await self.violation_service.get_violation_summary(db, repo_id)
        viol_summary = summary_res.value if summary_res.is_success else None

        # ── Build HTML sections ─────────────────────────────────────────
        score_html = self._build_score_section(score, now, str(repo_id))
        health_html = self._build_health_table(health_list)
        coverage_html = self._build_coverage_summary(coverage)
        delay_html = self._build_delay_table(delays)
        violations_html = self._build_violations_table(violations, viol_summary)

        return self._wrap_html(
            title=f"SENTINEL Governance Report",
            repo_id=str(repo_id),
            now=now,
            score_html=score_html,
            health_html=health_html,
            coverage_html=coverage_html,
            delay_html=delay_html,
            violations_html=violations_html,
        )

    def _build_score_section(self, score, now: datetime, repo_id: str) -> str:
        if not score:
            return "<p style='color:#64748b'>No governance score data available.</p>"

        grade_color = GRADE_COLORS.get(score.grade, "#64748B")
        return f"""
        <div class="score-section">
            <div class="score-circle" style="border-color:{grade_color}">
                <div class="score-number" style="color:{grade_color}">{score.score}</div>
                <div class="score-label">/ 100</div>
                <div class="score-grade" style="color:{grade_color}">{score.grade}</div>
            </div>
            <div class="score-details">
                <div class="score-metric">
                    <span class="metric-label">Folder Health Average</span>
                    <span class="metric-value">{score.folder_health_average:.1f}%</span>
                </div>
                <div class="score-metric">
                    <span class="metric-label">Violation Penalty</span>
                    <span class="metric-value" style="color:#F43F5E">-{score.violation_penalty:.1f} pts</span>
                </div>
                <div class="score-metric">
                    <span class="metric-label">Critical / High Violations</span>
                    <span class="metric-value">{score.active_critical_count} / {score.active_high_count}</span>
                </div>
                <div class="score-metric">
                    <span class="metric-label">Medium / Low Violations</span>
                    <span class="metric-value">{score.active_medium_count} / {score.active_low_count}</span>
                </div>
            </div>
        </div>
        """

    def _build_health_table(self, health_list) -> str:
        if not health_list:
            return "<p style='color:#64748b'>No folder health data available.</p>"

        rows = ""
        for idx, fh in enumerate(health_list, start=1):
            cls_badge = _health_badge(fh.classification)
            alt = "background:#0F1A2E" if idx % 2 == 0 else ""
            rows += f"""
            <tr style="{alt}">
                <td>{idx}</td>
                <td style="font-family:monospace">{escape(fh.folder_name)}</td>
                <td class="num">{fh.health_score:.1f}%</td>
                <td class="num">{fh.coverage_score:.1f}%</td>
                <td class="num">{fh.consistency_score:.1f}%</td>
                <td class="num">{fh.timeliness_score:.1f}%</td>
                <td>{cls_badge}</td>
            </tr>"""

        return f"""
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Folder</th>
                    <th>Health</th>
                    <th>Coverage</th>
                    <th>Consistency</th>
                    <th>Timeliness</th>
                    <th>Classification</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>"""

    def _build_coverage_summary(self, coverage) -> str:
        if not coverage:
            return "<p style='color:#64748b'>No coverage data available.</p>"

        pct = coverage.overall_coverage_pct
        bar_color = "#10B981" if pct >= 80 else "#F59E0B" if pct >= 50 else "#F43F5E"

        return f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-card-value">{coverage.total_jiras}</div>
                <div class="metric-card-label">Total Jiras</div>
            </div>
            <div class="metric-card" style="border-color:#10B981">
                <div class="metric-card-value" style="color:#10B981">{coverage.merged_count}</div>
                <div class="metric-card-label">Fully Merged</div>
            </div>
            <div class="metric-card" style="border-color:#F59E0B">
                <div class="metric-card-value" style="color:#F59E0B">{coverage.partial_count}</div>
                <div class="metric-card-label">Partial Coverage</div>
            </div>
            <div class="metric-card" style="border-color:#F43F5E">
                <div class="metric-card-value" style="color:#F43F5E">{coverage.missing_count}</div>
                <div class="metric-card-label">Missing Merges</div>
            </div>
        </div>
        <div class="progress-wrapper">
            <div class="progress-label">
                <span>Overall Coverage</span>
                <span style="font-weight:700;color:{bar_color}">{pct:.1f}%</span>
            </div>
            <div class="progress-track">
                <div class="progress-bar" style="width:{min(pct,100):.0f}%;background:{bar_color}"></div>
            </div>
        </div>"""

    def _build_delay_table(self, delays) -> str:
        if not delays or not delays.folder_rankings:
            return "<p style='color:#64748b'>No delay data available.</p>"

        rows = ""
        for idx, rank in enumerate(delays.folder_rankings, start=1):
            color = "#F43F5E" if rank.avg_delay_days > 14 else "#F59E0B" if rank.avg_delay_days > 7 else "#10B981"
            alt = "background:#0F1A2E" if idx % 2 == 0 else ""
            rows += f"""
            <tr style="{alt}">
                <td>{idx}</td>
                <td style="font-family:monospace">{escape(rank.folder_name)}</td>
                <td class="num" style="color:{color};font-weight:700">{rank.avg_delay_days:.1f}d</td>
                <td class="num">{rank.max_delay_days:.1f}d</td>
                <td class="num">{rank.p95_delay_days:.1f}d</td>
            </tr>"""

        header_stats = f"Overall Avg: {delays.overall_avg_delay_days:.1f} days | Max: {delays.overall_max_delay_days:.1f} days"
        return f"""
        <p style="color:#94A3B8;font-size:11px;margin-bottom:8px">{escape(header_stats)}</p>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Folder</th>
                    <th>Avg Delay</th>
                    <th>Max Delay</th>
                    <th>P95 Delay</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>"""

    def _build_violations_table(self, violations, summary) -> str:
        if not violations:
            return "<p style='color:#10B981;font-weight:600'>✓ No active unacknowledged violations.</p>"

        summary_line = ""
        if summary:
            summary_line = f"""<p style="color:#94A3B8;font-size:11px;margin-bottom:8px">
                Total: {summary.total_violations} | Critical: {summary.critical_count} |
                High: {summary.high_count} | Acknowledged: {summary.acknowledged_count}
            </p>"""

        rows = ""
        for idx, v in enumerate(violations, start=1):
            sev_badge = _severity_badge(v.severity)
            alt = "background:#0F1A2E" if idx % 2 == 0 else ""
            detected = (
                v.detected_at.strftime("%Y-%m-%d")
                if hasattr(v.detected_at, 'strftime') else str(v.detected_at)[:10]
            )
            rows += f"""
            <tr style="{alt}">
                <td style="font-family:monospace;font-size:10px">{escape(v.rule_id)}</td>
                <td>{sev_badge}</td>
                <td style="font-size:10px;color:#94A3B8">{escape(v.category)}</td>
                <td style="font-family:monospace;font-size:10px">{escape(v.jira_id or '—')}</td>
                <td style="font-size:10px">{escape(v.description[:80])}{'…' if len(v.description) > 80 else ''}</td>
                <td style="font-size:10px;color:#64748B">{detected}</td>
            </tr>"""

        return f"""
        {summary_line}
        <table>
            <thead>
                <tr>
                    <th>Rule ID</th>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>Jira</th>
                    <th>Description</th>
                    <th>Detected</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>"""

    def _wrap_html(
        self,
        title: str,
        repo_id: str,
        now: datetime,
        score_html: str,
        health_html: str,
        coverage_html: str,
        delay_html: str,
        violations_html: str,
    ) -> str:
        generated = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        css = self._get_css()
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <style>{css}</style>
</head>
<body>
    <!-- Cover Header -->
    <div class="header">
        <div class="header-content">
            <div class="logo">🛡 SENTINEL</div>
            <div class="header-right">
                <div class="report-title">Governance & Release Readiness Report</div>
                <div class="report-meta">Repository: {escape(repo_id)} &nbsp;|&nbsp; Generated: {escape(generated)}</div>
            </div>
        </div>
    </div>

    <!-- Governance Score -->
    <div class="section">
        <h2 class="section-title">📊 Governance Score</h2>
        {score_html}
    </div>

    <!-- Folder Health -->
    <div class="section page-break-before">
        <h2 class="section-title">🏥 Folder Health Rankings</h2>
        {health_html}
    </div>

    <!-- Coverage Summary -->
    <div class="section">
        <h2 class="section-title">📋 Jira Coverage Summary</h2>
        {coverage_html}
    </div>

    <!-- Merge Delay Analysis -->
    <div class="section page-break-before">
        <h2 class="section-title">⏱ Merge Delay Analysis</h2>
        {delay_html}
    </div>

    <!-- Violations -->
    <div class="section">
        <h2 class="section-title">⚠️ Active Governance Violations</h2>
        {violations_html}
    </div>

    <!-- Footer -->
    <div class="footer">
        <div>SENTINEL Governance Platform — Confidential &amp; Proprietary</div>
        <div>{escape(generated)}</div>
    </div>
</body>
</html>"""

    def _get_css(self) -> str:
        return """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #090D16;
            color: #E2E8F0;
            font-size: 12px;
            line-height: 1.5;
        }

        .header {
            background: linear-gradient(135deg, #0D1526 0%, #1E3A8A 100%);
            padding: 24px 32px;
            border-bottom: 2px solid #3B82F6;
        }
        .header-content { display: flex; align-items: center; justify-content: space-between; }
        .logo { font-size: 22px; font-weight: 800; color: #fff; letter-spacing: 1px; }
        .report-title { font-size: 16px; font-weight: 700; color: #fff; text-align: right; }
        .report-meta { font-size: 10px; color: #94A3B8; text-align: right; margin-top: 4px; }

        .section {
            padding: 24px 32px 16px;
            border-bottom: 1px solid #1E293B;
        }
        .section-title {
            font-size: 14px; font-weight: 700; color: #fff;
            margin-bottom: 16px; letter-spacing: 0.3px;
            padding-bottom: 8px; border-bottom: 1px solid #1E293B;
        }
        .page-break-before { page-break-before: always; }

        /* Score Section */
        .score-section { display: flex; align-items: flex-start; gap: 32px; }
        .score-circle {
            width: 120px; height: 120px; flex-shrink: 0;
            border-radius: 50%; border: 4px solid #3B82F6;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            background: rgba(59,130,246,0.08);
        }
        .score-number { font-size: 32px; font-weight: 800; line-height: 1; }
        .score-label { font-size: 10px; color: #64748B; }
        .score-grade { font-size: 20px; font-weight: 800; margin-top: 4px; }
        .score-details { flex: 1; display: flex; flex-wrap: wrap; gap: 12px; }
        .score-metric {
            background: #0F1A2E; border: 1px solid #1E3A5F;
            border-radius: 8px; padding: 10px 14px;
            min-width: 180px;
        }
        .metric-label { display: block; font-size: 10px; color: #64748B; font-weight: 600; text-transform: uppercase; }
        .metric-value { display: block; font-size: 18px; font-weight: 700; color: #F1F5F9; margin-top: 4px; }

        /* Tables */
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th {
            background: #1E3A8A; color: #fff;
            padding: 8px 10px; text-align: left;
            font-size: 10px; font-weight: 700; letter-spacing: 0.4px; text-transform: uppercase;
        }
        td { padding: 7px 10px; border-bottom: 1px solid #0F1A2E; color: #CBD5E1; }
        .num { text-align: right; font-family: monospace; font-weight: 600; }
        tr:hover td { background: #0F1A2E; }

        /* Metric Cards */
        .metric-grid { display: flex; gap: 12px; margin-bottom: 16px; }
        .metric-card {
            flex: 1; background: #0F1A2E; border: 1px solid #1E3A5F;
            border-radius: 10px; padding: 14px;
            text-align: center;
        }
        .metric-card-value { font-size: 28px; font-weight: 800; color: #F1F5F9; }
        .metric-card-label { font-size: 10px; color: #64748B; font-weight: 600; margin-top: 4px; }

        /* Progress bar */
        .progress-wrapper { margin-top: 8px; }
        .progress-label {
            display: flex; justify-content: space-between;
            font-size: 11px; color: #94A3B8; margin-bottom: 6px; font-weight: 600;
        }
        .progress-track { height: 10px; background: #1E293B; border-radius: 999px; overflow: hidden; }
        .progress-bar { height: 100%; border-radius: 999px; transition: width 0.3s ease; }

        /* Footer */
        .footer {
            display: flex; justify-content: space-between;
            padding: 16px 32px; background: #0D1526;
            font-size: 10px; color: #475569;
            border-top: 1px solid #1E293B;
        }
        """
