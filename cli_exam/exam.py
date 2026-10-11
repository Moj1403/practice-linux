#!/usr/bin/env python3
"""
سامانه آزمون عملی لینوکس (نسخه خط فرمان - CLI)
بهینه‌سازی‌شده برای تمام ترمینال‌های لینوکس با طراحی تمیز دو زبانه (فارسی / انگلیسی)
بدون به هم ریختگی فونت و مکان‌نما (Terminal-Safe & BiDi friendly)
"""

import os
import sys
import json
import time
import hmac
import hashlib
import datetime
import subprocess

SECRET_SALT = "LINUX_EXAM_MASTER_KEY_2026"

# استایل‌های رنگی ANSI
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_banner(lang="fa"):
    sub = "سامانه آزمون و ارزیابی عملی مهارت‌های لینوکس" if lang == "fa" else "Interactive Hands-on Linux Assessment Suite"
    print(f"""{CYAN}{BOLD}
======================================================================
                     LINUX PRACTICAL EXAM CLI
       {sub}
======================================================================{RESET}""")

def load_questions():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_file = os.path.join(script_dir, "questions.json")
    if not os.path.exists(questions_file):
        print(f"{RED}Error: questions.json not found in {script_dir}!{RESET}")
        sys.exit(1)
    with open(questions_file, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_signature(student_name, student_id, score, total_points, passed_ids, hints_used, timestamp):
    payload = f"{student_name}:{student_id}:{score}:{total_points}:{sorted(passed_ids)}:{sorted(list(hints_used))}:{timestamp}"
    return hmac.new(SECRET_SALT.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

def display_question_card(q, current_idx, total_questions, is_solved, lang="fa", hints_used=None):
    if hints_used is None:
        hints_used = set()
    hint_penalty = q.get("hint_penalty", 3)
    has_hint = (q["id"] in hints_used)
    base_points = q.get("points", 10)
    current_question_points = max(0, base_points - hint_penalty) if has_hint else base_points

    if lang == "fa":
        status_tag = f"{GREEN}[ حل شده ✔ ]{RESET}" if is_solved else f"{YELLOW}[ در انتظار پاسخ ⏳ ]{RESET}"
        title = q.get("title_fa", q.get("title", ""))
        desc = q.get("desc_fa", q.get("description", ""))
        q_label = f"سؤال {current_idx + 1} از {total_questions}"
        if has_hint:
            points_label = f"امتیاز: {current_question_points} نمره ({RED}{hint_penalty} نمره کسر شد بابت راهنمایی{RESET})"
        else:
            points_label = f"امتیاز: {base_points} نمره {DIM}(مشاهده راهنمایی: -{hint_penalty} نمره جریمه){RESET}"
        task_label = "شرح وظیفه:"
        specs_label = "مشخصات و مقادیر مورد نیاز:"
        cmds_label = "[c] بررسی | [n] سوال بعد | [p] سوال قبل | [h] راهنما (-۳ نمره) | [lang] زبان | [f] پایان"
    else:
        status_tag = f"{GREEN}[ SOLVED ✔ ]{RESET}" if is_solved else f"{YELLOW}[ PENDING ⏳ ]{RESET}"
        title = q.get("title_en", q.get("title", ""))
        desc = q.get("desc_en", q.get("description", ""))
        q_label = f"Question {current_idx + 1} of {total_questions}"
        if has_hint:
            points_label = f"Points: {current_question_points} ({RED}-{hint_penalty} deducted for hint{RESET})"
        else:
            points_label = f"Points: {base_points} {DIM}(Hint penalty: -{hint_penalty} pts){RESET}"
        task_label = "Task Description:"
        specs_label = "Required Specifications:"
        cmds_label = "[c] Check | [n] Next | [p] Prev | [h] Hint (-3 pts) | [lang] Toggle Lang | [f] Finish"

    category = q.get(f"category_{lang}", q.get("category_en", "عمومی"))
    print("\n" + "═" * 70)
    print(f"{MAGENTA}{BOLD}📁 [{category}]{RESET}")
    print(f"{BOLD}{q_label}: {CYAN}{title}{RESET}  {status_tag}")
    print(f"{points_label}")
    print("─" * 70)
    print(f"{BOLD}{task_label}{RESET}")
    print(f"  {desc}")

    # نمایش مقادیر و مسیرها در خطوط تفکیک‌شده چپ‌چین برای جلوگیری از به هم ریختگی متن
    specs = q.get("specs", [])
    if specs:
        print(f"\n{BOLD}{specs_label}{RESET}")
        for s in specs:
            print(f"  {CYAN}•{RESET} {s}")

    print("═" * 70)
    print(f"{DIM}{cmds_label}{RESET}")
    print("─" * 70)

def main():
    clear_screen()
    print_banner("en")

    # انتخاب زبان در بدو ورود
    print(f"{BOLD}Select Language / انتخاب زبان آزمون:{RESET}")
    print(f"  {CYAN}[1]{RESET} فارسی (Persian - بهینه‌شده برای ترمینال)")
    print(f"  {CYAN}[2]{RESET} English (Recommended for standard terminals)")
    lang_choice = input(f"{BOLD}> {RESET}").strip()
    current_lang = "en" if lang_choice == "2" else "fa"

    clear_screen()
    print_banner(current_lang)

    questions = load_questions()
    total_questions = len(questions)
    total_points = sum(q.get("points", 10) for q in questions)

    if current_lang == "fa":
        print(f"{YELLOW}مشخصات دانشجو را وارد کنید:{RESET}")
        student_name = input("نام و نام خانوادگی: ").strip()
        while not student_name:
            student_name = input("نام نمی‌تواند خالی باشد: ").strip()
        student_id = input("کد ملی: ").strip()
        while not student_id:
            student_id = input("کد ملی الزامی است: ").strip()
    else:
        print(f"{YELLOW}Please enter your credentials:{RESET}")
        student_name = input("Full Name: ").strip()
        while not student_name:
            student_name = input("Name cannot be empty: ").strip()
        student_id = input("National ID (کد ملی): ").strip()
        while not student_id:
            student_id = input("National ID cannot be empty: ").strip()

    solved = {}
    hints_used = set()
    current_idx = 0
    prev_dir = os.getcwd()

    def compute_current_score():
        score = 0
        for item in questions:
            if solved.get(item["id"]):
                pts = item.get("points", 10)
                if item["id"] in hints_used:
                    pts = max(0, pts - item.get("hint_penalty", 3))
                score += pts
        return score

    clear_screen()
    print_banner(current_lang)
    display_question_card(questions[current_idx], current_idx, total_questions, solved.get(questions[current_idx]["id"], False), current_lang, hints_used)

    while True:
        cwd = os.getcwd()
        q = questions[current_idx]
        is_solved = solved.get(q["id"], False)
        current_score = compute_current_score()

        # پرامپت کاملاً استاندارد و خنثی بدون به هم ریختن مکان‌نما
        prompt_cwd = cwd.replace(os.path.expanduser("~"), "~")
        prompt_line = (
            f"\n{BOLD}{BLUE}[PWD: {prompt_cwd}]{RESET} "
            f"{CYAN}[Q {current_idx + 1}/{total_questions} | Score: {current_score}/{total_points}]{RESET}\n"
            f"{GREEN}❯{RESET} "
        )

        try:
            raw_input = input(prompt_line).strip()
        except EOFError:
            break

        if not raw_input:
            continue

        cmd_lower = raw_input.lower()

        # تغییر زبان زنده
        if cmd_lower in ['lang', 'language']:
            current_lang = "en" if current_lang == "fa" else "fa"
            clear_screen()
            print_banner(current_lang)
            display_question_card(q, current_idx, total_questions, is_solved, current_lang, hints_used)
            continue

        # رفتن به سوال بعدی
        elif cmd_lower in ['n', 'next']:
            if current_idx < total_questions - 1:
                current_idx += 1
                clear_screen()
                print_banner(current_lang)
                display_question_card(questions[current_idx], current_idx, total_questions, solved.get(questions[current_idx]["id"], False), current_lang, hints_used)
            else:
                msg = "شما در آخرین سؤال قرار دارید." if current_lang == "fa" else "You are already at the last question."
                print(f"{YELLOW}{msg}{RESET}")
            continue

        # رفتن به سوال قبلی
        elif cmd_lower in ['p', 'prev', 'previous']:
            if current_idx > 0:
                current_idx -= 1
                clear_screen()
                print_banner(current_lang)
                display_question_card(questions[current_idx], current_idx, total_questions, solved.get(questions[current_idx]["id"], False), current_lang, hints_used)
            else:
                msg = "شما در اولین سؤال قرار دارید." if current_lang == "fa" else "You are at the first question."
                print(f"{YELLOW}{msg}{RESET}")
            continue

        # راهنمایی با کسر نمره
        elif cmd_lower in ['h', 'hint']:
            penalty = q.get("hint_penalty", 3)
            hint_txt = q.get(f"hint_{current_lang}", q.get("hint", ""))
            lbl = "💡 راهنمایی:" if current_lang == "fa" else "💡 Hint:"

            if q["id"] in hints_used:
                print(f"\n{YELLOW}{lbl} {hint_txt}{RESET}")
                msg_alr = f"{DIM}(راهنمایی این سؤال قبلاً باز شده و {penalty} نمره جریمه قبلاً اعمال گردیده است){RESET}" if current_lang == "fa" else f"{DIM}(Hint already unlocked; penalty applied){RESET}"
                print(msg_alr)
            else:
                msg_warn = (
                    f"⚠️ توجه: مشاهده راهنمایی باعث کسر {penalty} نمره از این سؤال می‌شود!\n"
                    f"آیا مایل به مشاهده راهنمایی هستید؟ (y/n) > "
                ) if current_lang == "fa" else (
                    f"⚠️ Warning: Unlocking hint will deduct {penalty} points from this question!\n"
                    f"Do you want to proceed? (y/n) > "
                )
                ans = input(f"\n{YELLOW}{BOLD}{msg_warn}{RESET}").strip().lower()
                if ans == 'y':
                    hints_used.add(q["id"])
                    print(f"\n{YELLOW}{lbl} {hint_txt}{RESET}")
                    msg_ded = f"{RED}{BOLD}🔻 {penalty} نمره از سقف این سؤال کسر گردید.{RESET}" if current_lang == "fa" else f"{RED}{BOLD}🔻 {penalty} points deducted from this question.{RESET}"
                    print(msg_ded)
                else:
                    msg_can = "مشاهده راهنمایی لغو شد. نمره‌ای کسر نگردید." if current_lang == "fa" else "Hint cancelled. No points deducted."
                    print(f"{GREEN}{msg_can}{RESET}")
            continue

        # بازنمایش سوال
        elif cmd_lower in ['q', 'question', 'show', 'clear']:
            clear_screen()
            print_banner(current_lang)
            display_question_card(q, current_idx, total_questions, is_solved, current_lang, hints_used)
            continue

        # فهرست تمامی سوالات
        elif cmd_lower in ['l', 'list']:
            clear_screen()
            hdr = "فهرست تمامی سؤالات آزمون (دسته‌بندی شده):" if current_lang == "fa" else "All Exam Questions (Grouped by Category):"
            print(f"\n{BOLD}{hdr}{RESET}")
            last_cat = None
            for i, item in enumerate(questions):
                cat = item.get(f"category_{current_lang}", item.get("category_en", "عمومی"))
                if cat != last_cat:
                    last_cat = cat
                    print(f"\n{MAGENTA}{BOLD}📁 {cat}:{RESET}")
                title_item = item.get(f"title_{current_lang}", item.get("title", ""))
                st = f"{GREEN}✔ Solved{RESET}" if solved.get(item["id"]) else f"{RED}⏳ Pending{RESET}"
                hint_indicator = f"{RED}[Hint -3]{RESET} " if item["id"] in hints_used else ""
                print(f"   [{i+1}] {hint_indicator}{title_item} ({item.get('points', 10)} pts) ──> {st}")
            print()
            pr_choice = "شماره سوال برای انتخاب (یا Enter برای برگشت): " if current_lang == "fa" else "Enter question number (or Enter to cancel): "
            choice = input(pr_choice).strip()
            if choice.isdigit():
                num = int(choice) - 1
                if 0 <= num < total_questions:
                    current_idx = num
            clear_screen()
            print_banner(current_lang)
            display_question_card(questions[current_idx], current_idx, total_questions, solved.get(questions[current_idx]["id"], False), current_lang, hints_used)
            continue

        # بررسی پاسخ
        elif cmd_lower in ['c', 'check']:
            msg_eval = "🔍 در حال اعتبارسنجی پاسخ شما روی سیستم..." if current_lang == "fa" else "🔍 Validating your answer on the system..."
            print(f"\n{CYAN}{msg_eval}{RESET}")
            verify_cmd = q.get("verify_cmd", "false")
            try:
                res = subprocess.run(
                    ["/bin/bash", "-c", verify_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=6
                )
                if res.returncode == 0:
                    solved[q["id"]] = True
                    base_pts = q.get("points", 10)
                    penalty = q.get("hint_penalty", 3)
                    if q["id"] in hints_used:
                        earned = max(0, base_pts - penalty)
                        note = f" ({penalty} نمره کسر شد بابت راهنمایی)" if current_lang == "fa" else f" ({penalty} pts deducted for hint)"
                    else:
                        earned = base_pts
                        note = ""
                    msg_succ = f"✔ تبریک! پاسخ شما کاملاً صحیح است (+{earned} نمره{note})" if current_lang == "fa" else f"✔ Awesome! Task successfully completed (+{earned} pts{note})"
                    print(f"{GREEN}{BOLD}{msg_succ}{RESET}")
                else:
                    msg_fail = "✘ شرایط مسئله هنوز روی سیستم برآورده نشده است." if current_lang == "fa" else "✘ The task requirements are not yet met."
                    msg_tip = "دستورات را تصحیح کرده و مجدداً [c] را وارد کنید." if current_lang == "fa" else "Review your changes and type [c] to check again."
                    print(f"{RED}{BOLD}{msg_fail}{RESET}")
                    print(f"{DIM}{msg_tip}{RESET}")
            except subprocess.TimeoutExpired:
                print(f"{RED}Timeout during verification.{RESET}")
            except Exception as e:
                print(f"{RED}Verification error: {e}{RESET}")
            continue

        # پایان آزمون
        elif cmd_lower in ['f', 'finish']:
            msg_confirm = "آیا از پایان آزمون و ثبت کارنامه نهایی مطمئن هستید؟ (y/n)" if current_lang == "fa" else "Are you sure you want to finish the exam? (y/n)"
            print(f"\n{YELLOW}{BOLD}{msg_confirm}{RESET}")
            confirm = input("> ").strip().lower()
            if confirm == 'y':
                break
            else:
                continue

        # مدیریت دستور cd
        if raw_input == "cd" or raw_input.startswith("cd "):
            parts = raw_input.split(maxsplit=1)
            target = parts[1].strip() if len(parts) > 1 else "~"

            if target == "-":
                target = prev_dir
            else:
                target = os.path.expanduser(target)

            try:
                new_prev = os.getcwd()
                os.chdir(target)
                prev_dir = new_prev
                msg_dir = f"مسیر جاری: {os.getcwd()}" if current_lang == "fa" else f"Changed directory to: {os.getcwd()}"
                print(f"{DIM}{msg_dir}{RESET}")
            except FileNotFoundError:
                print(f"{RED}bash: cd: {target}: No such file or directory{RESET}")
            except Exception as e:
                print(f"{RED}cd error: {e}{RESET}")
            continue

        # اجرای دستورات شل لینوکس (ls, mkdir, touch, chmod, cat, grep, ...)
        try:
            subprocess.run(raw_input, shell=True, executable="/bin/bash")
        except Exception as e:
            print(f"{RED}Execution error: {e}{RESET}")

    # صدور کارنامه و امضای دیجیتال
    clear_screen()
    final_score = compute_current_score()
    passed_ids = [item["id"] for item in questions if solved.get(item["id"])]
    timestamp = datetime.datetime.now().isoformat()
    signature = generate_signature(student_name, student_id, final_score, total_points, passed_ids, hints_used, timestamp)

    result_data = {
        "student_name": student_name,
        "student_id": student_id,
        "score": final_score,
        "total_points": total_points,
        "passed_questions": passed_ids,
        "hints_used": sorted(list(hints_used)),
        "hints_count": len(hints_used),
        "timestamp": timestamp,
        "signature": signature
    }

    output_filename = f"exam_result_{student_id}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"""{GREEN}{BOLD}
======================================================================
                     OFFICIAL EXAM CERTIFICATE
======================================================================{RESET}
  Student Name    : {BOLD}{student_name}{RESET}
  National ID     : {BOLD}{student_id}{RESET}
  Total Score     : {YELLOW}{BOLD}{final_score} / {total_points}{RESET}
  Passed Tasks    : {GREEN}{len(passed_ids)} / {total_questions}{RESET}
  Hints Unlocked  : {RED if hints_used else GREEN}{len(hints_used)}{RESET}
  Submitted At    : {timestamp}
  Result File     : {CYAN}{output_filename}{RESET}
  HMAC Signature  : {DIM}{signature}{RESET}
----------------------------------------------------------------------
Notice:
Please submit '{CYAN}{output_filename}{RESET}' to your instructor.
Any modification to this file will invalidate your score.
======================================================================
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Exam cancelled by user.{RESET}")
        sys.exit(0)
