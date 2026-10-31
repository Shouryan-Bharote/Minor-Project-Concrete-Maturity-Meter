"""MixProfile CRUD endpoints for concrete mix recipes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.mix_profile import MixProfile
from app.schemas.mix_profile import MixProfileCreate, MixProfileOut

router = APIRouter()


@router.get("", response_model=list[MixProfileOut], summary="List all mix profiles")
async def list_mix_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MixProfile).order_by(MixProfile.id))
    return result.scalars().all()


@router.post(
    "",
    response_model=MixProfileOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new concrete mix profile",
)
async def create_mix_profile(payload: MixProfileCreate, db: AsyncSession = Depends(get_db)):
    profile = MixProfile(**payload.model_dump())
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=MixProfileOut, summary="Get mix profile by ID")
async def get_mix_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile = await db.get(MixProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mix profile not found.")
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a mix profile")
async def delete_mix_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile = await db.get(MixProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mix profile not found.")
    await db.delete(profile)
    await db.flush()
