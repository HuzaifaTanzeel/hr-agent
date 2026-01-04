# HR AI Agent Frontend - Design Guidelines

## Design Approach
**Reference-Based**: Modern SaaS productivity tools (Linear, Notion, Slack) - Clean, professional interfaces optimized for efficiency and clarity with conversational AI elements.

## Core Design Elements

### Typography
- **Headings**: Bold, clear hierarchy (font-weight: 600-700)
- **Body Text**: Readable 14-16px for main content
- **Chat Messages**: Comfortable 14px with 1.5 line-height
- **Font Family**: System fonts or modern sans-serif via Google Fonts (Inter, DM Sans, or similar)

### Layout System
**Tailwind Spacing**: Primary units: 2, 3, 4, 6, 8, 12, 16, 20
- Component padding: p-4 to p-8
- Section spacing: py-12 to py-20
- Card spacing: p-6
- Gap utilities: gap-4, gap-6

### Color Palette
**Status-Driven System**:
- Primary: Blue (#3B82F6) - Actions, links, user messages
- Success: Green (#10B981) - Approved status, positive actions
- Warning: Yellow/Amber (#F59E0B) - Pending status
- Error: Red (#EF4444) - Rejected status, errors
- Background: Light gray (#F9FAFB)
- Surface: White (#FFFFFF)
- Text Primary: Dark gray (#111827)
- Text Secondary: Medium gray (#6B7280)
- Borders: Light gray (#E5E7EB)

## Portal-Specific Layouts

### Employee Portal
**Three-Section Layout**:
1. **Chat Interface** (Primary view)
   - Full-height chat container with fixed input at bottom
   - Message area: Auto-scroll, comfortable padding
   - User messages: Right-aligned, primary blue background, white text, rounded-lg
   - AI messages: Left-aligned, light gray background, dark text, rounded-lg
   - Input section: Fixed bottom, shadow-lg, white background
   - Typing indicator: Animated dots in AI message style

2. **Leave Requests Section**
   - Grid/list of cards (grid-cols-1 md:grid-cols-2 lg:grid-cols-3)
   - Each card: Leave type badge, date range, status badge, reason preview
   - Status badges: Color-coded (green/yellow/red), rounded-full
   - Filter tabs at top: All, Pending, Approved, Rejected

3. **Leave Balance Section**
   - Card-based layout for each leave type
   - Progress bars showing used vs. remaining
   - Visual hierarchy: Large numbers for remaining days
   - Color coding: Green for healthy balance, amber for low

### HR Portal
**Dashboard + Table Layout**:
1. **Dashboard Section** (Top)
   - Stat cards in grid (grid-cols-2 lg:grid-cols-4)
   - Quick metrics: Pending count, approved today, rejected today
   - Icon + number + label format

2. **Leave Management Table**
   - Clean table with hover states
   - Columns: Employee, Type, Dates, Days, Status, Actions
   - Action buttons: Inline approve/reject with modal confirmation
   - Filters: Dropdown for status, date range picker

## Component Library

### Cards
- Border radius: rounded-lg (12px)
- Shadow: shadow-sm with hover:shadow-md
- Background: white
- Padding: p-6
- Border: Optional 1px light gray

### Buttons
- **Primary**: Blue background, white text, rounded-lg, px-6 py-3
- **Secondary**: White background, gray border, gray text
- **Success**: Green background, white text
- **Danger**: Red background, white text
- Hover: Subtle shadow and color shift
- Loading state: Spinner + disabled appearance

### Badges
- Small rounded-full pills
- Status-based colors (bg-green-100 text-green-800 for approved)
- Font size: text-xs to text-sm
- Padding: px-3 py-1

### Input Fields
- Border: 1px gray with focus:border-blue
- Rounded: rounded-md
- Padding: px-4 py-2
- Focus ring: ring-2 ring-blue-500/20

### Modals/Dialogs
- Overlay: Dark semi-transparent backdrop
- Content: White, centered, shadow-2xl, rounded-xl
- Max width: max-w-lg to max-w-2xl
- Padding: p-6 to p-8

## Chat Interface Design Specifics

### Message Bubbles
- **User**: 
  - Max-width: max-w-[80%]
  - Background: bg-blue-500
  - Text: text-white
  - Position: ml-auto
  - Rounded: rounded-2xl with rounded-br-sm
  
- **AI Agent**:
  - Max-width: max-w-[80%]
  - Background: bg-gray-100
  - Text: text-gray-900
  - Position: mr-auto
  - Rounded: rounded-2xl with rounded-bl-sm

### Chat Container
- Background: Subtle pattern or solid light gray
- Padding: p-4 to p-6
- Messages spacing: space-y-4
- Auto-scroll behavior on new messages

## Responsive Behavior

- **Mobile** (base): 
  - Single column layouts
  - Full-width cards
  - Stacked navigation (hamburger menu)
  
- **Tablet** (md): 
  - 2-column grids where appropriate
  - Sidebar navigation visible
  
- **Desktop** (lg+): 
  - 3-4 column grids for cards
  - Full table layouts
  - Persistent sidebar

## Navigation Structure

### Employee Portal
- Tab-based or sidebar navigation
- Sections: Chat, My Requests, Leave Balance
- Active state: Blue underline or background

### HR Portal
- Sidebar with sections: Dashboard, Leave Requests, Conversations
- Role indicator at top
- Quick stats in header

## Visual Enhancements

- Smooth transitions: transition-all duration-200
- Hover effects on interactive elements
- Empty states: Centered icon + text + action button
- Loading states: Skeleton loaders matching content structure
- Toast notifications: Bottom-right, slide-in animation, auto-dismiss

## Accessibility & UX

- Focus visible outlines (ring-2 ring-blue-500)
- Keyboard navigation support
- Loading indicators for async actions
- Confirmation dialogs for destructive actions
- Error messages: Inline below inputs, toast for general errors
- Success feedback: Toast notifications, status updates

This design creates a professional, efficient HR management interface that balances conversational AI interaction with structured data management.