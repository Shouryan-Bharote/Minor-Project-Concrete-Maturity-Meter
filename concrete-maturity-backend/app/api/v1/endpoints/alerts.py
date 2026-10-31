"""Alerts endpoints: query unresolved alerts and resolve them."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertOut, AlertResolve

router = APIRouter()


@router.get("", response_model=list[AlertOut], summary="List unresolved alerts")
async def list_alerts(
    sensor_id: int | None = None,
    severity: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Alert).where(Alert.is_resolved == False).order_by(Alert.created_at.desc())  # noqa: E712
    if sensor_id is not None:
        query = query.where(Alert.sensor_id == sensor_id)
    if severity is not None:
        query = query.where(Alert.severity == severity)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{alert_id}", response_model=AlertOut, summary="Acknowledge or resolve an alert")
async def resolve_alert(
    alert_id: int,
    payload: AlertResolve,
    db: AsyncSession = Depends(get_db),
):
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    alert.is_resolved = payload.is_resolved
    await db.flush()
    await db.refresh(alert)
    return alert
