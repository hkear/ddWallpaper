"""Feedback API — submit feedback, optionally from logged-in users."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.models import Feedback
from backend.schemas import FeedbackCreate, FeedbackOut
from backend.auth import get_current_user_optional
from backend.webhook import notify_admin

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackOut, status_code=201)
@router.post("/feedback/", response_model=FeedbackOut, status_code=201, include_in_schema=False)
async def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """Submit user feedback. Logged-in users have their user_id linked."""
    feedback = Feedback(
        name=payload.name,
        email=payload.email,
        message=payload.message,
        user_id=user.id if user else None,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    # Send webhook notification
    notify_admin(
        f"📬 新反馈\\n"
        f"来自：{feedback.name} ({feedback.email})\\n"
        f"{'用户ID：' + str(feedback.user_id) + '\\n' if feedback.user_id else ''}"
        f"内容：{feedback.message[:200]}{'...' if len(feedback.message) > 200 else ''}\\n"
        f"时间：{feedback.created_at.strftime('%Y-%m-%d %H:%M')}"
    )

    return feedback
