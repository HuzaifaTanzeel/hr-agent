import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { MessageSquare, Calendar, Wallet, ArrowLeft, Filter, History, Plus, User } from "lucide-react";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatInterface } from "@/components/chat/chat-interface";
import { LeaveBalanceGrid } from "@/components/leave/leave-balance-card";
import { LeaveRequestList } from "@/components/leave/leave-request-card";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { apiService } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { LeaveStatus, Conversation } from "@shared/schema";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";

const CURRENT_EMPLOYEE_ID = 1;
const CURRENT_PERSON_ID = 1;

type StatusFilter = "ALL" | LeaveStatus;

export default function EmployeePortal() {
  const [activeTab, setActiveTab] = useState("chat");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [chatKey, setChatKey] = useState(0);
  const { toast } = useToast();

  const { 
    data: leaveRequests = [], 
    isLoading: isLoadingRequests 
  } = useQuery({
    queryKey: ['/api/v1/employees', CURRENT_EMPLOYEE_ID, 'leave-requests'],
    queryFn: () => apiService.getLeaveRequests(CURRENT_EMPLOYEE_ID),
    enabled: activeTab === "requests" || activeTab === "chat",
  });

  const { 
    data: leaveBalance, 
    isLoading: isLoadingBalance 
  } = useQuery({
    queryKey: ['/api/v1/employees', CURRENT_EMPLOYEE_ID, 'leave-balance'],
    queryFn: () => apiService.getLeaveBalance(CURRENT_EMPLOYEE_ID),
    enabled: activeTab === "balance",
  });

  const {
    data: conversations = [],
    isLoading: isLoadingConversations,
  } = useQuery({
    queryKey: ['/api/v1/employees', CURRENT_EMPLOYEE_ID, 'conversations'],
    queryFn: () => apiService.getEmployeeConversations(CURRENT_EMPLOYEE_ID),
    enabled: activeTab === "chat",
  });

  const cancelMutation = useMutation({
    mutationFn: (requestId: number) => apiService.cancelLeaveRequest(requestId, CURRENT_EMPLOYEE_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ 
        queryKey: ['/api/v1/employees', CURRENT_EMPLOYEE_ID, 'leave-requests'] 
      });
      toast({
        title: "Request Cancelled",
        description: "Your leave request has been cancelled successfully.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to cancel request",
        variant: "destructive",
      });
    },
  });

  const handleCancelRequest = (requestId: number) => {
    cancelMutation.mutate(requestId);
  };

  const handleSelectConversation = (conversationId: string) => {
    setSelectedConversationId(conversationId);
  };

  const handleNewChat = () => {
    setSelectedConversationId(null);
    setChatKey(k => k + 1);
  };

  const filteredRequests = statusFilter === "ALL" 
    ? leaveRequests 
    : leaveRequests.filter(r => r.status === statusFilter);

  const balances = leaveBalance?.balances.map(b => ({
    leaveType: b.leave_type,
    totalAllocated: b.total_allocated,
    used: b.used,
    remaining: b.remaining,
  })) || [];

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
            <h1 className="font-semibold text-lg">Employee Portal</h1>
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
                  value="chat" 
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12 px-0"
                  data-testid="tab-chat"
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Chat
                </TabsTrigger>
                <TabsTrigger 
                  value="requests" 
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12 px-0"
                  data-testid="tab-requests"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  My Requests
                </TabsTrigger>
                <TabsTrigger 
                  value="balance" 
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12 px-0"
                  data-testid="tab-balance"
                >
                  <Wallet className="w-4 h-4 mr-2" />
                  Leave Balance
                </TabsTrigger>
              </TabsList>
            </div>
          </div>

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
                      data-testid="button-new-chat"
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
                            onClick={() => handleSelectConversation(conv.id)}
                            className={`w-full text-left p-3 rounded-lg transition-colors hover-elevate ${
                              selectedConversationId === conv.id
                                ? "bg-primary/10 border border-primary/20"
                                : "hover:bg-muted/50"
                            }`}
                            data-testid={`button-conversation-${conv.id}`}
                          >
                            <div className="flex items-start gap-3">
                              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                <User className="w-4 h-4 text-primary" />
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
                  key={selectedConversationId ?? `new-${chatKey}`}
                  employeeId={CURRENT_EMPLOYEE_ID} 
                  personId={CURRENT_PERSON_ID}
                  role="employee"
                  initialConversationId={selectedConversationId}
                  onConversationChange={setSelectedConversationId}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="requests" className="flex-1 m-0 p-4 lg:p-6 data-[state=inactive]:hidden">
            <div className="container mx-auto max-w-6xl">
              <div className="flex items-center justify-between gap-4 mb-6 flex-wrap">
                <h2 className="text-xl font-semibold">My Leave Requests</h2>
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
                onCancel={handleCancelRequest}
                emptyMessage="You haven't submitted any leave requests yet"
              />
            </div>
          </TabsContent>

          <TabsContent value="balance" className="flex-1 m-0 p-4 lg:p-6 data-[state=inactive]:hidden">
            <div className="container mx-auto max-w-6xl">
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-1">Leave Balance</h2>
                <p className="text-muted-foreground text-sm">
                  Your leave allocation for {new Date().getFullYear()}
                </p>
              </div>
              <LeaveBalanceGrid balances={balances} isLoading={isLoadingBalance} />
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
