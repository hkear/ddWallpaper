from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Category
from backend.schemas import CategoryOut, CategoriesList

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("/", response_model=CategoriesList)
def list_categories(
    db: Session = Depends(get_db),
):
    cats = db.query(Category).order_by(Category.sort).all()
    return CategoriesList(items=[CategoryOut.model_validate(c) for c in cats])
