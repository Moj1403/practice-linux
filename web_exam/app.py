#!/usr/bin/env python3
"""
سامانه آزمون عملی لینوکس (نسخه وب‌اپلیکیشن محلی)
طراحی شده با پایتون و فلسک (Flask)
"""

import os
import sys
import json
import hmac
import hashlib
import datetime
import subprocess
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

SECRET_SALT = "LINUX_EXAM_MASTER_KEY_2026"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")

def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_signature(student_name, student_id, score, total_points, passed_ids, hints_used, timestamp):
    payload = f"{student_name}:{student_id}:{score}:{total_points}:{sorted(passed_ids)}:{sorted(list(hints_used))}:{timestamp}"
    return hmac.new(SECRET_SALT.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/questions", methods=["GET"])
def get_questions():
    questions = load_questions()
    # دستورات تست حساس را برای فرانت‌اند فیلتر می‌کنیم تا تقلب نشود
    safe_questions = []
    for q in questions:
        safe_questions.append({
            "id": q["id"],
            "category_fa": q.get("category_fa", "عمومی"),
            "category_en": q.get("category_en", "General"),
            "title": q.get("title_fa", q.get("title", "")),
            "title_en": q.get("title_en", ""),
            "description": q.get("desc_fa", q.get("description", "")),
            "desc_en": q.get("desc_en", ""),
            "specs": q.get("specs", []),
            "points": q.get("points", 10),
            "hint_penalty": q.get("hint_penalty", 3),
            "hint": q.get("hint_fa", q.get("hint", ""))
        })
    return jsonify(safe_questions)

@app.route("/api/check", methods=["POST"])
def check_question():
    data = request.get_json() or {}
    q_id = data.get("question_id")
    questions = load_questions()

    question = next((q for q in questions if q["id"] == q_id), None)
    if not question:
        return jsonify({"passed": False, "message": "سؤال مورد نظر یافت نشد."}), 404

    verify_cmd = question.get("verify_cmd", "false")

    try:
        res = subprocess.run(
            ["/bin/bash", "-c", verify_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        passed = (res.returncode == 0)
        if passed:
            return jsonify({
                "passed": True,
                "message": "عالی! دستورات به درستی روی لینوکس اجرا شده و تست پاس شد.",
                "points": question.get("points", 10)
            })
        else:
            return jsonify({
                "passed": False,
                "message": "شرط سؤال هنوز روی سیستم برقرار نیست. لطفاً مراحل را دوباره بررسی کنید."
            })
    except subprocess.TimeoutExpired:
        return jsonify({"passed": False, "message": "مهلت زمان بررسی به پایان رسید (Timeout)."}), 408
    except Exception as e:
        return jsonify({"passed": False, "message": f"خطا در اجرای تست: {str(e)}"}), 500

@app.route("/api/submit", methods=["POST"])
def submit_exam():
    data = request.get_json() or {}
    student_name = data.get("student_name", "").strip()
    student_id = data.get("student_id", "").strip()
    hints_used = set(data.get("hints_used", []))

    if not student_name or not student_id:
        return jsonify({"error": "نام و کد ملی الزامی است."}), 400

    questions = load_questions()
    passed_ids = []
    total_score = 0
    total_points = sum(q.get("points", 10) for q in questions)

    # اعتبارسنجی قطعی تمام سوالات در لحظه ثبت با کسر جریمه راهنمایی
    for q in questions:
        verify_cmd = q.get("verify_cmd", "false")
        try:
            res = subprocess.run(
                ["/bin/bash", "-c", verify_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if res.returncode == 0:
                passed_ids.append(q["id"])
                pts = q.get("points", 10)
                if q["id"] in hints_used:
                    pts = max(0, pts - q.get("hint_penalty", 3))
                total_score += pts
        except Exception:
            pass

    timestamp = datetime.datetime.now().isoformat()
    signature = generate_signature(student_name, student_id, total_score, total_points, passed_ids, hints_used, timestamp)

    result_data = {
        "student_name": student_name,
        "student_id": student_id,
        "score": total_score,
        "total_points": total_points,
        "passed_questions": passed_ids,
        "hints_used": sorted(list(hints_used)),
        "hints_count": len(hints_used),
        "timestamp": timestamp,
        "signature": signature
    }

    result_file = os.path.join(BASE_DIR, f"exam_result_{student_id}.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    return jsonify({
        "success": True,
        "result": result_data,
        "download_url": f"/api/download/{student_id}"
    })

@app.route("/api/download/<student_id>", methods=["GET"])
def download_result(student_id):
    filename = f"exam_result_{student_id}.json"
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({"error": "فایل یافت نشد"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 سامانه وب آزمون لینوکس در حال اجرا روی: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
