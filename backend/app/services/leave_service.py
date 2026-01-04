"""
Leave Service - Business Logic Layer

All business rules and validation happen here.
Services orchestrate repositories but don't access DB directly.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta, datetime
from typing import Dict, Optional, List

from app.db.repositories.leave_repository import (
    LeaveRequestRepository,
    LeaveBalanceRepository,
    EmployeeRepository,
    LeaveTypeRepository,
    LeaveApprovalRepository
)


class LeaveServiceException(Exception):
    """Base exception for leave service"""
    pass


class LeaveService:
    """Service for leave management operations"""

    @staticmethod
    def _calculate_working_days(start_date: date, end_date: date) -> int:
        """
        Calculate working days between dates (exclude weekends).
        In production, this would also exclude public holidays.
        """
        working_days = 0
        current = start_date

        while current <= end_date:
            if current.weekday() < 5:  # Monday=0, Friday=4
                working_days += 1
            current += timedelta(days=1)

        return working_days

    @staticmethod
    async def apply_leave(
            db: AsyncSession,
            employee_id: int,
            leave_type_code: str,
            start_date: date,
            end_date: date,
            reason: str
    ) -> Dict:
        """
        Apply for leave with complete validation

        Business Rules:
        1. Employee must exist
        2. Valid date range
        3. Sufficient balance
        4. No conflicts
        5. Calculate working days
        """

        # 1. Validate employee exists
        employee = await EmployeeRepository.get_by_id(db, employee_id)
        if not employee:
            raise LeaveServiceException(f"Employee {employee_id} not found")

        # 2. Get leave type
        leave_type = await LeaveTypeRepository.get_by_code(db, leave_type_code)
        if not leave_type:
            raise LeaveServiceException(f"Invalid leave type: {leave_type_code}")

        # 3. Validate dates
        if start_date < date.today():
            raise LeaveServiceException("Cannot apply for past dates")

        if end_date < start_date:
            raise LeaveServiceException("End date must be after start date")

        # 4. Calculate working days
        working_days = LeaveService._calculate_working_days(start_date, end_date)
        if working_days < 1:
            raise LeaveServiceException("Must request at least 1 working day")

        # 5. Check leave balance
        year = start_date.year
        balance = await LeaveBalanceRepository.get_balance(
            db, employee_id, leave_type.id, year
        )

        if not balance:
            raise LeaveServiceException(
                f"No leave balance found for {leave_type_code} in {year}"
            )

        if balance.remaining < working_days:
            raise LeaveServiceException(
                f"Insufficient balance. Requested: {working_days}, "
                f"Available: {balance.remaining}"
            )

        # 6. Check for conflicts
        conflicts = await LeaveRequestRepository.check_conflicts(
            db, employee_id, start_date, end_date
        )

        if conflicts:
            raise LeaveServiceException(
                f"Leave dates conflict with existing request (ID: {conflicts[0].id})"
            )

        # 7. Create leave request
        leave_request = await LeaveRequestRepository.create(db, {
            "employee_id": employee_id,
            "leave_type_id": leave_type.id,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": working_days,
            "reason": reason,
            "status": "PENDING"
        })

        return {
            "id": leave_request.id,
            "status": leave_request.status,
            "total_days": working_days,
            "remaining_balance": balance.remaining - working_days
        }

    @staticmethod
    async def get_leave_balance(
            db: AsyncSession,
            employee_id: int,
            leave_type_code: Optional[str] = None,
            year: Optional[int] = None
    ) -> Dict:
        """Get leave balance for employee"""

        # Validate employee
        employee = await EmployeeRepository.get_by_id(db, employee_id)
        if not employee:
            raise LeaveServiceException(f"Employee {employee_id} not found")

        year = year or datetime.now().year

        if leave_type_code:
            # Get specific leave type balance
            leave_type = await LeaveTypeRepository.get_by_code(db, leave_type_code)
            if not leave_type:
                raise LeaveServiceException(f"Invalid leave type: {leave_type_code}")

            balance = await LeaveBalanceRepository.get_balance(
                db, employee_id, leave_type.id, year
            )

            if not balance:
                raise LeaveServiceException(
                    f"No balance found for {leave_type_code} in {year}"
                )

            return {
                "leave_type": leave_type.code,
                "leave_type_name": leave_type.name,
                "year": year,
                "total_allocated": balance.total_allocated,
                "used": balance.used,
                "remaining": balance.remaining
            }
        else:
            # Get all balances
            balances = await LeaveBalanceRepository.get_all_balances(
                db, employee_id, year
            )

            return {
                "year": year,
                "balances": [
                    {
                        "leave_type": b.leave_type.code,
                        "leave_type_name": b.leave_type.name,
                        "total_allocated": b.total_allocated,
                        "used": b.used,
                        "remaining": b.remaining
                    }
                    for b in balances
                ]
            }

    @staticmethod
    async def approve_leave(
            db: AsyncSession,
            request_id: int,
            approver_person_id: int,
            action: str,
            comment: Optional[str] = None
    ) -> Dict:
        """
        Approve or reject leave request

        Business Rules:
        1. Request must exist and be PENDING
        2. If approved, deduct from balance
        3. Create approval record
        4. Update request status
        """

        # 1. Get leave request
        leave_request = await LeaveRequestRepository.get_by_id(db, request_id)
        if not leave_request:
            raise LeaveServiceException(f"Leave request {request_id} not found")

        if leave_request.status != "PENDING":
            raise LeaveServiceException(
                f"Cannot approve request with status: {leave_request.status}"
            )

        # 2. Update leave balance if approved
        if action == "APPROVED":
            balance = await LeaveBalanceRepository.get_balance(
                db,
                leave_request.employee_id,
                leave_request.leave_type_id,
                leave_request.start_date.year
            )

            if not balance or balance.remaining < leave_request.total_days:
                raise LeaveServiceException("Insufficient leave balance")

            # Deduct from balance
            await LeaveBalanceRepository.update_balance(
                db,
                leave_request.employee_id,
                leave_request.leave_type_id,
                leave_request.start_date.year,
                leave_request.total_days
            )

        # 3. Create approval record
        await LeaveApprovalRepository.create(db, {
            "leave_request_id": request_id,
            "approver_person_id": approver_person_id,
            "action": action,
            "comment": comment,
            "action_at": datetime.now()
        })

        # 4. Update request status
        await LeaveRequestRepository.update_status(db, request_id, action)

        return {
            "request_id": request_id,
            "status": action,
            "message": f"Leave request {action.lower()}"
        }

    @staticmethod
    async def cancel_leave(
            db: AsyncSession,
            request_id: int,
            employee_id: int
    ) -> Dict:
        """
        Cancel a pending leave request

        Business Rules:
        1. Only PENDING requests can be cancelled
        2. Employee can only cancel their own requests
        """

        leave_request = await LeaveRequestRepository.get_by_id(db, request_id)

        if not leave_request:
            raise LeaveServiceException(f"Leave request {request_id} not found")

        if leave_request.employee_id != employee_id:
            raise LeaveServiceException("You can only cancel your own requests")

        if leave_request.status != "PENDING":
            raise LeaveServiceException(
                f"Cannot cancel request with status: {leave_request.status}"
            )

        await LeaveRequestRepository.update_status(db, request_id, "CANCELLED")

        return {
            "request_id": request_id,
            "status": "CANCELLED",
            "message": "Leave request cancelled successfully"
        }

    @staticmethod
    async def get_leave_requests(
            db: AsyncSession,
            employee_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Dict]:
        """Get all leave requests for an employee"""

        requests = await LeaveRequestRepository.get_by_employee(
            db, employee_id, skip, limit
        )

        return [
            {
                "id": req.id,
                "leave_type": req.leave_type.code,
                "leave_type_name": req.leave_type.name,
                "start_date": req.start_date.isoformat(),
                "end_date": req.end_date.isoformat(),
                "total_days": req.total_days,
                "reason": req.reason,
                "status": req.status,
                "created_at": req.created_at.isoformat()
            }
            for req in requests
        ]