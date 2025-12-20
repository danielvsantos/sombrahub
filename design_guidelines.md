# Creative Agency Management Platform - Design Guidelines

## Design Approach
**System Selected:** DaisyUI Dark Theme (as specified)
**Rationale:** Utility-focused CRM/Project Management tool requiring consistency, professional appearance, and efficient workflows.

## Core Design Elements

### Typography
- **Primary Font:** System font stack via Tailwind (`font-sans`)
- **Hierarchy:**
  - Page titles: `text-3xl font-bold`
  - Section headers: `text-xl font-semibold`
  - Card/accordion headers: `text-lg font-medium`
  - Body text: `text-base`
  - Labels/meta: `text-sm text-base-content/70`

### Layout System
**Spacing Units:** Tailwind units of 2, 4, 6, and 8
- Component padding: `p-4` to `p-6`
- Section spacing: `gap-6` or `gap-8`
- Card margins: `mb-6`
- Sidebar width: `w-64` (desktop), full-width drawer (mobile)

### Color Strategy (Status Indicators)
- **Deal Stages:** New (badge-info), Proposal (badge-warning), Negotiation (badge-accent), Won (badge-success), Lost (badge-error)
- **Deliverable Status:** To Do (badge-ghost), Shooting (badge-info), Editing (badge-warning), Review (badge-accent), Done (badge-success)
- **Job Status:** Active (badge-primary), Completed (badge-success)
- **Retainer Flag:** Use badge-secondary with "Retainer" label

## Component Library

### Navigation
**Sidebar (Desktop):**
- Fixed left sidebar with dark background
- Logo/brand at top
- Navigation links with FontAwesome icons (fa-home, fa-handshake, fa-briefcase)
- User profile section at bottom with logout
- Active state: Highlighted background with left border accent

**Mobile:** Drawer component from DaisyUI

### Deals Board (Kanban)
**Layout:** 5-column horizontal grid (one per stage)
- Each column: Rounded card container with header showing stage name and count
- Deal cards: White/light cards with shadow, draggable (HTMX)
- Card content: Client name (bold), deal title, value (large, prominent), recurring badge if applicable
- Compact design: `min-h-24` per card
- Add deal button at top of each column

### Production Dashboard (Accordion)
**Job Accordion Items:**
- Header row: Client name (left), status badge (center-right), expand icon (right)
- Collapsed height: `h-16`
- Expanded: Shows deliverables table
- Alternating subtle background for visual separation

**Deliverables Table:**
- Columns: Title, Status (dropdown), Assignee, Due Date, Actions
- Status dropdown: Inline select with colored badges
- Compact rows: `py-3`
- Hover state on rows
- Add deliverable button above table

### Forms & Inputs
- Form groups: `space-y-4`
- Input fields: DaisyUI `input input-bordered`
- Select dropdowns: DaisyUI `select select-bordered`
- Textareas: `textarea textarea-bordered min-h-24`
- Submit buttons: `btn btn-primary`
- Cancel/secondary: `btn btn-ghost`

### Cards & Containers
- Standard card: `card bg-base-200 shadow-lg`
- Card body: `card-body p-6`
- Stats/metrics: `stats shadow` component from DaisyUI
- Use `divider` component between major sections

## Page-Specific Layouts

### Login Page
- Centered card on full-height container
- Max width: `max-w-md`
- Agency logo/name at top
- Form with username, password inputs
- Primary login button (full width)
- Subtle background pattern or gradient

### Dashboard (Home)
- 3-column stat cards at top: Total Deals, Active Jobs, Deliverables Due
- 2-column grid below: Recent deals (left), Upcoming deliverables (right)
- Each section in card containers

### Deals Board
- Full-width layout with horizontal scroll if needed
- Sticky header with "Add Deal" primary button (right)
- Columns use `flex-shrink-0 w-80` for consistent width

### Production View
- Header with "Active Jobs" title and "Add Job" button
- Accordion stack with `space-y-4`
- Filter/search bar at top (search by client name)

## Interactions & States

### Drag & Drop (HTMX)
- Dragging deal card: Slight opacity reduction, cursor change
- Drop zones: Subtle border highlight on hover
- Success feedback: Brief success alert toast

### Status Changes
- Dropdown selection triggers immediate update (HTMX)
- Optimistic UI update with loading indicator
- Badge color change reflects new status instantly

### Modals
- Use DaisyUI modal component for forms (Add Deal, Add Deliverable, Edit)
- Dark backdrop: `modal-backdrop`
- Modal content: `modal-box max-w-2xl`
- Form layout inside modal with proper spacing

## Responsive Behavior
- **Desktop (lg:):** Sidebar visible, multi-column grids
- **Tablet (md:):** Sidebar drawer, 2-column grids
- **Mobile:** Single column, drawer navigation, horizontal scroll on kanban

## Images
**No hero images required** - This is a utility application focused on data display and workflow management. All visual interest comes from the data visualization, status indicators, and efficient layouts.

## Accessibility
- Consistent focus states on all interactive elements
- Semantic HTML structure
- ARIA labels on icon-only buttons
- Proper color contrast for text on dark theme
- Keyboard navigation support for all features