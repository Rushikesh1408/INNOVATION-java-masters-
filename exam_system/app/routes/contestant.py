from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from ..db import Database
from datetime import datetime
import json

contestant_bp = Blueprint('contestant', __name__)

@contestant_bp.route('/')
def home():
    tests = Database.execute_query(
        "SELECT id, title, description, time_limit_minutes FROM tests WHERE is_active = 1",
        fetch='all'
    )
    return render_template('contestant/index.html', tests=tests)

@contestant_bp.route('/register', methods=['POST'])
def register():
    email = request.form.get('email', '').strip().lower()
    full_name = request.form.get('full_name', '').strip()
    test_id = request.form.get('test_id')

    if not email or not full_name or not test_id:
        flash('All fields are required.')
        return redirect(url_for('contestant.home'))

    # Create contestant if not exists
    contestant = Database.execute_query(
        "SELECT email FROM contestants WHERE email = %s", (email,), fetch='one'
    )
    if not contestant:
        Database.execute_query(
            "INSERT INTO contestants (email, full_name) VALUES (%s, %s)", (email, full_name)
        )

    # Check for existing attempt (one email = one attempt per test)
    existing_attempt = Database.execute_query(
        "SELECT id FROM attempts WHERE test_id = %s AND contestant_email = %s",
        (test_id, email), fetch='one'
    )
    if existing_attempt:
        flash('You have already attempted this test. Only one attempt is allowed.')
        return redirect(url_for('contestant.home'))

    session['contestant_email'] = email
    session['contestant_name'] = full_name
    return redirect(url_for('contestant.rules', test_id=test_id))

@contestant_bp.route('/rules/<int:test_id>')
def rules(test_id):
    if 'contestant_email' not in session:
        return redirect(url_for('contestant.home'))
    test = Database.execute_query(
        "SELECT id, title, description, time_limit_minutes FROM tests WHERE id = %s",
        (test_id,), fetch='one'
    )
    if not test:
        flash('Examination not found.')
        return redirect(url_for('contestant.home'))
    return render_template('contestant/rules.html', test=test)

@contestant_bp.route('/start-test/<int:test_id>', methods=['POST'])
def start_test(test_id):
    email = session.get('contestant_email')
    if not email:
        return redirect(url_for('contestant.home'))

    # Check for existing attempt to allow resuming or block double-starts
    existing = Database.execute_query(
        "SELECT id, submitted FROM attempts WHERE test_id = %s AND contestant_email = %s",
        (test_id, email), fetch='one'
    )

    if existing:
        if existing[1]: # submitted == 1
            flash('You have already completed this examination.')
            return redirect(url_for('contestant.home'))
        attempt_id = existing[0]
    else:
        attempt_id = Database.execute_insert(
            "INSERT INTO attempts (test_id, contestant_email, start_time) VALUES (%s, %s, %s)",
            (test_id, email, datetime.now().isoformat())
        )

    session['current_attempt_id'] = attempt_id
    session['current_test_id'] = test_id
    return redirect(url_for('contestant.exam', test_id=test_id))

@contestant_bp.route('/exam/<int:test_id>')
def exam(test_id):
    if 'current_attempt_id' not in session:
        return redirect(url_for('contestant.home'))

    test = Database.execute_query(
        "SELECT id, title, description, time_limit_minutes FROM tests WHERE id = %s",
        (test_id,), fetch='one'
    )
    questions_raw = Database.execute_query(
        "SELECT id, question_text, option_1, option_2, option_3, option_4 FROM questions WHERE test_id = %s ORDER BY id",
        (test_id,), fetch='all'
    )

    questions_list = []
    for q in questions_raw:
        questions_list.append({
            'id': q[0],
            'question_text': q[1],
            'option_1': q[2],
            'option_2': q[3],
            'option_3': q[4],
            'option_4': q[5]
        })

    if not test:
        flash('Examination instance not found.')
        return redirect(url_for('contestant.home'))
    return render_template('contestant/exam.html', test=test, questions=questions_list)

@contestant_bp.route('/submit-answer', methods=['POST'])
def submit_answer():
    attempt_id = session.get('current_attempt_id')
    if not attempt_id:
        return jsonify({'error': 'No active session'}), 401

    data = request.get_json()
    q_id = data.get('question_id')
    option = data.get('selected_option')   # 1-based int (1=A, 2=B, 3=C, 4=D)
    time_taken = data.get('time_taken', 0)

    # Map letter options A-D to 1-4 if needed
    if isinstance(option, str):
        option = {'A': 1, 'B': 2, 'C': 3, 'D': 4}.get(option.upper(), 1)

    # Upsert response (INSERT or REPLACE for SQLite)
    Database.execute_query(
        "INSERT OR REPLACE INTO responses (attempt_id, question_id, selected_option, time_taken_seconds) VALUES (%s, %s, %s, %s)",
        (attempt_id, q_id, option, time_taken)
    )
    return jsonify({'success': True})

@contestant_bp.route('/anti-cheat-event', methods=['POST'])
def anti_cheat_event():
    attempt_id = session.get('current_attempt_id')
    if not attempt_id:
        return jsonify({'error': 'No active session'}), 401

    data = request.get_json()
    event_type = data.get('event', 'unknown')

    # Append to anti_cheat_flags JSON
    current = Database.execute_query(
        "SELECT anti_cheat_flags FROM attempts WHERE id = %s", (attempt_id,), fetch='one'
    )
    flags = json.loads(current[0]) if current and current[0] else []
    flags.append({'event': event_type, 'time': datetime.now().isoformat()})

    Database.execute_query(
        "UPDATE attempts SET anti_cheat_flags = %s WHERE id = %s",
        (json.dumps(flags), attempt_id)
    )
    return jsonify({'success': True, 'total_flags': len(flags)})

@contestant_bp.route('/submit-test', methods=['POST'])
def submit_test():
    attempt_id = session.get('current_attempt_id')
    if not attempt_id:
        return redirect(url_for('contestant.home'))

    # Get all responses and calculate score
    results = Database.execute_query(
        """SELECT q.correct_option, r.selected_option
           FROM responses r
           JOIN questions q ON r.question_id = q.id
           WHERE r.attempt_id = %s""",
        (attempt_id,), fetch='all'
    )

    score = sum(1 for correct, selected in results if correct == selected)

    # Calculate total time
    attempt = Database.execute_query(
        "SELECT start_time FROM attempts WHERE id = %s", (attempt_id,), fetch='one'
    )
    total_time = 0
    if attempt and attempt[0]:
        try:
            start = datetime.fromisoformat(attempt[0])
            total_time = int((datetime.now() - start).total_seconds())
        except Exception:
            pass

    Database.execute_query(
        "UPDATE attempts SET end_time = %s, score = %s, total_time_taken = %s, submitted = 1, status = 'COMPLETED' WHERE id = %s",
        (datetime.now().isoformat(), score, total_time, attempt_id)
    )

    session.pop('current_attempt_id', None)
    session.pop('current_test_id', None)
    session['last_score'] = score
    return redirect(url_for('contestant.thank_you'))

@contestant_bp.route('/thank-you')
def thank_you():
    score = session.pop('last_score', None)
    return render_template('contestant/thank_you.html', score=score)
