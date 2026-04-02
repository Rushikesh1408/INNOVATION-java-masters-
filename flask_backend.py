from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

from app.core.config import get_settings
from app.core.security import create_access_token, create_admin_access_token, decode_token
from app.db.session import SessionLocal
from app.models.coding_problem import CodingProblem, Submission
from app.models.result import Result
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.repositories.coding_repository import CodingProblemRepository, SubmissionRepository
from app.services.auth_service import AuthService
from app.services.coding_service import CodingService
from app.services.contestant_service import ContestantService


settings = get_settings()
DEBUG_MODE = os.environ.get("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"}


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _json_error(message: str, status_code: int):
    return jsonify({"detail": message}), status_code


def _cookie_response(payload: dict, token: str | None = None, expires_in: int | None = None):
    response = make_response(jsonify(payload))
    if token:
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            samesite="Lax",
            secure=not DEBUG_MODE,
            max_age=expires_in,
        )
    return response


def _read_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    raise ValueError("Missing access token")


def _decode_identity() -> dict:
    payload = decode_token(_read_token())
    subject = str(payload.get("sub", ""))
    role = str(payload.get("role", ""))
    if role == "contestant":
        parts = subject.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid contestant session token")
        return {
            "role": role,
            "user_id": int(parts[0]),
            "session_id": parts[1],
            "exam_id": int(parts[2]),
        }
    if role == "admin":
        return {"role": role, "username": subject}
    raise ValueError("Unsupported token role")


def _serialize_exam(exam) -> dict:
    return {
        "id": exam.id,
        "title": exam.title,
        "time_limit": exam.time_limit,
        "rules": exam.rules,
        "positive_mark": exam.positive_mark,
        "negative_mark": exam.negative_mark,
    }


def _serialize_question(question) -> dict:
    return {
        "id": question.id,
        "question_text": question.question_text,
        "option_1": question.option_1,
        "option_2": question.option_2,
        "option_3": question.option_3,
        "option_4": question.option_4,
    }


def _serialize_problem(problem: CodingProblem, include_hidden: bool = False) -> dict:
    payload = {
        "id": problem.id,
        "exam_id": problem.exam_id,
        "title": problem.title,
        "description": problem.description,
        "difficulty": problem.difficulty,
        "time_limit_seconds": problem.time_limit_seconds,
        "memory_limit_mb": problem.memory_limit_mb,
        "starter_code": problem.starter_code,
        "visible_test_cases": problem.visible_test_cases or [],
    }
    if include_hidden:
        payload["hidden_test_cases"] = problem.hidden_test_cases or []
    return payload


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": settings.cors_origins}})

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(404)
    def not_found(_error):
        return _json_error("Not found", 404)

    @app.errorhandler(500)
    def internal_error(_error):
        return _json_error("Internal server error", 500)

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "flask-exam-platform"})

    @app.route("/api/v1/auth/login", methods=["POST"])
    def contestant_login():
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        exam_id = payload.get("exam_id")

        if not name or not email or exam_id in (None, ""):
            return _json_error("name, email and exam_id are required", 400)

        try:
            with db_session() as db:
                service = ContestantService(db)
                exam_session, exam, questions = service.start_exam(
                    name=name,
                    email=email,
                    exam_id=int(exam_id),
                    ip_address=request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1"),
                    device_info=request.headers.get("User-Agent", "unknown"),
                )
                token, expires_in = create_access_token(
                    subject=f"{exam_session.user_id}:{exam_session.id}:{exam_session.exam_id}",
                    role="contestant",
                    expire_minutes=settings.admin_jwt_expire_minutes,
                )
                response_payload = {
                    "access_token": token,
                    "expires_in": expires_in,
                    "user": {"id": exam_session.user_id, "name": name, "email": email},
                    "session_id": str(exam_session.id),
                    "exam": _serialize_exam(exam),
                    "questions": [
                        {
                            "id": item["question_id"],
                            "question_text": item["question_text"],
                            "options": item["options"],
                        }
                        for item in questions
                    ],
                }
                return _cookie_response(response_payload, token=token, expires_in=expires_in)
        except HTTPException as exc:
            return _json_error(str(exc.detail), int(exc.status_code))
        except (ValueError, TypeError) as exc:
            return _json_error(str(exc), 400)

    @app.route("/api/v1/auth/admin/login", methods=["POST"])
    def admin_login():
        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))
        if not username or not password:
            return _json_error("username and password are required", 400)

        with db_session() as db:
            try:
                token, expires_in = AuthService(db).admin_login(username, password)
            except HTTPException as exc:
                return _json_error(str(exc.detail), int(exc.status_code))
            return _cookie_response(
                {"access_token": token, "expires_in": expires_in, "user": {"username": username}},
                token=token,
                expires_in=expires_in,
            )

    @app.route("/api/v1/auth/me", methods=["GET"])
    def auth_me():
        try:
            identity = _decode_identity()
        except Exception as exc:
            return _json_error(str(exc), 401)
        return jsonify(identity)

    @app.route("/api/v1/auth/logout", methods=["POST"])
    def logout():
        response = make_response(jsonify({"detail": "logged out"}))
        response.delete_cookie("access_token")
        return response

    @app.route("/api/v1/exams/<int:exam_id>/quiz", methods=["GET"])
    def quiz_payload(exam_id: int):
        with db_session() as db:
            service = ContestantService(db)
            exam = service.exam_repo.get_exam(exam_id)
            if not exam:
                return _json_error("Exam not found", 404)
            questions = service.exam_repo.list_questions(exam_id)
            return jsonify(
                {
                    "exam": _serialize_exam(exam),
                    "questions": [
                        {
                            "id": question.id,
                            "question_text": question.question_text,
                            "options": [
                                question.option_1,
                                question.option_2,
                                question.option_3,
                                question.option_4,
                            ],
                        }
                        for question in questions
                    ],
                }
            )

    @app.route("/api/v1/quiz/submit", methods=["POST"])
    def submit_quiz():
        payload = request.get_json(silent=True) or {}
        answers = payload.get("answers", [])
        session_id = payload.get("session_id")

        if not session_id:
            try:
                identity = _decode_identity()
                session_id = identity["session_id"]
            except Exception as exc:
                return _json_error(str(exc), 401)

        try:
            session_uuid = UUID(str(session_id))
        except ValueError:
            return _json_error("Invalid session_id", 400)

        with db_session() as db:
            service = ContestantService(db)
            try:
                for answer in answers:
                    service.submit_answer(
                        session_id=session_uuid,
                        question_id=int(answer.get("question_id")),
                        selected_option=answer.get("selected_option"),
                        time_taken=int(answer.get("time_taken", 0)),
                    )
                result = service.finalize_result(session_uuid)
            except HTTPException as exc:
                return _json_error(str(exc.detail), int(exc.status_code))
            except (ValueError, TypeError) as exc:
                return _json_error(str(exc), 400)

            leaderboard = service.leaderboard(result.exam_id)
            current_rank = next(
                (item["rank"] for item in leaderboard if item["user_id"] == result.user_id),
                None,
            )
            qualified_for_coding = bool(result.score >= 60 and not result.flagged)
            return jsonify(
                {
                    "score": result.score,
                    "rank": current_rank,
                    "qualified_for_coding": qualified_for_coding,
                    "result": {
                        "id": result.id,
                        "user_id": result.user_id,
                        "exam_id": result.exam_id,
                        "score": result.score,
                        "accuracy": result.accuracy,
                        "total_time": result.total_time,
                        "flagged": result.flagged,
                    },
                }
            )

    @app.route("/api/v1/coding/problems/<int:exam_id>", methods=["GET"])
    def list_coding_problems(exam_id: int):
        with db_session() as db:
            repo = CodingProblemRepository(db)
            problems = repo.get_by_exam(exam_id)
            return jsonify({"problems": [_serialize_problem(problem) for problem in problems]})

    @app.route("/api/v1/coding/problems/<int:exam_id>/<int:problem_id>", methods=["GET"])
    def get_coding_problem(exam_id: int, problem_id: int):
        with db_session() as db:
            repo = CodingProblemRepository(db)
            problem = repo.get_by_id(problem_id)
            if problem is None:
                return _json_error("Coding problem not found", 404)

            problem_exam_id = int(getattr(problem, "exam_id", -1))
            if problem_exam_id != exam_id:
                return _json_error("Coding problem not found", 404)
            return jsonify({"problem": _serialize_problem(problem)})

    @app.route("/api/v1/coding/submit/<int:problem_id>", methods=["POST"])
    def submit_code(problem_id: int):
        payload = request.get_json(silent=True) or {}
        code = str(payload.get("code", ""))
        if not code.strip():
            return _json_error("code is required", 400)

        try:
            identity = _decode_identity()
        except Exception as exc:
            return _json_error(str(exc), 401)

        with db_session() as db:
            problem_repo = CodingProblemRepository(db)
            problem = problem_repo.get_by_id(problem_id)
            if not problem:
                return _json_error("Coding problem not found", 404)

            quiz_result = (
                db.query(Result)
                .filter(Result.user_id == identity["user_id"], Result.exam_id == problem.exam_id)
                .first()
            )
            if not quiz_result or quiz_result.score < 60:
                return _json_error("User is not qualified for the coding round", 403)

            service = CodingService(db)
            try:
                submission = service.submit_code(identity["user_id"], problem_id, code)
                evaluation = service.evaluate_submission(submission["submission_id"])
            except ValueError as exc:
                return _json_error(str(exc), 400)

            response_payload = {
                **submission,
                **evaluation,
                "problem": _serialize_problem(problem),
            }
            return jsonify(response_payload)

    @app.route("/api/v1/coding/submissions/<int:submission_id>", methods=["GET"])
    def get_submission(submission_id: int):
        with db_session() as db:
            repo = SubmissionRepository(db)
            submission = repo.get_by_id(submission_id)
            if not submission:
                return _json_error("Submission not found", 404)
            return jsonify({"submission": {
                "id": submission.id,
                "user_id": submission.user_id,
                "problem_id": submission.problem_id,
                "status": submission.status,
                "score": submission.score,
                "passed_visible": submission.passed_visible,
                "passed_hidden": submission.passed_hidden,
                "total_visible": submission.total_visible,
                "total_hidden": submission.total_hidden,
                "execution_time_ms": submission.execution_time_ms,
                "error_message": submission.error_message,
                "test_case_results": submission.test_case_results,
            }})

    @app.route("/api/v1/coding/leaderboard/<int:exam_id>", methods=["GET"])
    def coding_leaderboard(exam_id: int):
        limit = request.args.get("limit", 50)
        with db_session() as db:
            service = CodingService(db)
            try:
                leaderboard = service.get_coding_leaderboard(exam_id, int(limit))
            except ValueError as exc:
                return _json_error(str(exc), 400)
            return jsonify({"leaderboard": leaderboard})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=DEBUG_MODE)