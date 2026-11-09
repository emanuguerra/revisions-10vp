from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Profile


def current_profile(x_profile_token: str = Header(default=""), db: Session = Depends(get_db)) -> Profile:
    """Students are identified by the token returned when their profile is created (no password)."""
    profile = db.scalar(select(Profile).where(Profile.token == x_profile_token)) if x_profile_token else None
    if profile is None:
        raise HTTPException(401, "Profil inconnu : crée un profil ou entre ton code de reprise.")
    return profile
