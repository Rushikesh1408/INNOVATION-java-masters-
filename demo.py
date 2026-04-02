#!/usr/bin/env python
"""
End-to-End Demo Script for Java Masters Exam Engine
Demonstrates:
1. Admin creates exam with quiz + coding problems
2. User registers and takes quiz
3. User submits Java code for problem
4. System evaluates and shows results
5. Leaderboards generated
"""

import json
import time
from datetime import datetime

import requests

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def demo():
    """Run full end-to-end demo"""
    
    print_section("JAVA MASTERS EXAM ENGINE - END-TO-END DEMO")
    
    # Step 1: Admin Login
    print_section("STEP 1: Admin Authentication")
    print("Logging in as admin...")
    admin_login = requests.post(
        f"{BASE_URL}/auth/admin/login",
        json={"username": "admin", "password": "admin123"}
    )
    if admin_login.status_code != 200:
        print(f"❌ Admin login failed: {admin_login.text}")
        return
    
    admin_token = admin_login.json()["access_token"]
    print(f"✅ Admin logged in")
    print(f"   Token: {admin_token[:20]}...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Step 2: Create Exam
    print_section("STEP 2: Create Exam")
    print("Creating 'Java Fundamentals' exam...")
    exam_data = {
        "title": "Java Fundamentals",
        "time_limit": 60,
        "positive_mark": 4,
        "negative_mark": 1,
        "rules": "No plagiarism allowed"
    }
    exam_response = requests.post(
        f"{BASE_URL}/exams",
        json=exam_data,
        headers=headers
    )
    if exam_response.status_code != 200:
        print(f"❌ Exam creation failed: {exam_response.text}")
        return
    
    exam = exam_response.json()
    exam_id = exam["id"]
    print(f"✅ Exam created")
    print(f"   ID: {exam_id}")
    print(f"   Title: {exam['title']}")
    print(f"   Time: {exam['time_limit']}min")
    
    # Step 3: Add MCQ Questions
    print_section("STEP 3: Add MCQ Questions to Exam")
    questions = [
        {
            "question_text": "What is the output of factorial(5)?",
            "option_1": "120",
            "option_2": "100",
            "option_3": "25",
            "option_4": "5",
            "correct_option": 1
        },
        {
            "question_text": "Which method is used to find the length of a string?",
            "option_1": "getLength()",
            "option_2": "length()",
            "option_3": "size()",
            "option_4": "len()",
            "correct_option": 2
        }
    ]
    question_ids: list[int] = []
    
    for i, q in enumerate(questions, 1):
        print(f"Adding question {i}: {q['question_text'][:40]}...")
        q_response = requests.post(
            f"{BASE_URL}/exams/{exam_id}/questions",
            json=q,
            headers=headers
        )
        if q_response.status_code == 200:
            created_question = q_response.json()
            created_id = created_question.get("id")
            if isinstance(created_id, int):
                question_ids.append(created_id)
            print(f"   ✅ Added")
        else:
            print(f"   ❌ Failed: {q_response.text}")

    if len(question_ids) < len(questions):
        print("❌ Could not capture all created question IDs")
        return
    
    # Step 4: Create Coding Problems
    print_section("STEP 4: Create Coding Problems")
    print("Creating 'Factorial Calculator' problem...")
    
    coding_problem = {
        "title": "Factorial Calculator",
        "description": "Write a program to calculate the factorial of a given number N.\n\nInput: A single integer N\nOutput: The factorial of N\n\nExample:\nInput: 5\nOutput: 120",
        "difficulty": "easy",
        "time_limit_seconds": 2,
        "memory_limit_mb": 256,
        "starter_code": "public class Main {\n    public static void main(String[] args) {\n        // Read input from args[0]\n        int n = Integer.parseInt(args[0]);\n        // Your code here\n    }\n}",
        "visible_test_cases": [
            {"input": "5", "expected": "120"},
            {"input": "3", "expected": "6"}
        ],
        "hidden_test_cases": [
            {"input": "0", "expected": "1"},
            {"input": "10", "expected": "3628800"}
        ]
    }
    
    prob_response = requests.post(
        f"{BASE_URL}/coding/problems/{exam_id}",
        json=coding_problem,
        headers=headers
    )
    if prob_response.status_code != 200:
        print(f"❌ Problem creation failed: {prob_response.text}")
        return
    
    problem = prob_response.json()
    problem_id = problem["id"]
    print(f"✅ Coding problem created")
    print(f"   ID: {problem_id}")
    print(f"   Title: {problem['title']}")
    print(f"   Difficulty: {problem['difficulty']}")
    print(f"   Time limit: {problem['time_limit_seconds']}s")
    
    # Step 5: User Registration
    print_section("STEP 5: User Registration & Quiz")
    print("Registering contestant...")
    user_data = {
        "name": "John Developer",
        "email": "john@example.com"
    }
    user_response = requests.post(
        f"{BASE_URL}/contestants/register",
        json=user_data
    )
    if user_response.status_code != 200:
        print(f"❌ Registration failed: {user_response.text}")
        return
    
    user = user_response.json()
    user_id = user["id"]
    print(f"✅ User registered")
    print(f"   ID: {user_id}")
    print(f"   Name: {user['name']}")
    print(f"   Email: {user['email']}")
    
    # Step 6: Start Exam
    print_section("STEP 6: Start Quiz")
    start_response = requests.post(
        f"{BASE_URL}/contestants/start-exam",
        json={"exam_id": exam_id}
    )
    if start_response.status_code != 200:
        print(f"❌ Exam start failed: {start_response.text}")
        return
    
    session = start_response.json()
    session_id = session["session_id"]
    print(f"✅ Quiz started")
    print(f"   Session ID: {session_id}")
    
    # Step 7: Submit Answers
    print_section("STEP 7: Submit Quiz Answers")
    print("Submitting answers...")
    answers = [
        {"question_id": question_ids[0], "selected_option": 1},  # Correct
        {"question_id": question_ids[1], "selected_option": 2},  # Correct
    ]
    
    for ans in answers:
        print(f"Submitting answer for Q{ans['question_id']}...")
        submit_response = requests.post(
            f"{BASE_URL}/contestants/submit-answer",
            json={"session_id": session_id, **ans}
        )
        if submit_response.status_code == 200:
            print(f"   ✅ Submitted")
        else:
            print(f"   ❌ Failed: {submit_response.text}")
    
    # Step 8: Finish Quiz
    print_section("STEP 8: Finish Quiz")
    finish_response = requests.post(
        f"{BASE_URL}/contestants/finish/{session_id}"
    )
    if finish_response.status_code == 200:
        result = finish_response.json()
        print(f"✅ Quiz finished!")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Accuracy: {result.get('accuracy', 'N/A')}%")
    else:
        print(f"❌ Finish failed: {finish_response.text}")
    
    # Step 9: Submit Code for Coding Problem
    print_section("STEP 9: Submit Code to Coding Problem")
    
    java_code = """public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        long result = factorial(n);
        System.out.println(result);
    }
    
    static long factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }
}"""
    
    print("Submitting Java code...")
    print("Code:")
    print(java_code[:100] + "...")
    
    submit_code_response = requests.post(
        f"{BASE_URL}/coding/submit/{problem_id}",
        json={"code": java_code}
    )
    
    if submit_code_response.status_code != 200:
        print(f"❌ Code submission failed: {submit_code_response.text}")
        return
    
    submission = submit_code_response.json()
    submission_id = submission["submission_id"]
    print(f"✅ Code submitted")
    print(f"   Submission ID: {submission_id}")
    print(f"   Status: {submission.get('status')}")
    
    # Step 10: Wait for Evaluation
    print_section("STEP 10: Wait for Async Evaluation")
    print("Polling for evaluation results (up to 30s)...")
    
    evaluation_completed = False
    for attempt in range(30):
        time.sleep(1)
        status_response = requests.get(
            f"{BASE_URL}/coding/submissions/{submission_id}"
        )
        
        if status_response.status_code != 200:
            print(f"❌ Status check failed: {status_response.text}")
            break
        
        submission_status = status_response.json()
        current_status = submission_status.get("status", "unknown")
        
        if current_status not in ["pending"]:
            evaluation_completed = True
            print(f"✅ Evaluation complete!")
            print(f"\nResults:")
            print(f"   Status: {submission_status['status']}")
            print(f"   Score: {submission_status.get('score', 0)}/100")
            print(f"   Visible Tests: {submission_status.get('passed_visible', 0)}/{submission_status.get('total_visible', 0)} passed")
            print(f"   Hidden Tests: {submission_status.get('passed_hidden', 0)}/{submission_status.get('total_hidden', 0)} passed")
            print(f"   Execution Time: {submission_status.get('execution_time_ms', 0)}ms")
            if submission_status.get('error'):
                print(f"   Error: {submission_status['error'][:100]}")
            break
        
        print(f"   Waiting... {attempt + 1}s (status: {current_status})")

    if not evaluation_completed:
        print(
            f"⚠️ Evaluation polling timed out for submission {submission_id}. "
            "Check worker logs and retry status lookup later."
        )
    
    # Step 11: View Leaderboards
    print_section("STEP 11: View Leaderboards")
    
    print("Quiz Leaderboard:")
    quiz_resp = requests.get(f"{BASE_URL}/contestants/leaderboard/{exam_id}")
    if quiz_resp.ok:
        quiz_lb = quiz_resp.json()
        for entry in quiz_lb[:3]:
            print(f"   {entry['rank']}. {entry['name']} - {entry['score']} points")
    else:
        print(f"   ❌ Failed to fetch quiz leaderboard: {quiz_resp.status_code} {quiz_resp.text}")
    
    print("\nCoding Leaderboard:")
    coding_resp = requests.get(f"{BASE_URL}/coding/leaderboard/{exam_id}")
    if coding_resp.ok:
        coding_lb = coding_resp.json()
        for entry in coding_lb[:3]:
            print(f"   {entry['rank']}. {entry['name']} - {entry['total_score']} points")
    else:
        print(f"   ❌ Failed to fetch coding leaderboard: {coding_resp.status_code} {coding_resp.text}")
    
    print_section("✅ DEMO COMPLETE")
    print("\nSystem Features Demonstrated:")
    print("  ✅ Admin authentication & exam creation")
    print("  ✅ MCQ quiz round")
    print("  ✅ Java code submission")
    print("  ✅ Async evaluation via Celery")
    print("  ✅ Test case validation (visible + hidden)")
    print("  ✅ Scoring algorithm")
    print("  ✅ Dual leaderboards (Quiz + Coding)")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Celery Monitoring: http://localhost:5555 (if running with flower)")

if __name__ == "__main__":
    print("Starting demo in 2 seconds...")
    print("Make sure:")
    print("  1. Backend is running: uvicorn app.main:app --reload")
    print("  2. Admin seeded: python -m scripts.seed_admin")
    print("  3. Celery worker running: python scripts/run_celery_worker.py")
    time.sleep(2)
    demo()
