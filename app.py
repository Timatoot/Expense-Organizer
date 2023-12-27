from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import get_db_connection

app = Flask(__name__)
app.secret_key = b'\xda\xea\xd1\xff\xf6\x16CBPu\xedfn\x10\x87\xf0pp{\xd1\x83_-\x05'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (int(user_id),)).fetchone()
    conn.close()
    if user:
        user_obj = User(id=user['id'], username=user['username'])
        return user_obj
    return None

class User(UserMixin):
    def __init__(self, id=None, username=None):
        self.id = id
        self.username = username

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            user_obj = User(id=user['id'], username=user['username'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            conn.close()
            return 'Username already exists. Please choose a different username.'
        else:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, generate_password_hash(password)))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    recent_expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (current_user.id,)).fetchall()
    conn.close()
    return render_template('dashboard.html', recent_expenses=recent_expenses)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        category_id = request.form.get('category_id')
        user_id = current_user.id
        conn = get_db_connection()
        conn.execute('INSERT INTO expenses (user_id, amount, description, category_id) VALUES (?, ?, ?, ?)',
                     (user_id, amount, description, category_id))
        conn.commit()
        conn.close()
        flash('Expense added successfully!')
        return redirect(url_for('dashboard'))
    else:
        conn = get_db_connection()
        categories = conn.execute('SELECT * FROM categories').fetchall()
        conn.close()
        return render_template('add_expense.html', categories=categories)

@app.route('/view_expenses', methods=['GET'])
@login_required
def view_expenses():
    category_id = request.args.get('category_id')
    conn = get_db_connection()
    
    params = [current_user.id]
    query = 'SELECT e.*, c.name AS category_name FROM expenses e LEFT JOIN categories c ON e.category_id = c.id WHERE e.user_id = ?'

    if category_id and category_id.isdigit():
        query += ' AND e.category_id = ?'
        params.append(int(category_id))

    expenses = conn.execute(query, params).fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    
    expenses = [dict(expense) for expense in expenses]
    categories = [dict(category) for category in categories]
    
    conn.close()
    
    return render_template('view_expenses.html', expenses=expenses, categories=categories, current_category_id=category_id)

@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        conn = get_db_connection()
        conn.execute('INSERT INTO groups (name, created_by) VALUES (?, ?)', (group_name, current_user.id))
        conn.commit()
        conn.close()
        flash('Group created successfully!')
        return redirect(url_for('dashboard'))
    return render_template('create_group.html')

@app.route('/invite_members', methods=['POST'])
@login_required
def invite_members():
    member_email = request.form['member_email']
    flash(f'An invite has been sent to {member_email}!')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
