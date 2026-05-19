import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.models.user_preferences_model import UserPreferences


def get_preferences(session: Session, user_id: uuid.UUID) -> UserPreferences | None:
    return session.exec(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    ).first()


def get_or_create_preferences(
    session: Session, user_id: uuid.UUID
) -> UserPreferences:
    prefs = get_preferences(session, user_id)
    if prefs:
        return prefs

    now = datetime.utcnow()
    prefs = UserPreferences(
        user_id=user_id,
        theme="system",
        language="vi",
        updated_at=now,
    )
    session.add(prefs)
    session.commit()
    session.refresh(prefs)
    return prefs


def update_preferences(
    session: Session,
    user_id: uuid.UUID,
    theme: str | None = None,
    language: str | None = None,
) -> UserPreferences:
    prefs = get_or_create_preferences(session, user_id)

    if theme is not None:
        prefs.theme = theme
    if language is not None:
        prefs.language = language

    prefs.updated_at = datetime.utcnow()
    session.add(prefs)
    session.commit()
    session.refresh(prefs)
    return prefs
