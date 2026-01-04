# HR AI Agent Frontend

A modern, responsive React frontend for the HR AI Agent system with two portals for employee self-service and HR management.

## Overview

This application provides a smart leave management system powered by AI chat. Employees can chat with an HR AI assistant, apply for leave, check balances, and view request status. HR staff can manage leave requests, approve/reject applications, and review employee conversations.

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000` (see `../backend/README.md`)

### Installation

1. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

2. **Configure API endpoint**
   - Copy `.env.example` to `.env`
   - The default `VITE_API_URL=http://localhost:8000` should work if backend is running locally
   - For production, update with your backend URL

3. **Run the development server**
   ```bash
   npm run dev
   ```

The frontend will run on `http://localhost:3000`.

## Project Structure

```
frontend/
├── client/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── chat/       # Chat interface components
│   │   │   ├── leave/      # Leave management components
│   │   │   ├── layout/     # Layout components (theme toggle, etc.)
│   │   │   └── ui/         # shadcn/ui components
│   │   ├── pages/          # Page components (home, employee-portal, hr-portal)
│   │   ├── lib/            # Utilities and API client
│   │   │   ├── api.ts      # API service functions
│   │   │   └── queryClient.ts  # React Query configuration
│   │   └── hooks/          # Custom React hooks
│   ├── public/             # Static assets
│   └── index.html          # HTML template
├── shared/                 # Shared TypeScript types and schemas
│   └── schema.ts          # Type definitions matching backend API
├── package.json
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
└── .env                   # Environment variables (create from .env.example)
```

## API Integration

The frontend communicates with the backend API at `http://localhost:8000/api/v1`. All API calls are configured in `client/src/lib/api.ts`.

### Key API Endpoints Used

- **Chat**: `POST /api/v1/agent/chat` - Send messages to HR AI
- **Conversations**: `GET /api/v1/agent/conversations` - List conversations
- **Messages**: `GET /api/v1/agent/conversations/{id}/messages` - Get conversation history
- **Leave Requests**: `GET /api/v1/employees/{id}/leave-requests` - Get employee leave requests
- **Leave Balance**: `GET /api/v1/employees/{id}/leave-balance` - Get leave balance
- **Approvals**: `POST /api/v1/leave-requests/{id}/approve` - Approve/reject leave requests

For complete API documentation, see `../backend/API_ENDPOINTS_DOCUMENTATION.md`.

## Environment Variables

Create a `.env` file in the `frontend` directory:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000
```

For production, update with your production backend URL:
```env
VITE_API_URL=https://api.yourdomain.com
```

## Running Both Frontend and Backend

### Development Setup

**Terminal 1 - Backend:**
```bash
cd backend
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist` directory. You can preview it with:

```bash
npm run preview
```

## Key Features

- **AI Chat Interface**: Conversation continuity with ID management, typing indicators, suggestion buttons
- **Leave Management**: Status filtering, cancel/approve/reject workflows with comments
- **Leave Balance**: Visual progress bars, color-coded by leave type
- **Responsive Design**: Mobile-friendly layouts with proper breakpoints
- **Theme Support**: Light and dark mode with system preference detection
- **Type Safety**: Full TypeScript support with types matching backend API

## Troubleshooting

### CORS Errors
- Ensure backend is running on port 8000
- Backend CORS is configured to allow `http://localhost:3000`
- Check browser console for specific CORS error messages

### API Connection Issues
- Verify backend is running: Visit `http://localhost:8000/api/v1/agent/chat` in browser
- Check `.env` file has correct `VITE_API_URL`
- Ensure no firewall is blocking connections
- Check browser network tab for failed requests

### Port Already in Use
- Change frontend port in `vite.config.ts` (server.port)
- Update backend CORS settings if using a different port

### Type Errors
- Run `npm run check` to verify TypeScript compilation
- Ensure `shared/schema.ts` types match backend API responses

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Query** - Data fetching and caching
- **Wouter** - Lightweight routing
- **shadcn/ui** - UI component library
- **Tailwind CSS** - Styling
- **date-fns** - Date utilities

## Development Notes

- The frontend is a pure client-side application - no backend server code
- All API calls go directly to the Python FastAPI backend
- The `shared/schema.ts` file contains TypeScript types that should match backend API responses
- API service functions in `lib/api.ts` handle request/response transformation
