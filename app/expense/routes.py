from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.database import get_db_connection

expense_blueprint = Blueprint('expense', __name__)

@expense_blueprint.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    recent_expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (current_user.id,)).fetchall()
    conn.close()
    return render_template('dashboard.html', recent_expenses=recent_expenses)

@expense_blueprint.route('/add_expense', methods=['GET', 'POST'])
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
        return redirect(url_for('expense.dashboard'))
    else:
        conn = get_db_connection()
        categories = conn.execute('SELECT * FROM categories').fetchall()
        conn.close()
        return render_template('add_expense.html', categories=categories)

@expense_blueprint.route('/view_expenses', methods=['GET'])
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


@expense_blueprint.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        conn = get_db_connection()
        conn.execute('INSERT INTO groups (name, created_by) VALUES (?, ?)', (group_name, current_user.id))
        conn.commit()
        conn.close()
        flash('Group created successfully!')
        return redirect(url_for('expense.dashboard'))
    return render_template('create_group.html')

@expense_blueprint.route('/invite_members', methods=['POST'])
@login_required
def invite_members():
    member_email = request.form['member_email']
    flash(f'An invite has been sent to {member_email}!')
    return redirect(url_for('expense.dashboard'))