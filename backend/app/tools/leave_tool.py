"""
Leave Management Tools for HR Agent

These tools wrap the LeaveService and provide agent-compatible interfaces.
Tools are called by the agent and execute deterministic backend operations.
"""
import logging
from datetime import date
from typing import Optional
from agents import function_tool, RunContextWrapper

from app.services.leave_service import LeaveService, LeaveServiceException

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL FUNCTIONS (FIXED - Using RunContext for dependency injection)
# ============================================================================

@function_tool
async def apply_for_leave(
        ctx: RunContextWrapper,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str
) -> dict:
    """
    Apply for leave.

    This tool allows employees to submit leave requests.
    It validates the request, checks balance, and creates the leave request.

    Args:
        ctx: Run context (provides access to db and employee_id)
        leave_type: Type of leave (ANNUAL, SICK, CASUAL, UNPAID)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        reason: Reason for leave (minimum 10 characters)

    Returns:
        Dictionary with request details and status
    """
    # Extract dependencies from context
    db = ctx.context.get("db")
    employee_id = ctx.context.get("employee_id")

    logger.info(f"🔧 Tool: apply_for_leave called by employee {employee_id}")
    logger.info(f"   Leave type: {leave_type}, Dates: {start_date} to {end_date}")

    try:
        # Parse dates
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Call service
        result = await LeaveService.apply_leave(
            db=db,
            employee_id=employee_id,
            leave_type_code=leave_type,
            start_date=start,
            end_date=end,
            reason=reason
        )

        logger.info(f"   ✅ Leave request created: ID {result['id']}")

        return {
            "success": True,
            "request_id": result["id"],
            "status": result["status"],
            "total_days": result["total_days"],
            "remaining_balance": result["remaining_balance"],
            "message": f"Leave request submitted successfully. Request ID: {result['id']}"
        }

    except LeaveServiceException as e:
        logger.warning(f"   ⚠️  Leave application failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Could not apply for leave: {str(e)}"
        }
    except ValueError as e:
        logger.error(f"   ❌ Invalid date format: {str(e)}")
        return {
            "success": False,
            "error": "Invalid date format. Please use YYYY-MM-DD format.",
            "message": "Invalid date format. Please use YYYY-MM-DD format (e.g., 2026-02-01)."
        }
    except Exception as e:
        logger.error(f"   ❌ Unexpected error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while applying for leave."
        }


@function_tool
async def check_leave_balance(
        ctx: RunContextWrapper,
        leave_type: Optional[str] = None,
        year: Optional[int] = None
) -> dict:
    """
    Check leave balance for the employee.

    This tool retrieves the employee's leave balance for all leave types
    or a specific leave type.

    Args:
        ctx: Run context (provides access to db and employee_id)
        leave_type: Optional - specific leave type (ANNUAL, SICK, etc.)
        year: Optional - year (defaults to current year)

    Returns:
        Dictionary with leave balance information
    """
    # Extract dependencies from context
    db = ctx.context.get("db")
    employee_id = ctx.context.get("employee_id")

    logger.info(f"🔧 Tool: check_leave_balance called by employee {employee_id}")
    logger.info(f"   Leave type: {leave_type or 'ALL'}, Year: {year or 'CURRENT'}")

    try:
        # Call service
        balance = await LeaveService.get_leave_balance(
            db=db,
            employee_id=employee_id,
            leave_type_code=leave_type,
            year=year
        )

        logger.info(f"   ✅ Balance retrieved successfully")

        return {
            "success": True,
            "data": balance,
            "message": "Leave balance retrieved successfully"
        }

    except LeaveServiceException as e:
        logger.warning(f"   ⚠️  Balance check failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Could not retrieve leave balance: {str(e)}"
        }
    except Exception as e:
        logger.error(f"   ❌ Unexpected error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while checking leave balance."
        }


@function_tool
async def cancel_leave_request(
        ctx: RunContextWrapper,
        request_id: int
) -> dict:
    """
    Cancel a pending leave request.

    This tool allows employees to cancel their own pending leave requests.
    Only PENDING requests can be cancelled.

    Args:
        ctx: Run context (provides access to db and employee_id)
        request_id: ID of the leave request to cancel

    Returns:
        Dictionary with cancellation result
    """
    # Extract dependencies from context
    db = ctx.context.get("db")
    employee_id = ctx.context.get("employee_id")

    logger.info(f"🔧 Tool: cancel_leave_request called by employee {employee_id}")
    logger.info(f"   Request ID: {request_id}")

    try:
        # Call service
        result = await LeaveService.cancel_leave(
            db=db,
            request_id=request_id,
            employee_id=employee_id
        )

        logger.info(f"   ✅ Leave request {request_id} cancelled")

        return {
            "success": True,
            "request_id": result["request_id"],
            "status": result["status"],
            "message": result["message"]
        }

    except LeaveServiceException as e:
        logger.warning(f"   ⚠️  Cancellation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Could not cancel leave request: {str(e)}"
        }
    except Exception as e:
        logger.error(f"   ❌ Unexpected error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while cancelling the leave request."
        }


@function_tool
async def get_leave_requests(
        ctx: RunContextWrapper,
        skip: Optional[int] = 0,
        limit: Optional[int] = 100
) -> dict:
    """
    Get all leave requests for the employee.

    This tool retrieves the employee's leave request history.

    Args:
        ctx: Run context (provides access to db and employee_id)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        Dictionary with list of leave requests
    """
    # Extract dependencies from context
    db = ctx.context.get("db")
    employee_id = ctx.context.get("employee_id")

    logger.info(f"🔧 Tool: get_leave_requests called by employee {employee_id}")
    logger.info(f"   Skip: {skip}, Limit: {limit}")

    try:
        # Call service
        requests = await LeaveService.get_leave_requests(
            db=db,
            employee_id=employee_id,
            skip=skip,
            limit=limit
        )

        logger.info(f"   ✅ Retrieved {len(requests)} leave requests")

        return {
            "success": True,
            "data": requests,
            "count": len(requests),
            "message": f"Retrieved {len(requests)} leave request(s)"
        }

    except LeaveServiceException as e:
        logger.warning(f"   ⚠️  Request retrieval failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Could not retrieve leave requests: {str(e)}"
        }
    except Exception as e:
        logger.error(f"   ❌ Unexpected error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while retrieving leave requests."
        }