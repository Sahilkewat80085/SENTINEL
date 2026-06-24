import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.celery_app import celery_app
from app.core.database import get_db_context
from app.core.logging import logger
from app.repositories.report_repo import report_repo
from app.services.reporting.excel_builder import ExcelReportBuilder
from app.services.reporting.pdf_builder import PDFReportBuilder


@celery_app.task(name="tasks.generate_excel_report")
def generate_excel_report_task(repository_id: str, config: dict[str, Any] = None) -> dict[str, Any]:
    """Celery task to generate an Excel report in the background."""
    logger.info("Executing background Excel report generation task", repo_id=repository_id)

    async def _run() -> dict[str, Any]:
        async with get_db_context() as db:
            repo_uuid = uuid.UUID(repository_id)
            builder = ExcelReportBuilder()

            # Create reports directory inside backend workspace
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)

            # Generate the report bytes
            excel_bytes = await builder.build(db, repo_uuid, config)

            # Write to a file
            filename = f"excel_report_{repository_id}_{int(datetime.now(timezone.utc).timestamp())}.xlsx"
            file_path = os.path.join(reports_dir, filename)
            with open(file_path, "wb") as f:
                f.write(excel_bytes)

            # Create database entry
            obj_in = {
                "repository_id": repo_uuid,
                "report_type": "EXCEL",
                "file_path": file_path,
                "file_size": len(excel_bytes),
                "config": config or {},
                "generated_by": "system",
                "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
            }
            db_report = await report_repo.create(db, obj_in=obj_in)
            await db.commit()

            logger.info("Excel report generated successfully", repo_id=repository_id, report_id=str(db_report.id))
            return {"report_id": str(db_report.id), "status": "success"}

    return asyncio.run(_run())


@celery_app.task(name="tasks.generate_pdf_report")
def generate_pdf_report_task(repository_id: str, config: dict[str, Any] = None) -> dict[str, Any]:
    """Celery task to generate a PDF report in the background."""
    logger.info("Executing background PDF report generation task", repo_id=repository_id)

    async def _run() -> dict[str, Any]:
        async with get_db_context() as db:
            repo_uuid = uuid.UUID(repository_id)
            builder = PDFReportBuilder()

            # Create reports directory inside backend workspace
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)

            # Generate the report bytes
            pdf_bytes = await builder.build(db, repo_uuid, config)

            # Write to a file
            filename = f"pdf_report_{repository_id}_{int(datetime.now(timezone.utc).timestamp())}.pdf"
            file_path = os.path.join(reports_dir, filename)
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

            # Create database entry
            obj_in = {
                "repository_id": repo_uuid,
                "report_type": "PDF",
                "file_path": file_path,
                "file_size": len(pdf_bytes),
                "config": config or {},
                "generated_by": "system",
                "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
            }
            db_report = await report_repo.create(db, obj_in=obj_in)
            await db.commit()

            logger.info("PDF report generated successfully", repo_id=repository_id, report_id=str(db_report.id))
            return {"report_id": str(db_report.id), "status": "success"}

    return asyncio.run(_run())
