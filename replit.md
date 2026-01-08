# Sombra Hub - Sombra Lab Agency Management Platform

## Overview

Sombra Hub is a full-stack web application for managing Sombra Lab's sales and production workflows. It combines a Sales CRM (deals board) with Production Management (jobs and tasks tracking).

**Tech Stack:**
- Backend: Python Flask with SQLAlchemy ORM
- Database: PostgreSQL (Replit built-in, with separate dev/prod databases)
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
   - Tasks table per job with status tracking
   - Task statuses: To Do, In Progress, Review, Done
   - Assignee management
   - Due date tracking with overdue highlighting
   - Job completion workflow
   - Click on job title to view detailed job page with kanban

5. **Job Detail Page**
   - Kanban view of tasks organized by status
   - Add/edit/delete tasks with HTMX and unified modal
   - Team assignment management
   - View linked deal information

6. **Production Calendar**
   - Monthly calendar view of all tasks by due date
   - Filter by specific job
   - Color-coded status indicators
   - Navigate between months
   - Click on task to view job detail

7. **Clients Management**
   - Client database with contact info (email, phone, address)
   - Industry categorization
   - Deal and job counts per client
   - Click to view detailed client page

8. **Client Detail Page**
   - Full contact information display
   - Stats overview (total deals, active jobs, total value)
   - Related deals list with links
   - Kanban view of all tasks across all client jobs
   - Edit client information

## Database Models

- **User**: id, username, password_hash, role, full_name, email
- **Client**: id, name, industry, email, phone, address, notes
- **Deal**: id, client_id, title, value, cost_internal, cost_external, stage, is_recurring, notes
- **DealProfitShare**: id, deal_id, user_id, percentage, flat_amount
- **Job**: id, client_id, deal_id, title, status, start_date, is_retainer
- **JobAssignment**: id, job_id, user_id, role
- **Deliverable** (displayed as "Task"): id, job_id, title, description, status, assignee_id, due_date

## Demo Credentials

- Admin: `admin` / `admin`
- Photographer: `alex` / `alex123`
- Photographer: `jordan` / `jordan123`

## Project Structure

```
app.py                 # Main Flask application with all routes and models
templates/
  base.html            # Base layout with sidebar navigation + unified task modal
  login.html           # Login page
  dashboard.html       # Dashboard with stats and quick links
  deals.html           # Deals kanban board
  deal_detail.html     # Deal detail with costs and profit shares
  production.html      # Production jobs with accordion UI
  production_calendar.html  # Calendar view of tasks
  job_detail.html      # Job kanban view
  clients.html         # Clients grid view
  client_detail.html   # Client detail with info and kanban
  users.html           # User management (admin only)
  user_edit.html       # Edit user form
  partials/
    deals_board.html   # Kanban columns partial
    deliverables_table.html  # Job tasks table partial
    task_modal.html    # Unified add/edit task modal
    clients_list.html  # Clients grid partial
    status_badge.html  # Status badge partial
    users_list.html    # Users table partial
    profit_shares.html # Profit shares table partial
    job_kanban.html    # Job tasks kanban partial
    job_assignments.html  # Job team assignments partial
    calendar_grid.html # Calendar month grid partial
```

## Running the Application

The application runs on port 5000:
```bash
python app.py
```

## Architecture Notes

### Task Status System
Task statuses are centralized via `TASK_STATUSES` constant in app.py:
- "To Do" - New tasks not yet started
- "In Progress" - Tasks currently being worked on
- "Review" - Tasks awaiting review/approval
- "Done" - Completed tasks

### Unified Task Modal
The task add/edit modal is defined once in `partials/task_modal.html` and included in `base.html`. JavaScript functions control its behavior:
- `openTaskModal(mode, jobId, taskData, redirectTo, htmxTarget)` - Opens modal for add/edit
- `openEditTaskModal(taskId, jobId, redirectTo, htmxTarget)` - Fetches task data and opens edit modal
- `openAddDeliverableModal(jobId)` - Wrapper for production page compatibility

### Context Processor
`inject_users()` provides `all_users` (User objects) and `all_users_json` (serialized list) to all templates for populating assignee dropdowns.

### Database Connection Pooling
SQLAlchemy engine is configured with:
- `pool_pre_ping=True` - Validates connections before use
- `pool_recycle=300` - Recycles connections every 5 minutes
- `@app.teardown_appcontext` - Properly cleans up sessions

## Design Choices

- DaisyUI "night" theme for dark mode interface
- Purple/blue gradient accents for branding
- Glass morphism effects on login card
- Subtle animations and transitions
- Responsive layout with mobile sidebar drawer
- HTMX for seamless dynamic updates

## Development & Production Workflow

This application uses Replit's built-in PostgreSQL database system, which provides **separate development and production databases** automatically.

### How It Works

1. **Development Database**: Used when running the app in the Replit editor (via `python app.py`). This is where you make changes and test new features.

2. **Production Database**: Created automatically when you publish/deploy the app. Production users work with this database, which is isolated from development.

### Workflow for Making Changes

1. **Develop & Test**: Make code changes in the editor. The development database is automatically seeded with demo data on first run.

2. **Test Locally**: Use the development preview to verify your changes work correctly with the demo credentials:
   - Admin: `admin` / `admin`
   - Photographer: `alex` / `alex123`

3. **Publish to Production**: When ready, click "Deploy" or "Publish" to push your changes live. New tables will be created automatically; column changes require manual migration.

4. **Database Isolation**: Changes you make in development (adding test data, etc.) do NOT affect production users. They have their own separate database.

### Database Schema Changes

- The app uses `db.create_all()` which creates new tables but does NOT modify existing tables
- Adding new models (tables): Will be created automatically on deployment
- Adding new columns to existing tables: Requires manual SQL migration via the Database panel
- Removing columns/tables: Requires manual SQL migration and user coordination

**For column changes**, use the Database panel to run SQL like:
```sql
ALTER TABLE "user" ADD COLUMN new_field VARCHAR(100);
```

### Rolling Back

Replit provides point-in-time restore for production databases if you need to recover from a bad deployment. Access this through the Database panel in the Replit interface.

### Environment Variables

- `DATABASE_URL`: Automatically set by Replit for PostgreSQL connection
- `SESSION_SECRET`: Should be set in Secrets for secure session management

## Pending Features

- Multi-assignee support for tasks
- File upload capability for tasks
- Labels/tags system with admin management
- Role-based access control for clients/deals (admin only)
- Drag-and-drop for kanban task management
