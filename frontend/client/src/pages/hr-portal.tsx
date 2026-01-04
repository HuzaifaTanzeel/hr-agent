import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { 
  LayoutDashboard, 
  Calendar, 
  MessageSquare, 
  ArrowLeft, 
  Clock, 
  CheckCircle2, 
  XCircle,
  Users,
  Filter,
  Plus,
  History,
  Shield
} from "lucide-react";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LeaveRequestList } from "@/components/leave/leave-request-card";
import { ChatInterface } from "@/components/chat/chat-interface";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { apiService } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { LeaveStatus, Conversation } from "@shared/schema";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";

const HR_PERSON_ID = 4;
const HR_EMPLOYEE_ID = 4;

type StatusFilter = "ALL" | LeaveStatus;

interface ApprovalDialogState {
  isOpen: boolean;
  requestId: number | null;
  action: "APPROVED" | "REJECTED" | null;
  comment: string;
}

interface SelectedConversation {
  id: string;
  employeeId: number;
}

export default function HRPortal() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [selectedConversation, setSelectedConversation] = useState<SelectedConversation | null>(null);
  const [chatKey, setChatKey] = useState(0);
  const [approvalDialog, setApprovalDialog] = useState<ApprovalDialogState>({
    isOpen: false,
    requestId: null,
    action: null,
    comment: "",
  });
  const { toast } = useToast();

  const { data: employees = [] } = useQuery({
    queryKey: ['/api/v1/employees'],
    queryFn: () => apiService.getEmployees(),
  });

  const { 
    data: leaveRequests = [], 
    isLoading: isLoadingRequests 
  } = useQuery({
    queryKey: ['/api/v1/leave-requests'],
    queryFn: () => apiService.getAllLeaveRequests(),
  });

  const { 
    data: conversations = [], 
    isLoading: isLoadingConversations 
  } = useQuery({
    queryKey: ['/api/v1/employees', HR_EMPLOYEE_ID, 'conversations'],
    queryFn: () => apiService.getEmployeeConversations(HR_EMPLOYEE_ID),
    enabled: activeTab === "chat",
  });

  const approvalMutation = useMutation({
    mutationFn: ({ requestId, approval }: { requestId: number; approval: { leave_request_id: number; approver_person_id: number; action: "APPROVED" | "REJECTED"; comment: string } }) => 
      apiService.approveLeaveRequest(requestId, approval),
    onSuccess: (_, variables) => {
      // Invalidate all relevant queries to refresh the data
      queryClient.invalidateQueries({ queryKey: ['/api/v1/leave-requests'] });
      queryClient.invalidateQueries({ queryKey: ['/api/v1/employees'] });
      // Invalidate all employee leave request queries (pattern matching)
      queryClient.invalidateQueries({ 
        queryKey: ['/api/v1/employees'],
        exact: false
      });
      toast({
        title: variables.approval.action === "APPROVED" ? "Request Approved" : "Request Rejected",
        description: `The leave request has been ${variables.approval.action.toLowerCase()}.`,
      });
      closeApprovalDialog();
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to process request",
        variant: "destructive",
      });
    },
  });

  const openApprovalDialog = (requestId: number, action: "APPROVED" | "REJECTED") => {
    setApprovalDialog({
      isOpen: true,
      requestId,
      action,
      comment: "",
    });
  };

  const closeApprovalDialog = () => {
    setApprovalDialog({
      isOpen: false,
      requestId: null,
      action: null,
      comment: "",
    });
  };

  const handleApproval = () => {
    if (!approvalDialog.requestId || !approvalDialog.action) return;

    approvalMutation.mutate({
      requestId: approvalDialog.requestId,
      approval: {
        leave_request_id: approvalDialog.requestId,
        approver_person_id: HR_PERSON_ID,
        action: approvalDialog.action,
        comment: approvalDialog.comment,
      },
    });
  };

  const handleSelectConversation = (conv: Conversation) => {
    setSelectedConversation({
      id: conv.id,
      employeeId: conv.employeeId,
    });
  };

  const handleNewChat = () => {
    setSelectedConversation(null);
    setChatKey(k => k + 1);
  };

  const employeeMap = employees.reduce((acc, emp) => {
    acc[emp.id] = emp.name;
    return acc;
  }, {} as Record<number, string>);

  const filteredRequests = statusFilter === "ALL"
    ? leaveRequests
    : leaveRequests.filter(r => r.status === statusFilter);

  const pendingCount = leaveRequests.filter(r => r.status === "PENDING").length;
  const approvedCount = leaveRequests.filter(r => r.status === "APPROVED").length;
  const rejectedCount = leaveRequests.filter(r => r.status === "REJECTED").length;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost" size="icon" data-testid="button-back-home">
                <ArrowLeft className="w-5 h-5" />
              </Button>
            </Link>
            <h1 className="font-semibold text-lg">HR Portal</h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 flex flex-col">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <div className="border-b bg-background">
            <div className="container mx-auto px-4">
              <TabsList className="h-12 bg-transparent p-0 gap-4">
                <TabsTrigger
                  value="dashboard"
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12 px-0"
                  data-testid="tab-dashboard"
                >
                  <LayoutDashboard className="w-4 h-4 mr-2" />
                  Dashboard
                </TabsTrigger>
                <TabsTrigger
                  value="requests"
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12 px-0"
                  data-testid="tab-requests"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Leave Requests
                </TabsTrigger>
                <TabsTrigger
                  value="chat"
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12 px-0"
                  data-testid="tab-chat"
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Chat
                </TabsTrigger>
              </TabsList>
            </div>
          </div>

          <TabsContent value="dashboard" className="flex-1 m-0 p-4 lg:p-6 data-[state=inactive]:hidden">
            <div className="container mx-auto max-w-6xl">
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-1">Dashboard</h2>
                <p className="text-muted-foreground text-sm">Overview of leave management</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <Card data-testid="card-stat-pending">
                  <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Pending Requests
                    </CardTitle>
                    <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                      <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{pendingCount}</div>
                    <p className="text-xs text-muted-foreground">Awaiting review</p>
                  </CardContent>
                </Card>

                <Card data-testid="card-stat-approved">
                  <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Approved
                    </CardTitle>
                    <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                      <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{approvedCount}</div>
                    <p className="text-xs text-muted-foreground">Total approved</p>
                  </CardContent>
                </Card>

                <Card data-testid="card-stat-rejected">
                  <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Rejected
                    </CardTitle>
                    <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
                      <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{rejectedCount}</div>
                    <p className="text-xs text-muted-foreground">Total rejected</p>
                  </CardContent>
                </Card>

                <Card data-testid="card-stat-employees">
                  <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Employees
                    </CardTitle>
                    <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                      <Users className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{employees.length}</div>
                    <p className="text-xs text-muted-foreground">Total employees</p>
                  </CardContent>
                </Card>
              </div>

              {pendingCount > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Pending Requests</h3>
                  <LeaveRequestList
                    requests={leaveRequests.filter(r => r.status === "PENDING")}
                    isLoading={isLoadingRequests}
                    showEmployee
                    employees={employeeMap}
                    onApprove={(id) => openApprovalDialog(id, "APPROVED")}
                    onReject={(id) => openApprovalDialog(id, "REJECTED")}
                    isHRView
                    emptyMessage="No pending requests"
                  />
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="requests" className="flex-1 m-0 p-4 lg:p-6 data-[state=inactive]:hidden">
            <div className="container mx-auto max-w-6xl">
              <div className="flex items-center justify-between gap-4 mb-6 flex-wrap">
                <h2 className="text-xl font-semibold">All Leave Requests</h2>
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as StatusFilter)}>
                    <SelectTrigger className="w-[140px]" data-testid="select-status-filter">
                      <SelectValue placeholder="Filter status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Status</SelectItem>
                      <SelectItem value="PENDING">Pending</SelectItem>
                      <SelectItem value="APPROVED">Approved</SelectItem>
                      <SelectItem value="REJECTED">Rejected</SelectItem>
                      <SelectItem value="CANCELLED">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <LeaveRequestList
                requests={filteredRequests}
                isLoading={isLoadingRequests}
                showEmployee
                employees={employeeMap}
                onApprove={(id) => openApprovalDialog(id, "APPROVED")}
                onReject={(id) => openApprovalDialog(id, "REJECTED")}
                isHRView
                emptyMessage="No leave requests found"
              />
            </div>
          </TabsContent>

          <TabsContent value="chat" className="flex-1 m-0 data-[state=inactive]:hidden">
            <div className="flex h-[calc(100vh-7rem)]">
              <div className="w-80 border-r bg-muted/30 flex flex-col">
                <div className="p-4 border-b">
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <h3 className="font-semibold">Conversations</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleNewChat}
                      data-testid="button-new-hr-chat"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      New
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Your chat history with the HR assistant
                  </p>
                </div>
                <ScrollArea className="flex-1">
                  <div className="p-2">
                    {isLoadingConversations ? (
                      <div className="space-y-2 p-2">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="p-3 rounded-lg bg-muted/50">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-muted animate-pulse rounded-full" />
                              <div className="flex-1">
                                <div className="h-3 w-24 bg-muted animate-pulse rounded mb-2" />
                                <div className="h-2 w-full bg-muted animate-pulse rounded" />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : conversations.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-8 text-center px-4">
                        <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-3">
                          <History className="w-6 h-6 text-muted-foreground" />
                        </div>
                        <p className="text-sm text-muted-foreground">No conversations yet</p>
                        <p className="text-xs text-muted-foreground mt-1">Start a new chat to begin</p>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        {conversations.map((conv: Conversation) => (
                          <button
                            key={conv.id}
                            onClick={() => handleSelectConversation(conv)}
                            className={`w-full text-left p-3 rounded-lg transition-colors hover-elevate ${
                              selectedConversation?.id === conv.id
                                ? "bg-primary/10 border border-primary/20"
                                : "hover:bg-muted/50"
                            }`}
                            data-testid={`button-conversation-${conv.id}`}
                          >
                            <div className="flex items-start gap-3">
                              <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                                <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2 mb-0.5">
                                  <span className="text-sm font-medium truncate">{conv.title}</span>
                                  <span className="text-xs text-muted-foreground shrink-0">
                                    {format(new Date(conv.updatedAt), "MMM d")}
                                  </span>
                                </div>
                                <p className="text-xs text-muted-foreground truncate">
                                  {conv.lastMessage}
                                </p>
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </div>
              <div className="flex-1">
                <ChatInterface
                  key={selectedConversation?.id ?? `new-${chatKey}`}
                  employeeId={selectedConversation?.employeeId ?? HR_EMPLOYEE_ID}
                  personId={HR_PERSON_ID}
                  role="hr"
                  initialConversationId={selectedConversation?.id ?? null}
                  onConversationChange={(convId) => {
                    if (convId) {
                      setSelectedConversation({ id: convId, employeeId: HR_EMPLOYEE_ID });
                    } else {
                      setSelectedConversation(null);
                    }
                  }}
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>

      <Dialog open={approvalDialog.isOpen} onOpenChange={(open) => !open && closeApprovalDialog()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {approvalDialog.action === "APPROVED" ? "Approve Request" : "Reject Request"}
            </DialogTitle>
            <DialogDescription>
              {approvalDialog.action === "APPROVED"
                ? "Add an optional comment for the employee."
                : "Please provide a reason for rejecting this request."}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="comment">Comment</Label>
            <Textarea
              id="comment"
              value={approvalDialog.comment}
              onChange={(e) => setApprovalDialog(prev => ({ ...prev, comment: e.target.value }))}
              placeholder={
                approvalDialog.action === "APPROVED"
                  ? "Optional: Add a message..."
                  : "Please explain the reason..."
              }
              className="mt-2"
              data-testid="input-approval-comment"
            />
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={closeApprovalDialog} data-testid="button-cancel-dialog">
              Cancel
            </Button>
            <Button
              onClick={handleApproval}
              disabled={approvalMutation.isPending}
              className={
                approvalDialog.action === "APPROVED"
                  ? "bg-green-600 hover:bg-green-700"
                  : ""
              }
              variant={approvalDialog.action === "REJECTED" ? "destructive" : "default"}
              data-testid="button-confirm-approval"
            >
              {approvalMutation.isPending ? "Processing..." : approvalDialog.action === "APPROVED" ? "Approve" : "Reject"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
