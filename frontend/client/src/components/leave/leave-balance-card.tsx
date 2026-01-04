import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Calendar, Briefcase, Heart, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface LeaveBalanceProps {
  leaveType: string;
  totalAllocated: number;
  used: number;
  remaining: number;
}

const leaveTypeConfig: Record<string, { icon: React.ElementType; color: string; bgColor: string }> = {
  ANNUAL: { 
    icon: Calendar, 
    color: "text-blue-600 dark:text-blue-400", 
    bgColor: "bg-blue-100 dark:bg-blue-900/30" 
  },
  SICK: { 
    icon: Heart, 
    color: "text-red-600 dark:text-red-400", 
    bgColor: "bg-red-100 dark:bg-red-900/30" 
  },
  CASUAL: { 
    icon: Briefcase, 
    color: "text-amber-600 dark:text-amber-400", 
    bgColor: "bg-amber-100 dark:bg-amber-900/30" 
  },
  UNPAID: { 
    icon: Clock, 
    color: "text-gray-600 dark:text-gray-400", 
    bgColor: "bg-gray-100 dark:bg-gray-800/50" 
  },
};

const leaveTypeNames: Record<string, string> = {
  ANNUAL: "Annual Leave",
  SICK: "Sick Leave",
  CASUAL: "Casual Leave",
  UNPAID: "Unpaid Leave",
};

export function LeaveBalanceCard({ leaveType, totalAllocated, used, remaining }: LeaveBalanceProps) {
  const config = leaveTypeConfig[leaveType] || leaveTypeConfig.ANNUAL;
  const Icon = config.icon;
  const percentage = totalAllocated > 0 ? (used / totalAllocated) * 100 : 0;
  const isLowBalance = remaining <= 3 && leaveType !== "UNPAID";

  return (
    <Card data-testid={`card-balance-${leaveType.toLowerCase()}`}>
      <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {leaveTypeNames[leaveType] || leaveType}
        </CardTitle>
        <div className={cn("p-2 rounded-lg", config.bgColor)}>
          <Icon className={cn("w-4 h-4", config.color)} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2 mb-3">
          <span 
            className={cn(
              "text-3xl font-bold",
              isLowBalance ? "text-amber-600 dark:text-amber-400" : ""
            )}
            data-testid={`text-remaining-${leaveType.toLowerCase()}`}
          >
            {remaining}
          </span>
          <span className="text-sm text-muted-foreground">
            days remaining
          </span>
        </div>
        
        <Progress 
          value={percentage} 
          className="h-2 mb-2"
        />
        
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{used} used</span>
          <span>{totalAllocated} total</span>
        </div>
      </CardContent>
    </Card>
  );
}

interface LeaveBalanceGridProps {
  balances: LeaveBalanceProps[];
  isLoading?: boolean;
}

export function LeaveBalanceGrid({ balances, isLoading }: LeaveBalanceGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between gap-4 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              <div className="h-8 w-8 bg-muted animate-pulse rounded-lg" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted animate-pulse rounded mb-3" />
              <div className="h-2 bg-muted animate-pulse rounded mb-2" />
              <div className="flex justify-between">
                <div className="h-3 w-12 bg-muted animate-pulse rounded" />
                <div className="h-3 w-12 bg-muted animate-pulse rounded" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {balances.map((balance) => (
        <LeaveBalanceCard
          key={balance.leaveType}
          {...balance}
        />
      ))}
    </div>
  );
}
