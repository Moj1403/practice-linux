#!/usr/bin/env python3
"""
ابزار استاد برای اعتبارسنجی کارنامه خروجی وب‌اپلیکیشن
"""

import sys
import json
import hmac
import hashlib

SECRET_SALT = "LINUX_EXAM_MASTER_KEY_2026"

def verify_certificate(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ خطا در باز کردن فایل: {e}")
        return False

    required = ["student_name", "student_id", "score", "total_points", "passed_questions", "timestamp", "signature"]
    for r in required:
        if r not in data:
            print(f"❌ فایل نامعتبر است: فیلد {r} وجود ندارد.")
            return False

    hints_used = data.get("hints_used", [])
    payload = f"{data['student_name']}:{data['student_id']}:{data['score']}:{data['total_points']}:{sorted(data['passed_questions'])}:{sorted(list(hints_used))}:{data['timestamp']}"
    expected_sig = hmac.new(SECRET_SALT.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

    print("=" * 60)
    print(f"📄 نام دانشجو:     {data['student_name']}")
    print(f"🆔 کد ملی:         {data['student_id']}")
    print(f"🎯 نمره ثبت شده:   {data['score']} از {data['total_points']}")
    print(f"💡 راهنماهای مصرفی: {len(hints_used)} مورد (کسر نمره: {len(hints_used) * 3} نمره)")
    print(f"📅 زمان ثبت:       {data['timestamp']}")
    print("=" * 60)

    if hmac.compare_digest(data['signature'], expected_sig):
        print("✅ وضعیت کارنامه: معتبر و تایید شده (بدون دستکاری)")
        return True
    else:
        print("🚨 هشدار: امضای دیجیتال همخوانی ندارد! این فایل دستکاری یا جعل شده است.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("روش استفاده:")
        print(f"  python3 {sys.argv[0]} <exam_result_file.json>")
        sys.exit(1)

    verify_certificate(sys.argv[1])
