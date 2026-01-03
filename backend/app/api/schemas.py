"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class LeaveTypeEnum(str, Enum):
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    CASUAL = "CASUAL"
    UNPAID = "UNPAID"


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ApprovalAction(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ============================================================================
# PERSON & EMPLOYEE SCHEMAS
# ============================================================================

class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)


class PersonCreate(PersonBase):
    pass


class PersonResponse(PersonBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    person_id: int
    employee_code: str = Field(..., min_length=1, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=100)
    joining_date: date
    manager_id: Optional[int] = None


class EmployeeResponse(BaseModel):
    id: int
    person_id: int
    employee_code: str
    department: Optional[str]
    designation: Optional[str]
    joining_date: date
    manager_id: Optional[int]
    
    class Config:
        from_attributes = True


class EmployeeDetail(EmployeeResponse):
    """Employee with person details"""
    person: PersonResponse


# ============================================================================
# LEAVE REQUEST SCHEMAS
# ============================================================================

class LeaveRequestCreate(BaseModel):
    employee_id: int = Field(..., gt=0)
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=10, max_length=500)
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after or equal to start_date')
        return v


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    total_days: int
    reason: str
    status: LeaveStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeaveRequestDetail(LeaveRequestResponse):
    """Leave request with related data"""
    employee_name: str
    leave_type_name: str
    manager_name: Optional[str] = None


# ============================================================================
# LEAVE BALANCE SCHEMAS
# ============================================================================

class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    leave_type_name: str
    year: int
    total_allocated: int
    used: int
    remaining: int
    
    class Config:
        from_attributes = True


class LeaveBalanceCreate(BaseModel):
    employee_id: int
    leave_type_id: int
    year: int = Field(..., ge=2020, le=2030)
    total_allocated: int = Field(..., ge=0)


# ============================================================================
# LEAVE APPROVAL SCHEMAS
# ============================================================================

class LeaveApprovalCreate(BaseModel):
    leave_request_id: int
    approver_person_id: int
    action: ApprovalAction
    comment: Optional[str] = Field(None, max_length=500)


class LeaveApprovalResponse(BaseModel):
    id: int
    leave_request_id: int
    approver_person_id: int
    action: Optional[str]
    comment: Optional[str]
    action_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# GENERIC RESPONSE SCHEMAS
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[dict] = None


# ============================================================================
# PAGINATION
# ============================================================================

class PaginatedResponse(BaseModel):
    """Paginated list response"""
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int