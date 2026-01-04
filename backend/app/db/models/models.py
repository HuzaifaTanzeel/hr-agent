"""
SQLAlchemy Models - Maps to PostgreSQL tables (public schema)
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


# =========================
# PERSON
# =========================
class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    auth_user = relationship("AuthUser", back_populates="person", uselist=False)
    employee = relationship("Employee", back_populates="person", uselist=False)
    roles = relationship("PersonRole", back_populates="person")
    conversations = relationship("Conversation", back_populates="person")
    approvals = relationship("LeaveApproval", back_populates="approver")


# =========================
# AUTH USER
# =========================
class AuthUser(Base):
    __tablename__ = "auth_user"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    auth_provider = Column(String(20), default="LOCAL")
    last_login_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("auth_provider IN ('LOCAL', 'GOOGLE', 'SSO')", name="check_auth_provider"),
    )

    person = relationship("Person", back_populates="auth_user")


# =========================
# ROLE
# =========================
class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    __table_args__ = (
        CheckConstraint("code IN ('EMPLOYEE', 'HR', 'MANAGER')", name="check_role_code"),
    )

    person_roles = relationship("PersonRole", back_populates="role")


# =========================
# PERSON ROLE (M2M)
# =========================
class PersonRole(Base):
    __tablename__ = "person_role"

    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    person = relationship("Person", back_populates="roles")
    role = relationship("Role", back_populates="person_roles")


# =========================
# EMPLOYEE
# =========================
class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_code = Column(String(50), unique=True, nullable=False)
    department = Column(String(100))
    designation = Column(String(100))
    joining_date = Column(Date, nullable=False)
    manager_id = Column(Integer, ForeignKey("employee.id", ondelete="SET NULL"))

    person = relationship("Person", back_populates="employee")
    manager = relationship("Employee", remote_side=[id], backref="subordinates")
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")


# =========================
# LEAVE TYPE
# =========================
class LeaveType(Base):
    __tablename__ = "leave_type"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    max_days_per_year = Column(Integer, nullable=False)
    requires_approval = Column(Boolean, default=True)

    leave_balances = relationship("LeaveBalance", back_populates="leave_type")
    leave_requests = relationship("LeaveRequest", back_populates="leave_type")


# =========================
# LEAVE BALANCE
# =========================
class LeaveBalance(Base):
    __tablename__ = "leave_balance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_type.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    total_allocated = Column(Integer, nullable=False)
    used = Column(Integer, default=0)
    remaining = Column(Integer, nullable=False)

    employee = relationship("Employee", back_populates="leave_balances")
    leave_type = relationship("LeaveType", back_populates="leave_balances")


# =========================
# LEAVE REQUEST
# =========================
class LeaveRequest(Base):
    __tablename__ = "leave_request"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_type.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')",
            name="check_leave_status",
        ),
    )

    employee = relationship("Employee", back_populates="leave_requests")
    leave_type = relationship("LeaveType", back_populates="leave_requests")
    approvals = relationship("LeaveApproval", back_populates="leave_request")


# =========================
# LEAVE APPROVAL
# =========================
class LeaveApproval(Base):
    __tablename__ = "leave_approval"

    id = Column(Integer, primary_key=True, index=True)
    leave_request_id = Column(Integer, ForeignKey("leave_request.id", ondelete="CASCADE"), nullable=False)
    approver_person_id = Column(Integer, ForeignKey("person.id"), nullable=False)
    action = Column(String(20))
    comment = Column(Text)
    action_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("action IN ('APPROVED', 'REJECTED')", name="check_action"),
    )

    leave_request = relationship("LeaveRequest", back_populates="approvals")
    approver = relationship("Person", back_populates="approvals")


# =========================
# CONVERSATION
# =========================
class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="ACTIVE")

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'CLOSED')", name="check_conversation_status"),
    )

    person = relationship("Person", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


# =========================
# MESSAGE
# =========================
class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False)
    sender_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("sender_type IN ('USER', 'ASSISTANT')", name="check_sender_type"),
    )

    conversation = relationship("Conversation", back_populates="messages")
