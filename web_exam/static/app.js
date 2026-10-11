// سامانه وب آزمون عملی لینوکس - منطق و تعاملات فرانت‌اند

let questions = [];
let currentIndex = 0;
let studentName = "";
let studentId = "";
let solvedMap = {}; // { question_id: true }
let hintsUsed = new Set(); // { question_id }
let timerInterval = null;
let secondsElapsed = 0;

document.addEventListener("DOMContentLoaded", () => {
  const startForm = document.getElementById("start-exam-form");
  const btnPrev = document.getElementById("btn-prev-q");
  const btnNext = document.getElementById("btn-next-q");
  const btnCheck = document.getElementById("btn-check-task");
  const btnToggleHint = document.getElementById("btn-toggle-hint");
  const btnFinish = document.getElementById("btn-finish-exam");

  startForm.addEventListener("submit", handleStartExam);
  btnPrev.addEventListener("click", () => navigateQuestion(currentIndex - 1));
  btnNext.addEventListener("click", () => navigateQuestion(currentIndex + 1));
  btnCheck.addEventListener("click", handleCheckAnswer);
  btnToggleHint.addEventListener("click", toggleHint);
  btnFinish.addEventListener("click", handleFinishExam);
});

async function handleStartExam(e) {
  e.preventDefault();
  studentName = document.getElementById("student-name").value.trim();
  studentId = document.getElementById("student-id").value.trim();

  if (!studentName || !studentId) {
    alert("لطفاً نام و کد ملی خود را وارد نمایید.");
    return;
  }

  try {
    const res = await fetch("/api/questions");
    questions = await res.json();
    if (!questions || questions.length === 0) {
      alert("خطا در دریافت لیست سوالات آزمون!");
      return;
    }

    // پنهان کردن فرم ورود و نمایش پنل آزمون
    document.getElementById("login-section").style.display = "none";
    document.getElementById("exam-section").style.display = "grid";
    document.getElementById("exam-stats-bar").style.display = "flex";

    startTimer();
    renderSidebarList();
    renderCurrentQuestion();
    updateStatsBar();
  } catch (err) {
    console.error(err);
    alert("خطا در اتصال به سرور: " + err.message);
  }
}

function startTimer() {
  secondsElapsed = 0;
  const timerDisplay = document.getElementById("timer-display");
  timerInterval = setInterval(() => {
    secondsElapsed++;
    const mins = String(Math.floor(secondsElapsed / 60)).padStart(2, "0");
    const secs = String(secondsElapsed % 60).padStart(2, "0");
    timerDisplay.textContent = `${mins}:${secs}`;
  }, 1000);
}

function renderSidebarList() {
  const container = document.getElementById("questions-list-nav");
  container.innerHTML = "";

  let lastCategory = null;

  questions.forEach((q, idx) => {
    const cat = q.category_fa || "عمومی";
    if (cat !== lastCategory) {
      lastCategory = cat;
      const catHeader = document.createElement("div");
      catHeader.className = "sidebar-category-heading";
      catHeader.innerHTML = `📁 ${cat}`;
      container.appendChild(catHeader);
    }

    const item = document.createElement("div");
    item.className = `q-nav-item ${idx === currentIndex ? "active" : ""}`;
    item.id = `nav-item-${q.id}`;
    item.onclick = () => navigateQuestion(idx);

    const isSolved = solvedMap[q.id];
    const statusClass = isSolved ? "q-status-solved" : "q-status-pending";
    const statusText = isSolved ? "✔ حل شده" : "در انتظار";

    item.innerHTML = `
      <span class="q-nav-title">${idx + 1}. ${q.title}</span>
      <span class="q-nav-status ${statusClass}" id="nav-badge-${q.id}">${statusText}</span>
    `;
    container.appendChild(item);
  });
}

function renderCurrentQuestion() {
  if (!questions[currentIndex]) return;
  const q = questions[currentIndex];

  const hintPenalty = q.hint_penalty || 3;
  const isHintActive = hintsUsed.has(q.id);
  const curPoints = isHintActive ? Math.max(0, q.points - hintPenalty) : q.points;

  document.getElementById("q-category-pill").textContent = q.category_fa || "عمومی";
  document.getElementById("q-index-pill").textContent = `سؤال ${currentIndex + 1} از ${questions.length}`;
  document.getElementById("q-points-pill").textContent = isHintActive ? `${curPoints} نمره (${hintPenalty} نمره کسر شد)` : `${curPoints} نمره (راهنمایی: -${hintPenalty} نمره)`;
  document.getElementById("q-title").textContent = q.title;
  document.getElementById("q-description").textContent = q.description;

  const hintBtn = document.getElementById("btn-toggle-hint");
  if (isHintActive) {
    hintBtn.textContent = "💡 نمایش مجدد راهنمایی (-۳ نمره اعمال شده)";
    hintBtn.className = "btn btn-danger";
  } else {
    hintBtn.textContent = "💡 نمایش راهنمایی (-۳ نمره جریمه)";
    hintBtn.className = "btn btn-secondary";
  }

  // مشخصات و مقادیر مورد نیاز
  const specsBox = document.getElementById("q-specs-container");
  if (q.specs && q.specs.length > 0) {
    specsBox.style.display = "block";
    specsBox.innerHTML = `
      <div class="specs-title">مشخصات و مقادیر مورد نیاز:</div>
      ${q.specs.map(s => `<div class="spec-item">• ${s}</div>`).join("")}
    `;
  } else {
    specsBox.style.display = "none";
  }

  // بازنشانی راهنما و نتیجه قبلی
  document.getElementById("hint-box").style.display = "none";
  document.getElementById("hint-content").textContent = q.hint || "راهنمایی وجود ندارد.";
  document.getElementById("check-result-box").style.display = "none";

  // دکمه‌های ناوبری
  document.getElementById("btn-prev-q").disabled = (currentIndex === 0);
  document.getElementById("btn-next-q").disabled = (currentIndex === questions.length - 1);

  // به‌روزرسانی هایلایت در سایدبار
  document.querySelectorAll(".q-nav-item").forEach((el, idx) => {
    el.classList.toggle("active", idx === currentIndex);
  });
}

function navigateQuestion(newIndex) {
  if (newIndex >= 0 && newIndex < questions.length) {
    currentIndex = newIndex;
    renderCurrentQuestion();
  }
}

async function handleCheckAnswer() {
  const q = questions[currentIndex];
  const btn = document.getElementById("btn-check-task");
  const spinner = document.getElementById("btn-check-spinner");
  const btnText = document.getElementById("btn-check-text");
  const resultBox = document.getElementById("check-result-box");
  const feedbackIcon = document.getElementById("feedback-icon");
  const feedbackText = document.getElementById("feedback-text");

  btn.disabled = true;
  spinner.style.display = "inline-block";
  btnText.textContent = "در حال بررسی روی سیستم...";

  try {
    const res = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: q.id })
    });
    const data = await res.json();

    resultBox.style.display = "flex";
    if (data.passed) {
      resultBox.className = "result-feedback success";
      feedbackIcon.textContent = "✔";
      feedbackText.textContent = data.message || "عالی! سوال با موفقیت حل شد.";
      solvedMap[q.id] = true;

      // به‌روزرسانی نشان سایدبار
      const badge = document.getElementById(`nav-badge-${q.id}`);
      if (badge) {
        badge.className = "q-nav-status q-status-solved";
        badge.textContent = "✔ حل شده";
      }
    } else {
      resultBox.className = "result-feedback error";
      feedbackIcon.textContent = "✘";
      feedbackText.textContent = data.message || "دستورات هنوز به درستی اعمال نشده‌اند.";
    }

    updateStatsBar();
  } catch (err) {
    resultBox.style.display = "flex";
    resultBox.className = "result-feedback error";
    feedbackIcon.textContent = "⚠";
    feedbackText.textContent = "خطا در برقراری ارتباط با وب‌سرور: " + err.message;
  } finally {
    btn.disabled = false;
    spinner.style.display = "none";
    btnText.textContent = "🔍 بررسی مجدد روی سیستم";
  }
}

function toggleHint() {
  const q = questions[currentIndex];
  const box = document.getElementById("hint-box");
  const penalty = q.hint_penalty || 3;

  if (!hintsUsed.has(q.id)) {
    const confirmed = confirm(`⚠️ توجه: مشاهده راهنمایی باعث کسر ${penalty} نمره از سقف امتیاز این سؤال می‌شود!\n\nآیا از باز کردن راهنمایی اطمینان دارید؟`);
    if (!confirmed) return;
    hintsUsed.add(q.id);
    renderCurrentQuestion();
    updateStatsBar();
  }

  box.style.display = (box.style.display === "none") ? "block" : "none";
}

function updateStatsBar() {
  const totalScore = questions.reduce((acc, q) => acc + (q.points || 10), 0);
  const currentScore = questions.reduce((acc, q) => {
    if (!solvedMap[q.id]) return acc;
    const base = q.points || 10;
    const pen = hintsUsed.has(q.id) ? (q.hint_penalty || 3) : 0;
    return acc + Math.max(0, base - pen);
  }, 0);
  const solvedCount = Object.keys(solvedMap).length;

  document.getElementById("current-score").textContent = `${currentScore} از ${totalScore}`;
  document.getElementById("solved-count").textContent = `${solvedCount} از ${questions.length} حل شده`;

  const percent = questions.length ? Math.round((solvedCount / questions.length) * 100) : 0;
  document.getElementById("sidebar-progress").textContent = `${percent}%`;
  document.getElementById("progress-fill").style.width = `${percent}%`;
}

async function handleFinishExam() {
  const confirmed = confirm("آیا از پایان آزمون و ثبت قطعی نمره اطمینان دارید؟");
  if (!confirmed) return;

  if (timerInterval) clearInterval(timerInterval);

  try {
    const res = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_name: studentName,
        student_id: studentId,
        hints_used: Array.from(hintsUsed)
      })
    });
    const data = await res.json();
    if (data.success) {
      showResultModal(data.result, data.download_url);
    } else {
      alert("خطا در ثبت آزمون: " + (data.error || "نامشخص"));
    }
  } catch (err) {
    alert("خطا در ارتباط با سرور: " + err.message);
  }
}

function showResultModal(result, downloadUrl) {
  document.getElementById("cert-student-name").textContent = result.student_name;
  document.getElementById("cert-student-id").textContent = result.student_id;
  document.getElementById("cert-score").textContent = `${result.score} از ${result.total_points}`;
  document.getElementById("cert-passed-count").textContent = `${result.passed_questions.length} سؤال`;
  const hintsCount = result.hints_count || (result.hints_used ? result.hints_used.length : 0);
  document.getElementById("cert-hints-count").textContent = `${hintsCount} مورد (${hintsCount * 3} نمره کسر شد)`;
  document.getElementById("cert-time").textContent = new Date(result.timestamp).toLocaleString("fa-IR");
  document.getElementById("cert-signature").textContent = result.signature;

  const dlBtn = document.getElementById("btn-download-cert");
  dlBtn.href = downloadUrl;

  document.getElementById("result-modal").style.display = "flex";
}
