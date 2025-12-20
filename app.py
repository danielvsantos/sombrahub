import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Photographer')
    
    deliverables = db.relationship('Deliverable', backref='assignee', lazy=True)
    
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
    
    deals = db.relationship('Deal', backref='client', lazy=True)
    jobs = db.relationship('Job', backref='client', lazy=True)


class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Float, default=0.0)
    stage = db.Column(db.String(20), default='New')
    is_recurring = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    jobs = db.relationship('Job', backref='deal', lazy=True)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=True)
    status = db.Column(db.String(20), default='Active')
    start_date = db.Column(db.Date, default=date.today)
    is_retainer = db.Column(db.Boolean, default=False)
    
    deliverables = db.relationship('Deliverable', backref='job', lazy=True)


class Deliverable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
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
    
    return render_template('dashboard.html', 
                         total_deals=total_deals,
                         active_jobs=active_jobs,
                         pending_deliverables=pending_deliverables,
                         recent_deals=recent_deals,
                         upcoming_deliverables=upcoming_deliverables,
                         won_deals_value=won_deals_value,
                         today=date.today())


@app.route('/deals')
@login_required
def deals():
    stages = ['New', 'Proposal', 'Negotiation', 'Won', 'Lost']
    deals_by_stage = {}
    for stage in stages:
        deals_by_stage[stage] = Deal.query.filter_by(stage=stage).all()
    
    clients = Client.query.all()
    return render_template('deals.html', deals_by_stage=deals_by_stage, stages=stages, clients=clients)


@app.route('/deals/add', methods=['POST'])
@login_required
def add_deal():
    client_id = request.form.get('client_id')
    title = request.form.get('title')
    value = float(request.form.get('value', 0))
    stage = request.form.get('stage', 'New')
    is_recurring = request.form.get('is_recurring') == 'on'
    notes = request.form.get('notes', '')
    
    deal = Deal(
        client_id=client_id,
        title=title,
        value=value,
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


@app.route('/production')
@login_required
def production():
    search = request.args.get('search', '')
    
    if search:
        jobs = Job.query.join(Client).filter(
            Job.status == 'Active',
            Client.name.ilike(f'%{search}%')
        ).all()
    else:
        jobs = Job.query.filter_by(status='Active').all()
    
    users = User.query.all()
    return render_template('production.html', jobs=jobs, users=users, search=search, today=date.today())


@app.route('/jobs/<int:job_id>/add-deliverable', methods=['POST'])
@login_required
def add_deliverable(job_id):
    job = Job.query.get_or_404(job_id)
    
    title = request.form.get('title')
    assignee_id = request.form.get('assignee_id')
    due_date_str = request.form.get('due_date')
    
    due_date = None
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    
    deliverable = Deliverable(
        job_id=job_id,
        title=title,
        assignee_id=assignee_id if assignee_id else None,
        due_date=due_date,
        status='To Do'
    )
    db.session.add(deliverable)
    db.session.commit()
    
    flash('Deliverable added successfully!', 'success')
    
    if request.headers.get('HX-Request'):
        users = User.query.all()
        return render_template('partials/deliverables_table.html', job=job, users=users)
    
    return redirect(url_for('production'))


@app.route('/deliverables/<int:deliverable_id>/update-status', methods=['POST'])
@login_required
def update_deliverable_status(deliverable_id):
    deliverable = Deliverable.query.get_or_404(deliverable_id)
    new_status = request.form.get('status')
    
    deliverable.status = new_status
    db.session.commit()
    
    if request.headers.get('HX-Request'):
        return render_template('partials/status_badge.html', deliverable=deliverable)
    
    return redirect(url_for('production'))


@app.route('/deliverables/<int:deliverable_id>/delete', methods=['POST'])
@login_required
def delete_deliverable(deliverable_id):
    deliverable = Deliverable.query.get_or_404(deliverable_id)
    job = deliverable.job
    
    db.session.delete(deliverable)
    db.session.commit()
    
    flash('Deliverable deleted.', 'info')
    
    if request.headers.get('HX-Request'):
        users = User.query.all()
        return render_template('partials/deliverables_table.html', job=job, users=users)
    
    return redirect(url_for('production'))


@app.route('/jobs/<int:job_id>/complete', methods=['POST'])
@login_required
def complete_job(job_id):
    job = Job.query.get_or_404(job_id)
    job.status = 'Completed'
    db.session.commit()
    
    flash('Job marked as completed!', 'success')
    return redirect(url_for('production'))


@app.route('/clients')
@login_required
def clients():
    all_clients = Client.query.all()
    return render_template('clients.html', clients=all_clients)


@app.route('/clients/add', methods=['POST'])
@login_required
def add_client():
    name = request.form.get('name')
    industry = request.form.get('industry')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    client = Client(name=name, industry=industry, email=email, phone=phone)
    db.session.add(client)
    db.session.commit()
    
    flash('Client added successfully!', 'success')
    
    if request.headers.get('HX-Request'):
        all_clients = Client.query.all()
        return render_template('partials/clients_list.html', clients=all_clients)
    
    return redirect(url_for('clients'))


def seed_database():
    if User.query.first() is None:
        admin = User(username='admin', role='Admin')
        admin.set_password('admin')
        
        photographer1 = User(username='alex', role='Photographer')
        photographer1.set_password('alex123')
        
        photographer2 = User(username='jordan', role='Photographer')
        photographer2.set_password('jordan123')
        
        db.session.add_all([admin, photographer1, photographer2])
        
        client1 = Client(name='TechCorp Inc.', industry='Technology', email='contact@techcorp.com', phone='555-0101')
        client2 = Client(name='Fashion House', industry='Fashion', email='info@fashionhouse.com', phone='555-0102')
        client3 = Client(name='Startup Labs', industry='Technology', email='hello@startuplabs.io', phone='555-0103')
        client4 = Client(name='Green Foods Co.', industry='Food & Beverage', email='marketing@greenfoods.com', phone='555-0104')
        
        db.session.add_all([client1, client2, client3, client4])
        db.session.commit()
        
        deal1 = Deal(client_id=1, title='Annual Report Photography', value=5000.0, stage='New', is_recurring=False, notes='Need high-quality corporate photos')
        deal2 = Deal(client_id=2, title='Spring Collection Shoot', value=12000.0, stage='Proposal', is_recurring=False, notes='20 looks, studio and outdoor')
        deal3 = Deal(client_id=3, title='Monthly Content Package', value=3500.0, stage='Negotiation', is_recurring=True, notes='Ongoing social media content')
        deal4 = Deal(client_id=1, title='Product Launch Event', value=8000.0, stage='Won', is_recurring=False, notes='Launch event coverage')
        deal5 = Deal(client_id=4, title='Menu Photography', value=2500.0, stage='New', is_recurring=False, notes='New menu items')
        
        db.session.add_all([deal1, deal2, deal3, deal4, deal5])
        db.session.commit()
        
        job1 = Job(client_id=1, deal_id=4, status='Active', start_date=date.today(), is_retainer=False)
        
        db.session.add(job1)
        db.session.commit()
        
        deliverable1 = Deliverable(job_id=1, title='Event Coverage - 50 Photos', status='Shooting', assignee_id=2, due_date=date(2024, 12, 28))
        deliverable2 = Deliverable(job_id=1, title='Executive Headshots', status='To Do', assignee_id=3, due_date=date(2024, 12, 30))
        deliverable3 = Deliverable(job_id=1, title='Product Display Photos', status='Editing', assignee_id=2, due_date=date(2024, 12, 25))
        
        db.session.add_all([deliverable1, deliverable2, deliverable3])
        db.session.commit()
        
        print('Database seeded successfully!')


with app.app_context():
    db.create_all()
    seed_database()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
