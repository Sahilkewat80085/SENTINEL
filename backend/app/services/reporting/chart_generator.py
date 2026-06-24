"""
Module 10: Reporting Engine - Chart Generator
Generates beautiful charts using matplotlib for reports.
"""
from __future__ import annotations

import io

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ReportChartGenerator:
    """Generates charts for governance reports."""

    def __init__(self):
        pass

    def generate_coverage_pie_chart(self, merged: int, partial: int, missing: int) -> bytes | None:
        """Generate a pie chart for Jira coverage statuses."""
        if not HAS_MATPLOTLIB:
            return None

        labels = []
        sizes = []
        colors = []

        if merged > 0:
            labels.append("Merged")
            sizes.append(merged)
            colors.append("#10B981")  # Emerald
        if partial > 0:
            labels.append("Partial")
            sizes.append(partial)
            colors.append("#F59E0B")  # Amber
        if missing > 0:
            labels.append("Missing")
            sizes.append(missing)
            colors.append("#F43F5E")  # Rose

        if not sizes:
            labels.append("No Data")
            sizes.append(1)
            colors.append("#475569")

        plt.figure(figsize=(6, 4), facecolor="#090D16")
        ax = plt.subplot(111)
        ax.set_facecolor("#090D16")

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            textprops=dict(color="#E2E8F0"),
        )

        for text in texts:
            text.set_color("#E2E8F0")
        for autotext in autotexts:
            autotext.set_color("#090D16")
            autotext.set_weight("bold")

        plt.title("Jira Coverage Status Breakdown", color="#FFFFFF", fontsize=14, weight="bold", pad=20)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, facecolor="#090D16")
        plt.close()
        buf.seek(0)
        return buf.read()

    def generate_health_trend_chart(self, dates: list[str], values: list[float]) -> bytes | None:
        """Generate a line chart for historical health trends."""
        if not HAS_MATPLOTLIB:
            return None

        plt.figure(figsize=(8, 4), facecolor="#090D16")
        ax = plt.subplot(111)
        ax.set_facecolor("#0D1526")

        ax.plot(dates, values, color="#3B82F6", marker="o", linewidth=2, markersize=6)
        ax.fill_between(dates, values, color="#3B82F6", alpha=0.15)

        ax.spines["bottom"].set_color("#1E293B")
        ax.spines["top"].set_color("#1E293B")
        ax.spines["left"].set_color("#1E293B")
        ax.spines["right"].set_color("#1E293B")

        ax.tick_params(colors="#94A3B8", labelsize=9)
        ax.grid(True, linestyle="--", alpha=0.1, color="#E2E8F0")

        plt.title("Governance Score / Health Trend", color="#FFFFFF", fontsize=14, weight="bold", pad=20)
        plt.ylabel("Score (%)", color="#94A3B8")
        plt.ylim(0, 105)

        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, facecolor="#090D16")
        plt.close()
        buf.seek(0)
        return buf.read()
