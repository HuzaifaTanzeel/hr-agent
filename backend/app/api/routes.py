"""
FastAPI Routes - REST API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.api.schemas import (
    LeaveRequestCreate, LeaveRequestResponse, LeaveRequestDetail,
    LeaveBalanceResponse, LeaveApprovalCreate, LeaveApprovalResponse,
    SuccessResponse, ErrorResponse
)
from app.services.leave_service import LeaveService, LeaveServiceException
from app.db.repositories.leave_repository import (
    LeaveRequestRepository, LeaveBalanceRepository, LeaveTypeRepository,
    EmployeeRepository
)

router = APIRouter()


# ============================================================================
# LEAVE REQUEST ENDPOINTS
# ============================================================================

@router.post(
    "/leave-requests",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for leave"
)
async def create_leave_request(
    request: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply for leave
    
    - **employee_id**: Employee ID
    - **leave_type**: ANNUAL, SICK, CASUAL, or UNPAID
    - **start_date**: Leave start date (YYYY-MM-DD)
    - **end_date**: Leave end date (YYYY-MM-DD)
    - **reason**: Reason for leave (min 10 chars)
    """
    try:
        result = await LeaveService.apply_leave(
            db=db,
            employee_id=request.employee_id,
            leave_type_code=request.leave_type.value,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason
        )
        
        return SuccessResponse(
            success=True,
            message="Leave request submitted successfully",
            data=result
        )
    
    except LeaveServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )


@router.get(
    "/leave-requests",
    response_model=List[dict],
    summary="Get all leave requests (HR view)"
)
async def get_all_leave_requests(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all leave requests across all employees (for HR portal)"""
    try:
        # Get all employees first
        employees = await EmployeeRepository.get_all(db, skip=0, limit=1000)
        
        # Get leave requests for all employees
        all_requests = []
        for employee in employees:
            requests = await LeaveService.get_leave_requests(
                db=db,
                employee_id=employee.id,
                skip=0,
                limit=1000
            )
            # Add employee_id to each request for HR view
            for req in requests:
                req['employee_id'] = employee.id
            all_requests.extend(requests)
        
        # Sort by created_at descending
        all_requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return all_requests[skip:skip+limit]
    
    except LeaveServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/leave-requests/{request_id}",
    response_model=LeaveRequestResponse,
    summary="Get leave request details"
)
async def get_leave_request(
    request_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific leave request"""
    leave_request = await LeaveRequestRepository.get_by_id(db, request_id)
    
    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave request {request_id} not found"
        )
    
    return leave_request


@router.get(
    "/employees/{employee_id}/leave-requests",
    response_model=List[dict],
    summary="Get all leave requests for employee"
)
async def get_employee_leave_requests(
    employee_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all leave requests for a specific employee"""
    try:
        requests = await LeaveService.get_leave_requests(
            db=db,
            employee_id=employee_id,
            skip=skip,
            limit=limit
        )
        return requests
    
    except LeaveServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    "/leave-requests/{request_id}/cancel",
    response_model=SuccessResponse,
    summary="Cancel leave request"
)
async def cancel_leave_request(
    request_id: int,
    employee_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a pending leave request
    
    - Only PENDING requests can be cancelled
    - Employee can only cancel their own requests
    """
    try:
        result = await LeaveService.cancel_leave(
            db=db,
            request_id=request_id,
            employee_id=employee_id
        )
        
        return SuccessResponse(
            success=True,
            message=result["message"],
            data=result
        )
    
    except LeaveServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# LEAVE BALANCE ENDPOINTS
# ============================================================================

@router.get(
    "/employees/{employee_id}/leave-balance",
    response_model=dict,
    summary="Get leave balance"
)
async def get_leave_balance(
    employee_id: int,
    leave_type: str = None,
    year: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get leave balance for employee
    
    - **employee_id**: Employee ID
    - **leave_type**: Optional - specific leave type (ANNUAL, SICK, etc.)
    - **year**: Optional - defaults to current year
    """
    try:
        balance = await LeaveService.get_leave_balance(
            db=db,
            employee_id=employee_id,
            leave_type_code=leave_type,
            year=year
        )
        return balance
    
    except LeaveServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/leave-types",
    response_model=List[dict],
    summary="Get all leave types"
)
async def get_leave_types(db: AsyncSession = Depends(get_db)):
    """Get all available leave types"""
    leave_types = await LeaveTypeRepository.get_all(db)
    
    return [
        {
            "id": lt.id,
            "code": lt.code,
            "name": lt.name,
            "max_days_per_year": lt.max_days_per_year,
            "requires_approval": lt.requires_approval
        }
        for lt in leave_types
    ]


# ============================================================================
# LEAVE APPROVAL ENDPOINTS
# ============================================================================

@router.post(
    "/leave-requests/{request_id}/approve",
    response_model=SuccessResponse,
    summary="Approve or reject leave request"
)
async def approve_leave_request(
    request_id: int,
    approval: LeaveApprovalCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a leave request
    
    - **action**: APPROVED or REJECTED
    - **comment**: Optional comment
    
    Only managers or HR can approve requests
    """
    try:
        result = await LeaveService.approve_leave(
            db=db,
            request_id=request_id,
            approver_person_id=approval.approver_person_id,
            action=approval.action.value,
            comment=approval.comment
        )
        
        return SuccessResponse(
            success=True,
            message=result["message"],
            data=result
        )
    
    except LeaveServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", summary="Health check")
async def health_check():
    """Check if API is running"""
    return {
        "status": "healthy",
        "message": "HR AI Agent API is running"
    }