import os
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Photographer')
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    
    deliverables = db.relationship('Deliverable', backref='assignee', lazy=True)
    job_assignments = db.relationship('JobAssignment', backref='user', lazy=True, cascade='all, delete-orphan')
    profit_shares = db.relationship('DealProfitShare', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    deals = db.relationship('Deal', backref='client', lazy=True)
    jobs = db.relationship('Job', backref='client', lazy=True)


class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Float, default=0.0)
    cost_internal = db.Column(db.Float, default=0.0)
    cost_external = db.Column(db.Float, default=0.0)
    stage = db.Column(db.String(20), default='New')
    is_recurring = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    jobs = db.relationship('Job', backref='deal', lazy=True)
    profit_shares = db.relationship('DealProfitShare', backref='deal', lazy=True, cascade='all, delete-orphan')
    
    @property
    def total_cost(self):
        return self.cost_internal + self.cost_external
    
    @property
    def profit(self):
        return self.value - self.total_cost
    
    @property
    def profit_margin(self):
        if self.value > 0:
            return (self.profit / self.value) * 100
        return 0


class DealProfitShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    percentage = db.Column(db.Float, default=0.0)
    flat_amount = db.Column(db.Float, default=0.0)
    
    @property
    def calculated_amount(self):
        deal = Deal.query.get(self.deal_id)
        if deal:
            return (deal.profit * self.percentage / 100) + self.flat_amount
        return self.flat_amount


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Active')
    start_date = db.Column(db.Date, default=date.today)
    is_retainer = db.Column(db.Boolean, default=False)
    
    deliverables = db.relationship('Deliverable', backref='job', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('JobAssignment', backref='job', lazy=True, cascade='all, delete-orphan')
    
    @property
    def display_title(self):
        if self.title:
            return self.title
        if self.deal:
            return self.deal.title
        return f"Job #{self.id}"


class JobAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(50), default='Photographer')


class Deliverable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='To Do')
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    due_date = db.Column(db.Date, nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Welcome back!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_deals = Deal.query.count()
    active_jobs = Job.query.filter_by(status='Active').count()
    pending_deliverables = Deliverable.query.filter(Deliverable.status != 'Done').count()
    
    recent_deals = Deal.query.order_by(Deal.id.desc()).limit(5).all()
    upcoming_deliverables = Deliverable.query.filter(
        Deliverable.status != 'Done',
        Deliverable.due_date != None
    ).order_by(Deliverable.due_date).limit(5).all()
    
    won_deals_value = db.session.query(db.func.sum(Deal.value)).filter_by(stage='Won').scalar() or 0
    total_profit = db.session.query(
        db.func.sum(Deal.value - Deal.cost_internal - Deal.cost_external)
    ).filter_by(stage='Won').scalar() or 0
    
    return render_template('dashboard.html', 
                         total_deals=total_deals,
                         active_jobs=active_jobs,
                         pending_deliverables=pending_deliverables,
                         recent_deals=recent_deals,
                         upcoming_deliverables=upcoming_deliverables,
                         won_deals_value=won_deals_value,
                         total_profit=total_profit,
                         today=date.today())


# ==================== USER MANAGEMENT ====================

@app.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template('users.html', users=all_users)


@app.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'Photographer')
    full_name = request.form.get('full_name', '')
    email = request.form.get('email', '')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('users'))
    
    user = User(username=username, role=role, full_name=full_name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('User created successfully!', 'success')
    
    if request.headers.get('HX-Request'):
        all_users = User.query.all()
        return render_template('partials/users_list.html', users=all_users)
    
    return redirect(url_for('users'))


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_username = request.form.get('username', user.username)
        
        if new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash('Username already exists.', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
            user.username = new_username
        
        user.full_name = request.form.get('full_name', '')
        user.email = request.form.get('email', '')
        user.role = request.form.get('role', 'Photographer')
        
        new_password = request.form.get('password', '')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        
        if request.headers.get('HX-Request'):
            all_users = User.query.all()
            return render_template('partials/users_list.html', users=all_users)
        
        return redirect(url_for('users'))
    
    return render_template('user_edit.html', user=user)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'error')
        return redirect(url_for('users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted.', 'info')
    
    if request.headers.get('HX-Request'):
        all_users = User.query.all()
        return render_template('partials/users_list.html', users=all_users)
    
    return redirect(url_for('users'))


# ==================== DEALS ====================

@app.route('/deals')
@login_required
def deals():
    stages = ['New', 'Proposal', 'Negotiation', 'Won', 'Lost']
    deals_by_stage = {}
    for stage in stages:
        deals_by_stage[stage] = Deal.query.filter_by(stage=stage).all()
    
    clients = Client.query.all()
    users = User.query.all()
    return render_template('deals.html', deals_by_stage=deals_by_stage, stages=stages, clients=clients, users=users)


@app.route('/deals/add', methods=['POST'])
@login_required
def add_deal():
    client_id = request.form.get('client_id')
    title = request.form.get('title')
    value = float(request.form.get('value', 0) or 0)
    cost_internal = float(request.form.get('cost_internal', 0) or 0)
    cost_external = float(request.form.get('cost_external', 0) or 0)
    stage = request.form.get('stage', 'New')
    is_recurring = request.form.get('is_recurring') == 'on'
    notes = request.form.get('notes', '')
    
    deal = Deal(
        client_id=client_id,
        title=title,
        value=value,
        cost_internal=cost_internal,
        cost_external=cost_external,
        stage=stage,
        is_recurring=is_recurring,
        notes=notes
    )
    db.session.add(deal)
    db.session.commit()
    
    flash('Deal created successfully!', 'success')
    
    if request.headers.get('HX-Request'):
        stages = ['New', 'Proposal', 'Negotiation', 'Won', 'Lost']
        deals_by_stage = {}
        for s in stages:
            deals_by_stage[s] = Deal.query.filter_by(stage=s).all()
        return render_template('partials/deals_board.html', deals_by_stage=deals_by_stage, stages=stages)
    
    return redirect(url_for('deals'))


@app.route('/deals/<int:deal_id>')
@login_required
def deal_detail(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    users = User.query.all()
    clients = Client.query.all()
    return render_template('deal_detail.html', deal=deal, users=users, clients=clients)


@app.route('/deals/<int:deal_id>/edit', methods=['POST'])
@login_required
def edit_deal(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    
    old_title = deal.title
    new_title = request.form.get('title', deal.title)
    
    deal.title = new_title
    deal.value = float(request.form.get('value', deal.value) or 0)
    deal.cost_internal = float(request.form.get('cost_internal', deal.cost_internal) or 0)
    deal.cost_external = float(request.form.get('cost_external', deal.cost_external) or 0)
    deal.is_recurring = request.form.get('is_recurring') == 'on'
    deal.notes = request.form.get('notes', '')
    
    if old_title != new_title:
        linked_jobs = Job.query.filter_by(deal_id=deal_id, title=old_title).all()
        for job in linked_jobs:
            job.title = new_title
    
    db.session.commit()
    flash('Deal updated successfully!', 'success')
    
    return redirect(url_for('deal_detail', deal_id=deal_id))


@app.route('/deals/<int:deal_id>/update-stage', methods=['POST'])
@login_required
def update_deal_stage(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    new_stage = request.form.get('stage')
    old_stage = deal.stage
    
    deal.stage = new_stage
    
    if new_stage == 'Won' and old_stage != 'Won':
        job = Job(
            client_id=deal.client_id,
            deal_id=deal.id,
            title=deal.title,
            status='Active',
            start_date=date.today(),
            is_retainer=deal.is_recurring
        )
        db.session.add(job)
        flash(f'Deal won! New job created for {deal.client.name}', 'success')
    
    db.session.commit()
    
    if request.headers.get('HX-Request'):
        stages = ['New', 'Proposal', 'Negotiation', 'Won', 'Lost']
        deals_by_stage = {}
        for s in stages:
            deals_by_stage[s] = Deal.query.filter_by(stage=s).all()
        return render_template('partials/deals_board.html', deals_by_stage=deals_by_stage, stages=stages)
    
    return redirect(url_for('deals'))


@app.route('/deals/<int:deal_id>/profit-share/add', methods=['POST'])
@login_required
def add_profit_share(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    
    user_id = request.form.get('user_id')
    percentage = float(request.form.get('percentage', 0) or 0)
    flat_amount = float(request.form.get('flat_amount', 0) or 0)
    
    existing = DealProfitShare.query.filter_by(deal_id=deal_id, user_id=user_id).first()
    if existing:
        flash('This user already has a profit share for this deal.', 'error')
    else:
        share = DealProfitShare(deal_id=deal_id, user_id=user_id, percentage=percentage, flat_amount=flat_amount)
        db.session.add(share)
        db.session.commit()
        flash('Profit share added.', 'success')
    
    if request.headers.get('HX-Request'):
        users = User.query.all()
        return render_template('partials/profit_shares.html', deal=deal, users=users)
    
    return redirect(url_for('deal_detail', deal_id=deal_id))


@app.route('/profit-share/<int:share_id>/delete', methods=['POST'])
@login_required
def delete_profit_share(share_id):
    share = DealProfitShare.query.get_or_404(share_id)
    deal_id = share.deal_id
    deal = Deal.query.get(deal_id)
    
    db.session.delete(share)
    db.session.commit()
    
    flash('Profit share removed.', 'info')
    
    if request.headers.get('HX-Request'):
        users = User.query.all()
        return render_template('partials/profit_shares.html', deal=deal, users=users)
    
    return redirect(url_for('deal_detail', deal_id=deal_id))


# ==================== PRODUCTION ====================

@app.route('/production')
@login_required
def production():
    view = request.args.get('view', 'list')
    search = request.args.get('search', '')
    
    if search:
        jobs = Job.query.join(Client).filter(
            Job.status == 'Active',
            Client.name.ilike(f'%{search}%')
        ).all()
    else:
        jobs = Job.query.filter_by(status='Active').all()
    
    users = User.query.all()
    return render_template('production.html', jobs=jobs, users=users, search=search, today=date.today(), view=view)


@app.route('/production/calendar')
@login_required
def production_calendar():
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', date.today().month, type=int)
    job_filter = request.args.get('job_id', '', type=str)
    
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    query = Deliverable.query.filter(
        Deliverable.due_date >= first_day,
        Deliverable.due_date <= last_day
    )
    
    if job_filter:
        query = query.filter(Deliverable.job_id == int(job_filter))
    
    deliverables = query.all()
    
    deliverables_by_date = {}
    for d in deliverables:
        if d.due_date:
            key = d.due_date.day
            if key not in deliverables_by_date:
                deliverables_by_date[key] = []
            deliverables_by_date[key].append(d)
    
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    jobs = Job.query.filter_by(status='Active').all()
    
    if request.headers.get('HX-Request'):
        return render_template('partials/calendar_grid.html',
                             year=year, month=month,
                             month_days=month_days,
                             deliverables_by_date=deliverables_by_date,
                             prev_month=prev_month, prev_year=prev_year,
                             next_month=next_month, next_year=next_year,
                             jobs=jobs, job_filter=job_filter,
                             calendar=calendar, today=date.today())
    
    return render_template('production_calendar.html',
                         year=year, month=month,
                         month_days=month_days,
                         deliverables_by_date=deliverables_by_date,
                         prev_month=prev_month, prev_year=prev_year,
                         next_month=next_month, next_year=next_year,
                         jobs=jobs, job_filter=job_filter,
                         calendar=calendar, today=date.today())


# ==================== JOBS ====================

@app.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    users = User.query.all()
    statuses = ['To Do', 'Shooting', 'Editing', 'Review', 'Done']
    
    deliverables_by_status = {}
    for status in statuses:
        deliverables_by_status[status] = [d for d in job.deliverables if d.status == status]
    
    return render_template('job_detail.html', job=job, users=users, statuses=statuses, 
                         deliverables_by_status=deliverables_by_status, today=date.today())


@app.route('/jobs/<int:job_id>/add-deliverable', methods=['POST'])
@login_required
def add_deliverable(job_id):
    job = Job.query.get_or_404(job_id)
    
    title = request.form.get('title')
    description = request.form.get('description', '')
    assignee_id = request.form.get('assignee_id')
    due_date_str = request.form.get('due_date')
    status = request.form.get('status', 'To Do')
    
    due_date = None
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    
    deliverable = Deliverable(
        job_id=job_id,
        title=title,
        description=description,
        assignee_id=assignee_id if assignee_id else None,
        due_date=due_date,
        status=status
    )
    db.session.add(deliverable)
    db.session.commit()
    
    flash('Deliverable added successfully!', 'success')
    
    redirect_to = request.form.get('redirect_to', 'production')
    
    if request.headers.get('HX-Request'):
        if redirect_to == 'job_detail':
            users = User.query.all()
            statuses = ['To Do', 'Shooting', 'Editing', 'Review', 'Done']
            deliverables_by_status = {}
            for s in statuses:
                deliverables_by_status[s] = [d for d in job.deliverables if d.status == s]
            return render_template('partials/job_kanban.html', job=job, users=users, 
                                 statuses=statuses, deliverables_by_status=deliverables_by_status, today=date.today())
        else:
            users = User.query.all()
            return render_template('partials/deliverables_table.html', job=job, users=users, today=date.today())
    
    if redirect_to == 'job_detail':
        return redirect(url_for('job_detail', job_id=job_id))
    return redirect(url_for('production'))


@app.route('/deliverables/<int:deliverable_id>/update-status', methods=['POST'])
@login_required
def update_deliverable_status(deliverable_id):
    deliverable = Deliverable.query.get_or_404(deliverable_id)
    new_status = request.form.get('status')
    redirect_to = request.form.get('redirect_to', 'production')
    
    deliverable.status = new_status
    db.session.commit()
    
    job = deliverable.job
    
    if request.headers.get('HX-Request'):
        if redirect_to == 'job_detail':
            users = User.query.all()
            statuses = ['To Do', 'Shooting', 'Editing', 'Review', 'Done']
            deliverables_by_status = {}
            for s in statuses:
                deliverables_by_status[s] = [d for d in job.deliverables if d.status == s]
            return render_template('partials/job_kanban.html', job=job, users=users, 
                                 statuses=statuses, deliverables_by_status=deliverables_by_status, today=date.today())
        return render_template('partials/status_badge.html', deliverable=deliverable)
    
    return redirect(url_for('production'))


@app.route('/deliverables/<int:deliverable_id>/delete', methods=['POST'])
@login_required
def delete_deliverable(deliverable_id):
    deliverable = Deliverable.query.get_or_404(deliverable_id)
    job = deliverable.job
    redirect_to = request.form.get('redirect_to', 'production')
    
    db.session.delete(deliverable)
    db.session.commit()
    
    flash('Deliverable deleted.', 'info')
    
    if request.headers.get('HX-Request'):
        if redirect_to == 'job_detail':
            users = User.query.all()
            statuses = ['To Do', 'Shooting', 'Editing', 'Review', 'Done']
            deliverables_by_status = {}
            for s in statuses:
                deliverables_by_status[s] = [d for d in job.deliverables if d.status == s]
            return render_template('partials/job_kanban.html', job=job, users=users, 
                                 statuses=statuses, deliverables_by_status=deliverables_by_status, today=date.today())
        users = User.query.all()
        return render_template('partials/deliverables_table.html', job=job, users=users, today=date.today())
    
    if redirect_to == 'job_detail':
        return redirect(url_for('job_detail', job_id=job.id))
    return redirect(url_for('production'))


@app.route('/jobs/<int:job_id>/complete', methods=['POST'])
@login_required
def complete_job(job_id):
    job = Job.query.get_or_404(job_id)
    job.status = 'Completed'
    db.session.commit()
    
    flash('Job marked as completed!', 'success')
    return redirect(url_for('production'))


@app.route('/jobs/<int:job_id>/assign', methods=['POST'])
@login_required
def assign_user_to_job(job_id):
    job = Job.query.get_or_404(job_id)
    user_id = request.form.get('user_id')
    role = request.form.get('role', 'Photographer')
    
    existing = JobAssignment.query.filter_by(job_id=job_id, user_id=user_id).first()
    if not existing:
        assignment = JobAssignment(job_id=job_id, user_id=user_id, role=role)
        db.session.add(assignment)
        db.session.commit()
        flash('User assigned to job.', 'success')
    else:
        flash('User already assigned.', 'info')
    
    if request.headers.get('HX-Request'):
        users = User.query.all()
        return render_template('partials/job_assignments.html', job=job, users=users)
    
    return redirect(url_for('job_detail', job_id=job_id))


@app.route('/job-assignment/<int:assignment_id>/delete', methods=['POST'])
@login_required
def remove_job_assignment(assignment_id):
    assignment = JobAssignment.query.get_or_404(assignment_id)
    job = assignment.job
    
    db.session.delete(assignment)
    db.session.commit()
    
    flash('Assignment removed.', 'info')
    
    if request.headers.get('HX-Request'):
        users = User.query.all()
        return render_template('partials/job_assignments.html', job=job, users=users)
    
    return redirect(url_for('job_detail', job_id=job.id))


# ==================== CLIENTS ====================

@app.route('/clients')
@login_required
def clients():
    all_clients = Client.query.all()
    return render_template('clients.html', clients=all_clients)


@app.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    
    all_deliverables = []
    for job in client.jobs:
        all_deliverables.extend(job.deliverables)
    
    statuses = ['To Do', 'Shooting', 'Editing', 'Review', 'Done']
    deliverables_by_status = {}
    for status in statuses:
        deliverables_by_status[status] = [d for d in all_deliverables if d.status == status]
    
    users = User.query.all()
    return render_template('client_detail.html', client=client, statuses=statuses, 
                         deliverables_by_status=deliverables_by_status, users=users, today=date.today())


@app.route('/clients/add', methods=['POST'])
@login_required
def add_client():
    name = request.form.get('name')
    industry = request.form.get('industry')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address', '')
    notes = request.form.get('notes', '')
    
    client = Client(name=name, industry=industry, email=email, phone=phone, address=address, notes=notes)
    db.session.add(client)
    db.session.commit()
    
    flash('Client added successfully!', 'success')
    
    if request.headers.get('HX-Request'):
        all_clients = Client.query.all()
        return render_template('partials/clients_list.html', clients=all_clients)
    
    return redirect(url_for('clients'))


@app.route('/clients/<int:client_id>/edit', methods=['POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    client.name = request.form.get('name', client.name)
    client.industry = request.form.get('industry', client.industry)
    client.email = request.form.get('email', client.email)
    client.phone = request.form.get('phone', client.phone)
    client.address = request.form.get('address', client.address)
    client.notes = request.form.get('notes', client.notes)
    
    db.session.commit()
    flash('Client updated successfully!', 'success')
    
    return redirect(url_for('client_detail', client_id=client_id))


def seed_database():
    if User.query.first() is None:
        admin = User(username='admin', role='Admin', full_name='Admin User', email='admin@agency.com')
        admin.set_password('admin')
        
        photographer1 = User(username='alex', role='Photographer', full_name='Alex Thompson', email='alex@agency.com')
        photographer1.set_password('alex123')
        
        photographer2 = User(username='jordan', role='Photographer', full_name='Jordan Smith', email='jordan@agency.com')
        photographer2.set_password('jordan123')
        
        db.session.add_all([admin, photographer1, photographer2])
        
        client1 = Client(name='TechCorp Inc.', industry='Technology', email='contact@techcorp.com', phone='555-0101')
        client2 = Client(name='Fashion House', industry='Fashion', email='info@fashionhouse.com', phone='555-0102')
        client3 = Client(name='Startup Labs', industry='Technology', email='hello@startuplabs.io', phone='555-0103')
        client4 = Client(name='Green Foods Co.', industry='Food & Beverage', email='marketing@greenfoods.com', phone='555-0104')
        
        db.session.add_all([client1, client2, client3, client4])
        db.session.commit()
        
        deal1 = Deal(client_id=1, title='Annual Report Photography', value=5000.0, cost_internal=1000.0, cost_external=500.0, stage='New', is_recurring=False, notes='Need high-quality corporate photos')
        deal2 = Deal(client_id=2, title='Spring Collection Shoot', value=12000.0, cost_internal=3000.0, cost_external=2000.0, stage='Proposal', is_recurring=False, notes='20 looks, studio and outdoor')
        deal3 = Deal(client_id=3, title='Monthly Content Package', value=3500.0, cost_internal=800.0, cost_external=200.0, stage='Negotiation', is_recurring=True, notes='Ongoing social media content')
        deal4 = Deal(client_id=1, title='Product Launch Event', value=8000.0, cost_internal=2000.0, cost_external=1000.0, stage='Won', is_recurring=False, notes='Launch event coverage')
        deal5 = Deal(client_id=4, title='Menu Photography', value=2500.0, cost_internal=500.0, cost_external=200.0, stage='New', is_recurring=False, notes='New menu items')
        
        db.session.add_all([deal1, deal2, deal3, deal4, deal5])
        db.session.commit()
        
        share1 = DealProfitShare(deal_id=4, user_id=2, percentage=30.0, flat_amount=0)
        share2 = DealProfitShare(deal_id=4, user_id=3, percentage=20.0, flat_amount=100)
        db.session.add_all([share1, share2])
        
        job1 = Job(client_id=1, deal_id=4, title='Product Launch Event Coverage', status='Active', start_date=date.today(), is_retainer=False)
        
        db.session.add(job1)
        db.session.commit()
        
        assignment1 = JobAssignment(job_id=1, user_id=2, role='Lead Photographer')
        assignment2 = JobAssignment(job_id=1, user_id=3, role='Assistant')
        db.session.add_all([assignment1, assignment2])
        
        today = date.today()
        deliverable1 = Deliverable(job_id=1, title='Event Coverage - 50 Photos', status='Shooting', assignee_id=2, due_date=today + timedelta(days=3))
        deliverable2 = Deliverable(job_id=1, title='Executive Headshots', status='To Do', assignee_id=3, due_date=today + timedelta(days=5))
        deliverable3 = Deliverable(job_id=1, title='Product Display Photos', status='Editing', assignee_id=2, due_date=today + timedelta(days=1))
        deliverable4 = Deliverable(job_id=1, title='Social Media Teasers', status='To Do', assignee_id=None, due_date=today + timedelta(days=7))
        deliverable5 = Deliverable(job_id=1, title='Press Kit Images', status='Review', assignee_id=2, due_date=today + timedelta(days=2))
        
        db.session.add_all([deliverable1, deliverable2, deliverable3, deliverable4, deliverable5])
        db.session.commit()
        
        print('Database seeded successfully!')


with app.app_context():
    db.create_all()
    seed_database()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
