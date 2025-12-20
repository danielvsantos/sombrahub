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

2. **Deals Board (Sales CRM)**
   - Kanban-style board with 5 stages: New, Proposal, Negotiation, Won, Lost
   - Create new deals with client, value, and notes
   - Move deals between stages via dropdown menu
   - Recurring/retainer deal tracking with special badges
   - Automatic job creation when deals move to "Won" stage

3. **Production Dashboard**
   - Accordion-style job cards showing active jobs
   - Deliverables table per job with status tracking
   - Deliverable statuses: To Do, Shooting, Editing, Review, Done
   - Assignee management
   - Due date tracking with overdue highlighting
   - Job completion workflow

4. **Clients Management**
   - Client database with contact info
   - Industry categorization
   - Deal and job counts per client

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
  production.html      # Production jobs with accordion UI
  clients.html         # Clients grid view
  partials/
    deals_board.html   # Kanban columns partial
    deliverables_table.html  # Job deliverables table partial
    clients_list.html  # Clients grid partial
    status_badge.html  # Status badge partial
```

## Database Models

- **User**: id, username, password_hash, role
- **Client**: id, name, industry, email, phone
- **Deal**: id, client_id, title, value, stage, is_recurring, notes
- **Job**: id, client_id, deal_id, status, start_date, is_retainer
- **Deliverable**: id, job_id, title, status, assignee_id, due_date

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
