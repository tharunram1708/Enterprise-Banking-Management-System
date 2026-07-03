from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.constants import UserRole
from app.db.session import get_db
from app.models import Attendance, Branch, Employee, LeaveRequest, Payroll, User
from app.schemas import AttendanceCreate, EmployeeCreate, EmployeeRead, LeaveCreate, Message, PayrollCreate


router = APIRouter(prefix="/employees", tags=["Employee Management"])
admin_roles = (UserRole.ADMIN.value, UserRole.MANAGER.value)


def get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> Employee:
    if not db.get(Branch, payload.branch_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("", response_model=list[EmployeeRead])
def list_employees(db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> list[Employee]:
    return list(db.scalars(select(Employee).order_by(Employee.id.desc())).all())


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, payload: EmployeeCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> Employee:
    employee = get_employee_or_404(db, employee_id)
    for field, value in payload.model_dump().items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}", response_model=Message)
def delete_employee(employee_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN.value))) -> Message:
    employee = get_employee_or_404(db, employee_id)
    employee.is_active = False
    db.commit()
    return Message(message="Employee deactivated")


@router.post("/attendance", response_model=Message)
def mark_attendance(payload: AttendanceCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> Message:
    get_employee_or_404(db, payload.employee_id)
    db.add(Attendance(**payload.model_dump()))
    db.commit()
    return Message(message="Attendance marked")


@router.post("/leaves", response_model=Message)
def request_leave(payload: LeaveCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(*admin_roles))) -> Message:
    get_employee_or_404(db, payload.employee_id)
    db.add(LeaveRequest(**payload.model_dump()))
    db.commit()
    return Message(message="Leave request recorded")


@router.post("/payroll", response_model=Message)
def create_payroll(payload: PayrollCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN.value))) -> Message:
    get_employee_or_404(db, payload.employee_id)
    net_pay = payload.gross_pay - payload.deductions
    db.add(Payroll(**payload.model_dump(), net_pay=net_pay))
    db.commit()
    return Message(message="Payroll generated")
