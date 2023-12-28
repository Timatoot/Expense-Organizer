import io
import base64
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.database import get_db_connection

expense_blueprint = Blueprint('expense', __name__)

@expense_blueprint.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    user_id = current_user.id
    
    current_month_expenses = conn.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')",
        (user_id,)).fetchone()[0] or 0

    last_month_expenses = conn.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', '-1 month')",
        (user_id,)).fetchone()[0] or 0

    average_12_months_expenses = conn.execute(
        "SELECT AVG(monthly_total) FROM (SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as monthly_total FROM expenses WHERE user_id = ? AND created_at >= date('now', '-12 months') GROUP BY month)",
        (user_id,)).fetchone()[0] or 0

    month_difference = current_month_expenses - last_month_expenses

    pie_data = conn.execute("""
        SELECT c.name AS category_name, SUM(e.amount) AS amount
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.created_at) = strftime('%Y-%m', 'now')
        GROUP BY c.name
    """, (user_id,)).fetchall()

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.pie(
        [data['amount'] for data in pie_data],
        labels=[data['category_name'] for data in pie_data],
        autopct='%1.1f%%'
    )
    axis.axis('equal')

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    pie_image = base64.b64encode(buf.getbuffer()).decode("ascii")

    buf.close()
    plt.close(fig)

    recent_expenses = conn.execute(
        'SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user_id,)).fetchall()

    conn.close()

    return render_template('dashboard.html',
                           recent_expenses=recent_expenses,
                           current_month_expenses=current_month_expenses,
                           month_difference=month_difference,
                           average_12_months_expenses=average_12_months_expenses,
                           pie_image=pie_image)

@expense_blueprint.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        category_id = request.form.get('category_id')
        user_id = current_user.id
        if float(amount) < 0:
            flash('Amount cannot be negative.', 'error')
            return render_template('add_expense.html')

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

@expense_blueprint.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    conn = get_db_connection()
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        category_id = request.form.get('category_id')
        if float(amount) < 0:
            expense = conn.execute('SELECT * FROM expenses WHERE id = ? AND user_id = ?', (expense_id, current_user.id)).fetchone()
            categories = conn.execute('SELECT * FROM categories').fetchall()
            conn.close()
            flash('Amount cannot be negative.', 'error')
            return render_template('edit_expense.html', expense=expense, categories=categories)

        conn.execute('UPDATE expenses SET amount = ?, description = ?, category_id = ? WHERE id = ? AND user_id = ?',
                     (amount, description, category_id, expense_id, current_user.id))
        conn.commit()
        flash('Expense updated successfully!')
        return redirect(url_for('expense.view_expenses'))

    expense = conn.execute('SELECT * FROM expenses WHERE id = ? AND user_id = ?', (expense_id, current_user.id)).fetchone()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    
    if not expense:
        flash('Expense not found.')
        return redirect(url_for('expense.view_expenses'))
    
    return render_template('edit_expense.html', expense=expense, categories=categories)

@expense_blueprint.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (expense_id, current_user.id))
    conn.commit()
    conn.close()
    flash('Expense deleted successfully.')
    return redirect(url_for('expense.view_expenses'))

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