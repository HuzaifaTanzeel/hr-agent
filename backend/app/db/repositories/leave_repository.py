"""
Repository Layer - Database Operations

Repositories handle all database CRUD operations.
No business logic here - just data access.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from datetime import date
from typing import List, Optional

from app.db.models.models import (
    Employee, Person, LeaveRequest, LeaveBalance, 
    LeaveType, LeaveApproval
)


class EmployeeRepository:
    """Repository for Employee operations"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, employee_id: int) -> Optional[Employee]:
        """Get employee by ID with person details"""
        result = await db.execute(
            select(Employee)
            .options(joinedload(Employee.person))
            .where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_person_id(db: AsyncSession, person_id: int) -> Optional[Employee]:
        """Get employee by person ID"""
        result = await db.execute(
            select(Employee)
            .where(Employee.person_id == person_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, employee_data: dict) -> Employee:
        """Create new employee"""
        employee = Employee(**employee_data)
        db.add(employee)
        await db.commit()
        await db.refresh(employee)
        return employee
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Employee]:
        """Get all employees with pagination"""
        result = await db.execute(
            select(Employee)
            .options(joinedload(Employee.person))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class LeaveRequestRepository:
    """Repository for Leave Request operations"""
    
    @staticmethod
    async def create(db: AsyncSession, request_data: dict) -> LeaveRequest:
        """Create leave request"""
        leave_request = LeaveRequest(**request_data)
        db.add(leave_request)
        await db.commit()
        await db.refresh(leave_request)
        return leave_request
    
    @staticmethod
    async def get_by_id(db: AsyncSession, request_id: int) -> Optional[LeaveRequest]:
        """Get leave request by ID"""
        result = await db.execute(
            select(LeaveRequest)
            .options(
                joinedload(LeaveRequest.employee).joinedload(Employee.person),
                joinedload(LeaveRequest.leave_type)
            )
            .where(LeaveRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_employee(
        db: AsyncSession, 
        employee_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LeaveRequest]:
        """Get all leave requests for an employee"""
        result = await db.execute(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.leave_type))
            .where(LeaveRequest.employee_id == employee_id)
            .order_by(LeaveRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def check_conflicts(
        db: AsyncSession,
        employee_id: int,
        start_date: date,
        end_date: date,
        exclude_request_id: Optional[int] = None
    ) -> List[LeaveRequest]:
        """
        Check for conflicting leave requests.
        Returns requests that overlap with given date range.
        """
        query = select(LeaveRequest).where(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status.in_(['PENDING', 'APPROVED']),
                or_(
                    # New request starts during existing request
                    and_(
                        LeaveRequest.start_date <= start_date,
                        LeaveRequest.end_date >= start_date
                    ),
                    # New request ends during existing request
                    and_(
                        LeaveRequest.start_date <= end_date,
                        LeaveRequest.end_date >= end_date
                    ),
                    # New request completely covers existing request
                    and_(
                        LeaveRequest.start_date >= start_date,
                        LeaveRequest.end_date <= end_date
                    )
                )
            )
        )
        
        if exclude_request_id:
            query = query.where(LeaveRequest.id != exclude_request_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_status(
        db: AsyncSession,
        request_id: int,
        status: str
    ) -> Optional[LeaveRequest]:
        """Update leave request status"""
        result = await db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
        leave_request = result.scalar_one_or_none()
        
        if leave_request:
            leave_request.status = status
            await db.commit()
            await db.refresh(leave_request)
        
        return leave_request


class LeaveBalanceRepository:
    """Repository for Leave Balance operations"""
    
    @staticmethod
    async def get_balance(
        db: AsyncSession,
        employee_id: int,
        leave_type_id: int,
        year: int
    ) -> Optional[LeaveBalance]:
        """Get leave balance for specific type and year"""
        result = await db.execute(
            select(LeaveBalance)
            .options(joinedload(LeaveBalance.leave_type))
            .where(
                and_(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.leave_type_id == leave_type_id,
                    LeaveBalance.year == year
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_balances(
        db: AsyncSession,
        employee_id: int,
        year: int
    ) -> List[LeaveBalance]:
        """Get all leave balances for employee in a year"""
        result = await db.execute(
            select(LeaveBalance)
            .options(joinedload(LeaveBalance.leave_type))
            .where(
                and_(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.year == year
                )
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def create(db: AsyncSession, balance_data: dict) -> LeaveBalance:
        """Create leave balance"""
        balance = LeaveBalance(**balance_data)
        db.add(balance)
        await db.commit()
        await db.refresh(balance)
        return balance
    
    @staticmethod
    async def update_balance(
        db: AsyncSession,
        employee_id: int,
        leave_type_id: int,
        year: int,
        days_to_deduct: int
    ) -> Optional[LeaveBalance]:
        """Update leave balance (deduct used days)"""
        balance = await LeaveBalanceRepository.get_balance(
            db, employee_id, leave_type_id, year
        )
        
        if balance:
            balance.used += days_to_deduct
            balance.remaining -= days_to_deduct
            await db.commit()
            await db.refresh(balance)
        
        return balance


class LeaveTypeRepository:
    """Repository for Leave Type operations"""
    
    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[LeaveType]:
        """Get leave type by code"""
        result = await db.execute(
            select(LeaveType).where(LeaveType.code == code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[LeaveType]:
        """Get all leave types"""
        result = await db.execute(select(LeaveType))
        return result.scalars().all()


class LeaveApprovalRepository:
    """Repository for Leave Approval operations"""
    
    @staticmethod
    async def create(db: AsyncSession, approval_data: dict) -> LeaveApproval:
        """Create leave approval record"""
        approval = LeaveApproval(**approval_data)
        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        return approval
    
    @staticmethod
    async def get_by_request_id(
        db: AsyncSession,
        request_id: int
    ) -> List[LeaveApproval]:
        """Get all approvals for a leave request"""
        result = await db.execute(
            select(LeaveApproval)
            .where(LeaveApproval.leave_request_id == request_id)
            .order_by(LeaveApproval.action_at.desc())
        )
        return result.scalars().all()