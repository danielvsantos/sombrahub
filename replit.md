# CreativeHub - Creative Agency Management Platform

## Overview

CreativeHub is a full-stack web application for managing a creative agency's sales and production workflows. It combines a Sales CRM (deals board) with Production Management (jobs and deliverables tracking).

**Tech Stack:**
- Backend: Python Flask with SQLAlchemy ORM
- Database: SQLite
- Frontend: Server-side rendered HTML with Jinja2 templates
- Styling: TailwindCSS + DaisyUI (dark theme via CDN)
- Interactivity: HTMX for dynamic updates without page reloads
- Authentication: Flask-Login
- Icons: Font Awesome

## Key Features

1. **Authentication System**
   - Login/logout with Flask-Login
   - Role-based users (Admin, Photographer)
   - Protected routes requiring authentication

2. **User Management (Admin Only)**
   - CRUD operations for team members
   - Role assignment (Admin, Photographer)
   - Full name and email tracking
   - View job assignments per user

3. **Deals Board (Sales CRM)**
   - Kanban-style board with 5 stages: New, Proposal, Negotiation, Won, Lost
   - Create new deals with client, value, and notes
   - Move deals between stages via dropdown menu
   - **Cost Tracking**: Internal cost, external cost, profit calculation
   - **Profit Sharing**: Allocate profit percentages and flat amounts to team members
   - Recurring/retainer deal tracking with special badges
   - Automatic job creation when deals move to "Won" stage
   - Click on deal title to view detailed deal page

4. **Production Dashboard**
   - Accordion-style job cards showing active jobs
   - Deliverables table per job with status tracking
   - Deliverable statuses: To Do, Shooting, Editing, Review, Done
   - Assignee management
   - Due date tracking with overdue highlighting
   - Job completion workflow
   - Click on job title to view detailed job page with kanban

5. **Job Detail Page**
   - Kanban view of deliverables organized by status
   - Add/edit/delete deliverables with HTMX
   - Team assignment management
   - View linked deal information

6. **Production Calendar**
   - Monthly calendar view of all deliverables by due date
   - Filter by specific job
   - Color-coded status indicators
   - Navigate between months
   - Click on deliverable to view job detail

7. **Clients Management**
   - Client database with contact info (email, phone, address)
   - Industry categorization
   - Deal and job counts per client
   - Click to view detailed client page

8. **Client Detail Page**
   - Full contact information display
   - Stats overview (total deals, active jobs, total value)
   - Related deals list with links
   - Kanban view of all deliverables across all client jobs
   - Edit client information

## Database Models

- **User**: id, username, password_hash, role, full_name, email
- **Client**: id, name, industry, email, phone, address, notes
- **Deal**: id, client_id, title, value, cost_internal, cost_external, stage, is_recurring, notes
- **DealProfitShare**: id, deal_id, user_id, percentage, flat_amount
- **Job**: id, client_id, deal_id, title, status, start_date, is_retainer
- **JobAssignment**: id, job_id, user_id, role
- **Deliverable**: id, job_id, title, description, status, assignee_id, due_date

## Demo Credentials

- Admin: `admin` / `admin`
- Photographer: `alex` / `alex123`
- Photographer: `jordan` / `jordan123`

## Project Structure

```
app.py                 # Main Flask application with all routes and models
templates/
  base.html            # Base layout with sidebar navigation
  login.html           # Login page
  dashboard.html       # Dashboard with stats and quick links
  deals.html           # Deals kanban board
  deal_detail.html     # Deal detail with costs and profit shares
  production.html      # Production jobs with accordion UI
  production_calendar.html  # Calendar view of deliverables
  job_detail.html      # Job kanban view
  clients.html         # Clients grid view
  client_detail.html   # Client detail with info and kanban
  users.html           # User management (admin only)
  user_edit.html       # Edit user form
  partials/
    deals_board.html   # Kanban columns partial
    deliverables_table.html  # Job deliverables table partial
    clients_list.html  # Clients grid partial
    status_badge.html  # Status badge partial
    users_list.html    # Users table partial
    profit_shares.html # Profit shares table partial
    job_kanban.html    # Job deliverables kanban partial
    job_assignments.html  # Job team assignments partial
    calendar_grid.html # Calendar month grid partial
```

## Running the Application

The application runs on port 5000:
```bash
python app.py
```

## Design Choices

- DaisyUI "night" theme for dark mode interface
- Purple/blue gradient accents for branding
- Glass morphism effects on login card
- Subtle animations and transitions
- Responsive layout with mobile sidebar drawer
- HTMX for seamless dynamic updates
