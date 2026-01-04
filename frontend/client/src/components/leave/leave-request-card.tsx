import { format, parseISO } from "date-fns";
import { Calendar, Clock, AlertCircle, CheckCircle2, XCircle, Ban } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { LeaveRequest, LeaveStatus } from "@shared/schema";
import { cn } from "@/lib/utils";

interface LeaveRequestCardProps {
  request: LeaveRequest;
  showEmployee?: boolean;
  employeeName?: string;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onCancel?: (id: number) => void;
  isHRView?: boolean;
}

const statusConfig: Record<LeaveStatus, { 
  label: string; 
  icon: React.ElementType; 
  variant: "default" | "secondary" | "destructive" | "outline";
  className: string;
}> = {
  PENDING: { 
    label: "Pending", 
    icon: Clock, 
    variant: "secondary",
    className: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800"
  },
  APPROVED: { 
    label: "Approved", 
    icon: CheckCircle2, 
    variant: "default",
    className: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800"
  },
  REJECTED: { 
    label: "Rejected", 
    icon: XCircle, 
    variant: "destructive",
    className: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800"
  },
  CANCELLED: { 
    label: "Cancelled", 
    icon: Ban, 
    variant: "outline",
    className: "bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400 border-gray-200 dark:border-gray-700"
  },
};

const leaveTypeNames: Record<string, string> = {
  ANNUAL: "Annual Leave",
  SICK: "Sick Leave",
  CASUAL: "Casual Leave",
  UNPAID: "Unpaid Leave",
};

export function LeaveRequestCard({ 
  request, 
  showEmployee,
  employeeName,
  onApprove, 
  onReject, 
  onCancel,
  isHRView 
}: LeaveRequestCardProps) {
  const status = statusConfig[request.status as LeaveStatus] || statusConfig.PENDING;
  const StatusIcon = status.icon;

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return "—";
    try {
      // Handle both ISO date strings (2026-02-10) and ISO datetime strings
      const date = parseISO(dateStr);
      return format(date, "MMM d, yyyy");
    } catch (error) {
      // If parsing fails, try to return the original string or show placeholder
      console.warn("Failed to parse date:", dateStr, error);
      return dateStr;
    }
  };

  return (
    <Card 
      className="overflow-visible"
      data-testid={`card-leave-request-${request.id}`}
    >
      <CardHeader className="flex flex-row items-start justify-between gap-4 pb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-base">
              {request.leave_type_name || leaveTypeNames[request.leave_type] || request.leave_type || "Leave Request"}
            </h3>
            <Badge 
              variant={status.variant}
              className={cn("shrink-0", status.className)}
            >
              <StatusIcon className="w-3 h-3 mr-1" />
              {status.label}
            </Badge>
          </div>
          {showEmployee && employeeName && (
            <p className="text-sm text-muted-foreground">{employeeName}</p>
          )}
        </div>
        <div className="text-right shrink-0">
          <span className="text-2xl font-bold">{request.total_days}</span>
          <span className="text-sm text-muted-foreground ml-1">
            {request.total_days === 1 ? "day" : "days"}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Calendar className="w-4 h-4 shrink-0" />
          <span>
            {formatDate(request.start_date)} — {formatDate(request.end_date)}
          </span>
        </div>
        
        <div className="flex items-start gap-2 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-muted-foreground" />
          <p className="text-muted-foreground line-clamp-2">{request.reason}</p>
        </div>

        {request.approver_comment && (
          <div className="pt-2 border-t">
            <p className="text-sm">
              <span className="font-medium">Comment: </span>
              <span className="text-muted-foreground">{request.approver_comment}</span>
            </p>
          </div>
        )}

        {(isHRView && request.status === "PENDING" && (onApprove || onReject)) && (
          <div className="flex gap-2 pt-2 border-t">
            {onApprove && (
              <Button 
                size="sm" 
                onClick={() => onApprove(request.id)}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                data-testid={`button-approve-${request.id}`}
              >
                <CheckCircle2 className="w-4 h-4 mr-1" />
                Approve
              </Button>
            )}
            {onReject && (
              <Button 
                size="sm" 
                variant="destructive"
                onClick={() => onReject(request.id)}
                className="flex-1"
                data-testid={`button-reject-${request.id}`}
              >
                <XCircle className="w-4 h-4 mr-1" />
                Reject
              </Button>
            )}
          </div>
        )}

        {(!isHRView && request.status === "PENDING" && onCancel) && (
          <div className="pt-2 border-t">
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onCancel(request.id)}
              className="w-full"
              data-testid={`button-cancel-${request.id}`}
            >
              <Ban className="w-4 h-4 mr-1" />
              Cancel Request
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface LeaveRequestListProps {
  requests: LeaveRequest[];
  isLoading?: boolean;
  showEmployee?: boolean;
  employees?: Record<number, string>;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onCancel?: (id: number) => void;
  isHRView?: boolean;
  emptyMessage?: string;
}

export function LeaveRequestList({ 
  requests, 
  isLoading, 
  showEmployee,
  employees = {},
  onApprove, 
  onReject, 
  onCancel,
  isHRView,
  emptyMessage = "No leave requests found"
}: LeaveRequestListProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-3">
              <div className="flex justify-between">
                <div className="h-5 w-32 bg-muted animate-pulse rounded" />
                <div className="h-8 w-12 bg-muted animate-pulse rounded" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="h-4 w-full bg-muted animate-pulse rounded" />
              <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Calendar className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="font-medium text-lg mb-1">No Requests</h3>
        <p className="text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {requests.map((request) => (
        <LeaveRequestCard
          key={request.id}
          request={request}
          showEmployee={showEmployee}
          employeeName={employees[request.employee_id || 0]}
          onApprove={onApprove}
          onReject={onReject}
          onCancel={onCancel}
          isHRView={isHRView}
        />
      ))}
    </div>
  );
}
