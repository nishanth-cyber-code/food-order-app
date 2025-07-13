from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# ---------------------- DATABASE MODELS ----------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'manager' or 'customer'

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    item_code = db.Column(db.String(10), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.Integer, nullable=False)
    item_code = db.Column(db.String(10), nullable=False)
    customer_name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)

# ---------------------- HELPER FUNCTIONS ----------------------

def get_next_order_no():
    today = date.today().strftime('%Y-%m-%d')
    last_order = Order.query.filter_by(date=today).order_by(Order.order_no.desc()).first()
    return 1 if not last_order else last_order.order_no + 1

# ---------------------- ROUTES ----------------------

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    user = User.query.filter_by(username=username, password=password, role=role).first()
    if user:
        session['user'] = username
        session['role'] = role
        return redirect(url_for(f'{role}_dashboard'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('home'))

@app.route('/customer_dashboard')
def customer_dashboard():
    if session.get('role') != 'customer':
        return redirect(url_for('home'))
    today = date.today().strftime('%Y-%m-%d')
    menu = Menu.query.filter_by(date=today).all()
    return render_template('customer_dashboard.html', menu=menu)

@app.route('/place_order', methods=['POST'])
def place_order():
    item_code = request.form['item_code']
    customer_name = request.form['customer_name']
    today = date.today().strftime('%Y-%m-%d')
    item = Menu.query.filter_by(date=today, item_code=item_code).first()
    if item:
        order_no = get_next_order_no()
        new_order = Order(order_no=order_no, item_code=item_code,
                          customer_name=customer_name, date=today, total_price=item.price)
        db.session.add(new_order)
        db.session.commit()
        return render_template('bill.html', order=new_order, item=item)
    else:
        flash("Item not found for today")
        return redirect(url_for('customer_dashboard'))

@app.route('/manager_dashboard')
def manager_dashboard():
    if session.get('role') != 'manager':
        return redirect(url_for('home'))
    today = date.today().strftime('%Y-%m-%d')
    menu = Menu.query.filter_by(date=today).all()
    orders = Order.query.filter_by(date=today).all()
    return render_template('manager_dashboard.html', menu=menu, orders=orders)

@app.route('/add_menu', methods=['POST'])
def add_menu():
    item_code = request.form['item_code']
    item_name = request.form['item_name']
    price = int(request.form['price'])
    today = date.today().strftime('%Y-%m-%d')
    new_item = Menu(date=today, item_code=item_code, item_name=item_name, price=price)
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('manager_dashboard'))

@app.route('/delete_order/<int:id>')
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('manager_dashboard'))

@app.route('/sales_report', methods=['POST'])
def sales_report():
    report_date = request.form['report_date']
    orders = Order.query.filter_by(date=report_date).all()
    total = sum(order.total_price for order in orders)
    return render_template('sales_report.html', orders=orders, total=total, report_date=report_date)

# ---------------------- RUN FLASK APP ----------------------

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        with app.app_context():
            db.create_all()
            # Add default users (manager and customer) if needed
            if not User.query.first():
                db.session.add(User(username='admin', password='admin', role='manager'))
                db.session.add(User(username='cust', password='cust', role='customer'))
                db.session.commit()
    app.run(debug=True)
