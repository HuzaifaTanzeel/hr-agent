import { Link } from "wouter";
import { Users, Building2, Bot, Calendar, CheckCircle, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-12 lg:py-20">
        <div className="text-center mb-12 lg:mb-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6">
            <Bot className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-4xl lg:text-5xl font-bold tracking-tight mb-4">
            HR AI Agent
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Smart leave management powered by AI. Apply for leave, check balances, 
            and get instant answers to your HR questions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-16">
          <Card className="relative overflow-visible group">
            <CardHeader className="pb-4">
              <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <CardTitle className="text-xl">Employee Portal</CardTitle>
              <CardDescription>
                Chat with the HR AI assistant, apply for leave, check your balance, and view request status.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground mb-6">
                <li className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-primary" />
                  AI-powered chat assistant
                </li>
                <li className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-primary" />
                  Leave request management
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-primary" />
                  Real-time balance tracking
                </li>
              </ul>
              <Link href="/employee">
                <Button className="w-full" data-testid="link-employee-portal">
                  Enter Employee Portal
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="relative overflow-visible group">
            <CardHeader className="pb-4">
              <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-4">
                <Building2 className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <CardTitle className="text-xl">HR Portal</CardTitle>
              <CardDescription>
                Manage leave requests, approve or reject applications, and view employee conversations.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground mb-6">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-primary" />
                  Approve/reject requests
                </li>
                <li className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary" />
                  View all employees
                </li>
                <li className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-primary" />
                  Review conversations
                </li>
              </ul>
              <Link href="/hr">
                <Button variant="outline" className="w-full" data-testid="link-hr-portal">
                  Enter HR Portal
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Powered by AI for smarter HR management
          </p>
        </div>
      </div>
    </div>
  );
}
