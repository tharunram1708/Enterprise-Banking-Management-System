from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import CardStatus, UserRole
from app.core.security import generate_card_last_four, hash_password
from app.db.session import get_db
from app.models import Account, Card, Customer, User
from app.schemas import CardCreate, CardLimitUpdate, CardRead, Message, PinCreate


router = APIRouter(prefix="/cards", tags=["Card Management"])
staff_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.EMPLOYEE.value)


def get_card_or_404(db: Session, card_id: int) -> Card:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def create_card(payload: CardCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Card:
    if not db.get(Account, payload.account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    card = Card(
        account_id=payload.account_id,
        customer_id=payload.customer_id,
        card_type=payload.card_type.value,
        last_four=generate_card_last_four(),
        daily_limit=payload.daily_limit,
        monthly_limit=payload.monthly_limit,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.get("", response_model=list[CardRead])
def list_cards(db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> list[Card]:
    return list(db.scalars(select(Card).order_by(Card.id.desc())).all())


@router.post("/{card_id}/block", response_model=CardRead)
def block_card(card_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Card:
    card = get_card_or_404(db, card_id)
    card.status = CardStatus.BLOCKED.value
    db.commit()
    db.refresh(card)
    return card


@router.post("/{card_id}/pin", response_model=Message)
def generate_pin(card_id: int, payload: PinCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Message:
    card = get_card_or_404(db, card_id)
    card.pin_hash = hash_password(payload.pin)
    db.commit()
    return Message(message="PIN updated")


@router.patch("/{card_id}/limits", response_model=CardRead)
def update_limits(card_id: int, payload: CardLimitUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(*staff_roles))) -> Card:
    card = get_card_or_404(db, card_id)
    if payload.daily_limit is not None:
        card.daily_limit = payload.daily_limit
    if payload.monthly_limit is not None:
        card.monthly_limit = payload.monthly_limit
    db.commit()
    db.refresh(card)
    return card
