from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from ..db import Database
from flask_bcrypt import check_password_hash
import json

admin_bp = Blueprint('admin', __name__)

def admin_required():
    return 'admin_id' in session

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if admin_required():
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = Database.execute_query(
            "SELECT id, username, password_hash FROM admins WHERE username = %s",
            (username,), fetch='one'
        )

        if user and check_password_hash(user[2], password):
            session['admin_id'] = user[0]
            session['admin_username'] = user[1]
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.')

    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
def dashboard():
    if not admin_required():
        return redirect(url_for('admin.login'))

    tests = Database.execute_query(
        """SELECT t.id, t.title, t.time_limit_minutes, t.is_active,
                  (SELECT COUNT(*) FROM questions q WHERE q.test_id = t.id) as q_count,
                  (SELECT COUNT(*) FROM attempts a WHERE a.test_id = t.id AND a.submitted = 1) as attempt_count
           FROM tests t ORDER BY t.created_at DESC""",
        fetch='all'
    )
    return render_template('admin/dashboard.html', tests=tests,
                           admin_username=session.get('admin_username'))

@admin_bp.route('/create-test', methods=['POST'])
def create_test():
    if not admin_required():
        return redirect(url_for('admin.login'))

    title = request.form.get('title', '').strip()
    time_limit = request.form.get('time_limit', 30)
    description = request.form.get('description', '').strip()

    if not title:
        flash('Test title is required.')
        return redirect(url_for('admin.dashboard'))

    test_id = Database.execute_insert(
        "INSERT INTO tests (title, description, time_limit_minutes) VALUES (%s, %s, %s)",
        (title, description, int(time_limit))
    )
    return redirect(url_for('admin.test_details', test_id=test_id))

@admin_bp.route('/test/<int:test_id>')
def test_details(test_id):
    if not admin_required():
        return redirect(url_for('admin.login'))

    test = Database.execute_query(
        "SELECT id, title, description, time_limit_minutes, is_active FROM tests WHERE id = %s",
        (test_id,), fetch='one'
    )
    questions = Database.execute_query(
        "SELECT id, question_text, option_1, option_2, option_3, option_4, correct_option FROM questions WHERE test_id = %s ORDER BY id",
        (test_id,), fetch='all'
    )
    if not test:
        flash('Test configuration not found.')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/test_details.html', test=test, questions=questions)

@admin_bp.route('/add-question', methods=['POST'])
def add_question():
    if not admin_required():
        return redirect(url_for('admin.login'))

    test_id = request.form.get('test_id')
    question_text = request.form.get('question_text', '').strip()
    opt1 = request.form.get('option_1', '').strip()
    opt2 = request.form.get('option_2', '').strip()
    opt3 = request.form.get('option_3', '').strip()
    opt4 = request.form.get('option_4', '').strip()
    correct = request.form.get('correct_option')

    if not all([test_id, question_text, opt1, opt2, opt3, opt4, correct]):
        flash('All question fields are required.')
        return redirect(url_for('admin.test_details', test_id=test_id or 0))

    Database.execute_insert(
        "INSERT INTO questions (test_id, question_text, option_1, option_2, option_3, option_4, correct_option) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (test_id, question_text, opt1, opt2, opt3, opt4, int(correct))
    )
    return redirect(url_for('admin.test_details', test_id=test_id))

@admin_bp.route('/delete-question/<int:q_id>', methods=['POST'])
def delete_question(q_id):
    if not admin_required():
        return redirect(url_for('admin.login'))
    q = Database.execute_query("SELECT test_id FROM questions WHERE id = %s", (q_id,), fetch='one')
    Database.execute_query("DELETE FROM questions WHERE id = %s", (q_id,))
    if q:
        return redirect(url_for('admin.test_details', test_id=q[0]))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/toggle-test/<int:test_id>', methods=['POST'])
def toggle_test(test_id):
    if not admin_required():
        return redirect(url_for('admin.login'))
    test = Database.execute_query("SELECT is_active FROM tests WHERE id = %s", (test_id,), fetch='one')
    if test:
        new_status = 0 if test[0] else 1
        Database.execute_query("UPDATE tests SET is_active = %s WHERE id = %s", (new_status, test_id))
    
    # Return to previous page if it exists and is an admin page
    ref = request.referrer
    if ref and ('admin' in ref):
        return redirect(ref)
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete-test/<int:test_id>', methods=['POST'])
def delete_test(test_id):
    if not admin_required():
        return redirect(url_for('admin.login'))
    # Delete responses → attempts → questions → test (cascade order)
    Database.execute_query(
        "DELETE FROM responses WHERE attempt_id IN (SELECT id FROM attempts WHERE test_id = %s)", (test_id,)
    )
    Database.execute_query("DELETE FROM attempts WHERE test_id = %s", (test_id,))
    Database.execute_query("DELETE FROM questions WHERE test_id = %s", (test_id,))
    Database.execute_query("DELETE FROM tests WHERE id = %s", (test_id,))
    flash(f'Test deleted successfully.')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/leaderboard/<int:test_id>')
def leaderboard(test_id):
    if not admin_required():
        return redirect(url_for('admin.login'))

    test = Database.execute_query(
        "SELECT id, title FROM tests WHERE id = %s", (test_id,), fetch='one'
    )
    ranks = Database.execute_query(
        """SELECT c.full_name, c.email, a.score, a.total_time_taken, a.anti_cheat_flags
           FROM attempts a
           JOIN contestants c ON a.contestant_email = c.email
           WHERE a.test_id = %s AND a.submitted = 1
           ORDER BY a.score DESC, a.total_time_taken ASC""",
        (test_id,), fetch='all'
    )
    if not test:
        flash('Test node not found.')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/leaderboard.html', test=test, rankings=ranks)

@admin_bp.route('/analytics/<int:test_id>')
def analytics(test_id):
    if not admin_required():
        return redirect(url_for('admin.login'))

    test = Database.execute_query(
        "SELECT id, title FROM tests WHERE id = %s", (test_id,), fetch='one'
    )
    stats = Database.execute_query(
        "SELECT AVG(score), AVG(total_time_taken), COUNT(*) FROM attempts WHERE test_id = %s AND submitted = 1",
        (test_id,), fetch='one'
    )
    q_stats = Database.execute_query(
        """SELECT q.id, q.question_text, AVG(r.time_taken_seconds) as avg_time
           FROM questions q
           LEFT JOIN responses r ON q.id = r.question_id
           WHERE q.test_id = %s
           GROUP BY q.id, q.question_text""",
        (test_id,), fetch='all'
    )
    rankings = Database.execute_query(
        """SELECT a.id, c.full_name, a.contestant_email, a.score, a.total_time_taken 
           FROM attempts a 
           JOIN contestants c ON a.contestant_email = c.email
           WHERE a.test_id = %s AND a.submitted = 1 
           ORDER BY a.score DESC, a.total_time_taken ASC""",
        (test_id,), fetch='all'
    )
    if not test:
        flash('Analytical node not found.')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/analytics.html', test=test, stats=stats,
                           q_stats=q_stats, rankings=rankings, test_id=test_id)
