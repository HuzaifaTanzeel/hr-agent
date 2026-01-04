import { z } from "zod";

// Leave Request Status
export const leaveStatusEnum = z.enum(["PENDING", "APPROVED", "REJECTED", "CANCELLED"]);
export type LeaveStatus = z.infer<typeof leaveStatusEnum>;

// Leave Type (simplified - backend provides this)
export interface LeaveType {
  id: number;
  code: string;
  name: string;
  max_days_per_year: number;
  requires_approval: boolean;
}

// Leave Request (matches backend API response from get_leave_requests)
export interface LeaveRequest {
  id: number;
  employee_id?: number; // May not be present in all responses
  leave_type: string; // Leave type code (ANNUAL, SICK, CASUAL, UNPAID)
  leave_type_name: string; // Full name (Annual Leave, Sick Leave, etc.)
  start_date: string; // ISO date string
  end_date: string; // ISO date string
  total_days: number;
  reason: string;
  status: LeaveStatus;
  created_at: string; // ISO datetime string
  approver_person_id?: number | null;
  approver_comment?: string | null;
}

// Chat Message Interface (for frontend state)
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

// Conversation Status from backend
export const conversationStatusEnum = z.enum(["ACTIVE", "COMPLETED", "FAILED", "CLOSED"]);
export type ConversationStatus = z.infer<typeof conversationStatusEnum>;

// Sender type from backend API
export type SenderType = "USER" | "ASSISTANT";

// Chat Request/Response types matching backend API
export interface ChatRequest {
  message: string;
  employee_id: number;
  person_id: number;
  conversation_id: string | null;
  actor_role?: "employee" | "hr";
}

export interface ChatResponse {
  conversation_id: string;
  success: boolean;
  message: string;
  intent: string;
  turn: number;
}

// Leave Balance Response (matches backend API)
export interface LeaveBalanceResponse {
  employee_id: number;
  year: number;
  balances: {
    leave_type: string;
    total_allocated: number;
    used: number;
    remaining: number;
  }[];
}

// Approval Request
export interface ApprovalRequest {
  leave_request_id: number;
  approver_person_id: number;
  action: "APPROVED" | "REJECTED";
  comment: string;
}

// Employee type for frontend
export interface Employee {
  id: number;
  name: string;
  email: string;
  department: string;
}

// Backend API Conversation type (matches GET /api/v1/agent/conversations response)
export interface ApiConversation {
  conversation_id: string;
  person_id: number;
  employee_id: number;
  status: ConversationStatus;
  created_at: string;
  last_activity: string;
  turn_count: number;
}

// Backend API Conversations List Response
export interface ConversationsListResponse {
  conversations: ApiConversation[];
  total: number;
}

// Frontend Conversation type (transformed for UI use)
export interface Conversation {
  id: string;
  employeeId: number;
  employeeName: string;
  title: string;
  lastMessage: string;
  status: ConversationStatus;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
}

// HR Conversation type (alias for backward compatibility)
export type HRConversation = Conversation;

// Backend API Message type (matches GET /api/v1/agent/conversations/{id}/messages response)
export interface ApiMessage {
  id: number;
  sender_type: SenderType;
  content: string;
  intent: string | null;
  sequence_number: number;
  created_at: string;
}

// Stored message from API (frontend-friendly format)
export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sequenceNumber?: number;
  intent?: string | null;
}

// Response when fetching conversation messages (frontend format)
export interface ConversationMessagesResponse {
  conversation_id: string;
  employee_id: number;
  messages: ConversationMessage[];
}
