import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import logger
from app.models.user import User
from app.repositories.report_repo import report_repo
from app.schemas.common import ResponseEnvelope
from app.schemas.report import ReportResponse
from app.services.reporting.excel_builder import ExcelReportBuilder
from app.services.reporting.pdf_builder import PDFReportBuilder
from pydantic import BaseModel

router = APIRouter()


class ReportGenerateRequest(BaseModel):
    repository_id: uuid.UUID
    config: Dict[str, Any] = {}


@router.post("/excel", response_model=ResponseEnvelope[Dict[str, Any]])
async def generate_excel_report(
    body: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger generation of an Excel report."""
    logger.info("Generating Excel report synchronously", repo_id=str(body.repository_id))
    builder = ExcelReportBuilder()

    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    try:
        excel_bytes = await builder.build(db, body.repository_id, body.config)

        filename = f"excel_report_{body.repository_id}_{int(datetime.now(timezone.utc).timestamp())}.xlsx"
        file_path = os.path.join(reports_dir, filename)

        with open(file_path, "wb") as f:
            f.write(excel_bytes)

        obj_in = {
            "repository_id": body.repository_id,
            "report_type": "EXCEL",
            "file_path": file_path,
            "file_size": len(excel_bytes),
            "config": body.config or {},
            "generated_by": current_user.username,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        }
        db_report = await report_repo.create(db, obj_in=obj_in)
        await db.commit()

        return ResponseEnvelope(
            success=True,
            data={
                "report_id": str(db_report.id),
                "message": "Excel report generated successfully",
            },
        )
    except Exception as e:
        logger.exception("Failed to generate Excel report", error=str(e))
        return ResponseEnvelope(
            success=False,
            errors=[{"code": "GENERATE_FAILED", "message": str(e)}],
        )


@router.post("/pdf", response_model=ResponseEnvelope[Dict[str, Any]])
async def generate_pdf_report(
    body: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger generation of a PDF report."""
    logger.info("Generating PDF report synchronously", repo_id=str(body.repository_id))
    builder = PDFReportBuilder()

    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    try:
        pdf_bytes = await builder.build(db, body.repository_id, body.config)

        filename = f"pdf_report_{body.repository_id}_{int(datetime.now(timezone.utc).timestamp())}.pdf"
        file_path = os.path.join(reports_dir, filename)

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        obj_in = {
            "repository_id": body.repository_id,
            "report_type": "PDF",
            "file_path": file_path,
            "file_size": len(pdf_bytes),
            "config": body.config or {},
            "generated_by": current_user.username,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        }
        db_report = await report_repo.create(db, obj_in=obj_in)
        await db.commit()

        return ResponseEnvelope(
            success=True,
            data={
                "report_id": str(db_report.id),
                "message": "PDF report generated successfully",
            },
        )
    except Exception as e:
        logger.exception("Failed to generate PDF report", error=str(e))
        return ResponseEnvelope(
            success=False,
            errors=[{"code": "GENERATE_FAILED", "message": str(e)}],
        )


@router.get("", response_model=ResponseEnvelope[List[ReportResponse]])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch all reports, ordered by generation date desc."""
    reports = await report_repo.get_multi(db, limit=100)
    reports = sorted(reports, key=lambda x: x.generated_at, reverse=True)
    return ResponseEnvelope(success=True, data=reports)


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Download a generated report file."""
    db_report = await report_repo.get(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not os.path.exists(db_report.file_path):
        logger.error("Report file missing on disk", file_path=db_report.file_path)
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    filename = os.path.basename(db_report.file_path)
    media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if db_report.report_type.upper() == "EXCEL"
        else "application/pdf"
    )

    return FileResponse(
        path=db_report.file_path, filename=filename, media_type=media_type
    )
