from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import UserRole
from app.db.session import get_db
from app.models import Branch, User
from app.schemas import BranchCreate, BranchRead, Message


router = APIRouter(prefix="/branches", tags=["Branch Management"])
admin_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value)


def get_branch_or_404(db: Session, branch_id: int) -> Branch:
    branch = db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return branch


@router.post("", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> Branch:
    branch = Branch(**payload.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.get("", response_model=list[BranchRead])
def list_branches(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> list[Branch]:
    return list(db.scalars(select(Branch).order_by(Branch.name)).all())


@router.patch("/{branch_id}", response_model=BranchRead)
def update_branch(branch_id: int, payload: BranchCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> Branch:
    branch = get_branch_or_404(db, branch_id)
    for field, value in payload.model_dump().items():
        setattr(branch, field, value)
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{branch_id}", response_model=Message)
def delete_branch(branch_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN.value))) -> Message:
    branch = get_branch_or_404(db, branch_id)
    db.delete(branch)
    db.commit()
    return Message(message="Branch deleted")


@router.get("/{branch_id}/reports")
def branch_report(branch_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> dict:
    branch = get_branch_or_404(db, branch_id)
    return {"branch": branch.name, "city": branch.city, "status": "report-ready"}
