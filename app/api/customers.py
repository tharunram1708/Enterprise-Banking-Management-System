from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.constants import CustomerStatus, UserRole
from app.db.session import get_db
from app.models import Address, Customer, CustomerDocument, Nominee, User
from app.schemas import (
    AddressCreate,
    AddressRead,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    DocumentCreate,
    DocumentRead,
    Message,
    NomineeCreate,
    NomineeRead,
)


router = APIRouter(prefix="/customers", tags=["Customer Management"])
staff_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.EMPLOYEE.value)


def get_customer_or_404(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    current_user: User = Depends(require_roles(*staff_roles)),
    db: Session = Depends(get_db),
) -> Customer:
    customer = Customer(**payload.model_dump(), created_by_user_id=current_user.id)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=list[CustomerRead])
def list_customers(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> list[Customer]:
    query = select(Customer).order_by(Customer.id.desc())
    if search:
        like = f"%{search}%"
        query = query.where(
            or_(
                Customer.first_name.like(like),
                Customer.last_name.like(like),
                Customer.email.like(like),
                Customer.phone.like(like),
            )
        )
    return list(db.scalars(query).all())


@router.get("/{customer_id}", response_model=CustomerRead)
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Customer:
    return get_customer_or_404(db, customer_id)


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> Customer:
    customer = get_customer_or_404(db, customer_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", response_model=Message)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.MANAGER.value)),
) -> Message:
    customer = get_customer_or_404(db, customer_id)
    db.delete(customer)
    db.commit()
    return Message(message="Customer deleted")


@router.post("/{customer_id}/verify", response_model=CustomerRead)
def verify_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.MANAGER.value)),
) -> Customer:
    customer = get_customer_or_404(db, customer_id)
    customer.status = CustomerStatus.VERIFIED.value
    customer.kyc_status = "verified"
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/{customer_id}/addresses", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def add_address(
    customer_id: int,
    payload: AddressCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> Address:
    get_customer_or_404(db, customer_id)
    address = Address(customer_id=customer_id, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.post("/{customer_id}/nominees", response_model=NomineeRead, status_code=status.HTTP_201_CREATED)
def add_nominee(
    customer_id: int,
    payload: NomineeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> Nominee:
    get_customer_or_404(db, customer_id)
    nominee = Nominee(customer_id=customer_id, **payload.model_dump())
    db.add(nominee)
    db.commit()
    db.refresh(nominee)
    return nominee


@router.post("/{customer_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def add_document(
    customer_id: int,
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> CustomerDocument:
    get_customer_or_404(db, customer_id)
    document = CustomerDocument(customer_id=customer_id, **payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/{customer_id}/documents/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    customer_id: int,
    document_type: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*staff_roles)),
) -> CustomerDocument:
    get_customer_or_404(db, customer_id)
    upload_dir = Path("uploads") / "customer_documents" / str(customer_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "document.bin").name
    saved_path = upload_dir / safe_name
    with saved_path.open("wb") as target:
        target.write(file.file.read())

    document = CustomerDocument(
        customer_id=customer_id,
        document_type=document_type,
        file_name=safe_name,
        file_path=str(saved_path),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
