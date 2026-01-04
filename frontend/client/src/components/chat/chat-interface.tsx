import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Send, Bot, User, Loader2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { ChatMessage, ChatRequest } from "@shared/schema";
import { apiService } from "@/lib/api";
import { cn } from "@/lib/utils";

export type ChatRole = "employee" | "hr";

interface ChatConfig {
  title: string;
  description: string;
  suggestions: string[];
  userLabel: string;
}

const CHAT_CONFIGS: Record<ChatRole, ChatConfig> = {
  employee: {
    title: "HR AI Assistant",
    description: "I'm here to help you with leave requests, check your balance, view request status, and answer policy questions.",
    suggestions: [
      "Apply for annual leave",
      "Check my leave balance",
      "View pending requests",
      "What are the leave policies?",
    ],
    userLabel: "You",
  },
  hr: {
    title: "HR Management Assistant",
    description: "I can help you with leave approvals, employee queries, policy updates, and HR management tasks.",
    suggestions: [
      "Show pending requests",
      "Approve leave for employee",
      "View employee balances",
      "Generate leave report",
    ],
    userLabel: "HR",
  },
};

interface ChatInterfaceProps {
  employeeId: number;
  personId: number;
  role?: ChatRole;
  initialConversationId?: string | null;
  onConversationChange?: (conversationId: string | null) => void;
}

export function ChatInterface({ 
  employeeId, 
  personId, 
  role = "employee",
  initialConversationId = null,
  onConversationChange 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loadedConversationId, setLoadedConversationId] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const config = CHAT_CONFIGS[role];
  const shouldLoadConversation = initialConversationId && initialConversationId !== loadedConversationId;

  const { data: conversationData, isLoading: isLoadingMessages } = useQuery({
    queryKey: ['/api/v1/conversations', initialConversationId, 'messages'],
    queryFn: () => apiService.getConversationMessages(initialConversationId!),
    enabled: !!shouldLoadConversation,
    staleTime: 0,
  });

  useEffect(() => {
    if (conversationData && initialConversationId) {
      const loadedMessages: ChatMessage[] = conversationData.messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }));
      setMessages(loadedMessages);
      setConversationId(initialConversationId);
      setLoadedConversationId(initialConversationId);
    }
  }, [conversationData, initialConversationId]);

  useEffect(() => {
    if (initialConversationId === null && loadedConversationId !== null) {
      setMessages([]);
      setConversationId(null);
      setLoadedConversationId(null);
    }
  }, [initialConversationId, loadedConversationId]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (request: ChatRequest) => apiService.sendMessage(request),
    onSuccess: (response) => {
      if (!conversationId) {
        setConversationId(response.conversation_id);
        onConversationChange?.(response.conversation_id);
      }

      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: "assistant",
        content: response.message,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    },
    onError: () => {
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: "assistant",
        content: "I apologize, but I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    },
  });

  const sendMessage = useCallback(async () => {
    const trimmedMessage = inputValue.trim();
    if (!trimmedMessage || chatMutation.isPending) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: trimmedMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");

    chatMutation.mutate({
      message: trimmedMessage,
      employee_id: employeeId,
      person_id: personId,
      conversation_id: conversationId,
      actor_role: role,
    });
  }, [inputValue, chatMutation, employeeId, personId, conversationId, role]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const isLoading = Boolean(shouldLoadConversation) && isLoadingMessages;
  const isHR = role === "hr";

  return (
    <div className="flex flex-col h-full bg-muted/30">
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Loading conversation...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center px-4">
            <div className={cn(
              "w-16 h-16 rounded-full flex items-center justify-center mb-4",
              isHR ? "bg-blue-100 dark:bg-blue-900/30" : "bg-primary/10"
            )}>
              {isHR ? (
                <Shield className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              ) : (
                <Bot className="w-8 h-8 text-primary" />
              )}
            </div>
            <h3 className="text-lg font-semibold mb-2">{config.title}</h3>
            <p className="text-muted-foreground max-w-md mb-6">
              {config.description}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md">
              {config.suggestions.map((suggestion) => (
                <Button
                  key={suggestion}
                  variant="outline"
                  className="text-left justify-start h-auto py-3 px-4"
                  onClick={() => {
                    setInputValue(suggestion);
                    textareaRef.current?.focus();
                  }}
                  data-testid={`button-suggestion-${suggestion.toLowerCase().replace(/\s+/g, '-').replace(/\?/g, '')}`}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 pb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex gap-3",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
                data-testid={`message-${message.role}-${message.id}`}
              >
                {message.role === "assistant" && (
                  <Avatar className="w-8 h-8 shrink-0">
                    <AvatarFallback className={cn(
                      isHR ? "bg-blue-600 text-white" : "bg-primary text-primary-foreground"
                    )}>
                      {isHR ? <Shield className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </AvatarFallback>
                  </Avatar>
                )}
                <div
                  className={cn(
                    "max-w-[80%] rounded-2xl px-4 py-3",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground rounded-br-sm"
                      : "bg-card border border-border rounded-bl-sm"
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {message.content}
                  </p>
                </div>
                {message.role === "user" && (
                  <Avatar className="w-8 h-8 shrink-0">
                    <AvatarFallback className={cn(
                      isHR ? "bg-blue-100 dark:bg-blue-900/30" : "bg-muted"
                    )}>
                      {isHR ? <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400" /> : <User className="w-4 h-4" />}
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}
            {chatMutation.isPending && (
              <div className="flex gap-3 justify-start" data-testid="thinking-indicator">
                <Avatar className="w-8 h-8 shrink-0">
                  <AvatarFallback className={cn(
                    isHR ? "bg-blue-600 text-white" : "bg-primary text-primary-foreground"
                  )}>
                    {isHR ? <Shield className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </AvatarFallback>
                </Avatar>
                <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-pulse" style={{ animationDelay: "0ms", animationDuration: "1s" }} />
                      <span className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-pulse" style={{ animationDelay: "200ms", animationDuration: "1s" }} />
                      <span className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-pulse" style={{ animationDelay: "400ms", animationDuration: "1s" }} />
                    </div>
                    <span className="text-sm text-muted-foreground">Thinking</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      <div className="border-t bg-background p-4">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <Textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="min-h-[44px] max-h-32 resize-none"
            rows={1}
            disabled={chatMutation.isPending || isLoading}
            data-testid="input-chat-message"
          />
          <Button
            onClick={sendMessage}
            disabled={!inputValue.trim() || chatMutation.isPending || isLoading}
            size="icon"
            data-testid="button-send-message"
          >
            {chatMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
