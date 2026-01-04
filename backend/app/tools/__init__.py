"""
Agent Tools - Functions that the HR agent can call
"""
from app.tools.leave_tool import (
    apply_for_leave,
    check_leave_balance,
    cancel_leave_request,
    get_leave_requests
)

__all__ = [
    "apply_for_leave",
    "check_leave_balance",
    "cancel_leave_request",
    "get_leave_requests"
]

