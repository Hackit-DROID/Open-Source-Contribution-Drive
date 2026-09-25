/* ── SGGS Dashboard JS ───────────────────────────────────────────────── */
'use strict';

let currentPage = 1;
let currentSection = 'dashboard';
let searchDebounce = null;

// ─── Navigation ───────────────────────────────────────────────────────────
function switchSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`section-${name}`)?.classList.add('active');
  document.querySelector(`[data-section="${name}"]`)?.classList.add('active');
  currentSection = name;
  const titles = {
    dashboard: 'Dashboard Overview', students: 'Students',
    marks: 'Academic Marks', attendance: 'Attendance',
    library: 'Library', hostel: 'Hostel'
  };
  document.getElementById('pageTitle').textContent = titles[name] || name;
  if (name === 'students') loadStudents();
}

document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    switchSection(item.dataset.section);
  });
});

document.getElementById('menuToggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

// ─── Dashboard Stats ──────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const res = await fetch('/api/dashboard_stats');
    const d = await res.json();
    document.getElementById('stat-total').textContent = d.total_students;
    document.getElementById('stat-hostel').textContent = d.hostel_students;
    document.getElementById('stat-library').textContent = d.library_issued;
    document.getElementById('stat-attendance').textContent = d.low_attendance;
    document.getElementById('stat-avgmarks').textContent = d.avg_marks;
    document.getElementById('stat-overdue').textContent = d.overdue_books;
    renderCharts(d);
  } catch (e) { console.error('Dashboard load error:', e); }

  loadTopStudents();
  loadAttendanceAlerts();
}

// ─── Charts ───────────────────────────────────────────────────────────────
function renderCharts(d) {
  const branchColors = ['#4f8ef7','#a855f7','#22c55e','#f97316','#14b8a6'];
  const gradeColors  = ['#22c55e','#14b8a6','#4f8ef7','#a855f7','#f97316','#eab308','#ef4444'];

  // Branch Chart
  const bCtx = document.getElementById('branchChart').getContext('2d');
  new Chart(bCtx, {
    type: 'bar',
    data: {
      labels: d.branch_dist.map(b => b.branch.replace(' Engineering', '')),
      datasets: [{
        label: 'Students',
        data: d.branch_dist.map(b => b.count),
        backgroundColor: branchColors,
        borderRadius: 7,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.raw} students` } } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } }
      }
    }
  });

  // Grade Chart
  const gCtx = document.getElementById('gradeChart').getContext('2d');
  new Chart(gCtx, {
    type: 'doughnut',
    data: {
      labels: d.grade_dist.map(g => g.grade),
      datasets: [{ data: d.grade_dist.map(g => g.count), backgroundColor: gradeColors, borderWidth: 0 }]
    },
    options: {
      responsive: true, cutout: '62%',
      plugins: { legend: { position: 'bottom', labels: { color: '#64748b', boxWidth: 10, font: { size: 11 } } } }
    }
  });

  // Attendance Chart
  const aCtx = document.getElementById('attendanceChart').getContext('2d');
  new Chart(aCtx, {
    type: 'pie',
    data: {
      labels: d.attendance_dist.map(a => a.range),
      datasets: [{ data: d.attendance_dist.map(a => a.count), backgroundColor: ['#22c55e','#f97316','#ef4444'], borderWidth: 0 }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom', labels: { color: '#64748b', boxWidth: 10, font: { size: 11 } } } }
    }
  });
}

// ─── Top Students ────────────────────────────────────────────────────────
async function loadTopStudents() {
  const res = await fetch('/api/top_students');
  const data = await res.json();
  const tbody = document.getElementById('topStudentsBody');
  tbody.innerHTML = data.map((s, i) => `
    <tr>
      <td><span class="rank-badge">#${i + 1}</span></td>
      <td>${s.name}</td>
      <td style="color:var(--text-muted);font-size:12px">${s.branch.split(' ')[0]}</td>
      <td><span class="pill total">${s.avg}</span></td>
    </tr>
  `).join('');
}

// ─── Attendance Alerts ───────────────────────────────────────────────────
async function loadAttendanceAlerts() {
  const res = await fetch('/api/attendance_alerts');
  const data = await res.json();
  const tbody = document.getElementById('attendanceAlertsBody');
  tbody.innerHTML = data.map(s => {
    const cls = s.avg_att < 60 ? 'alert-low' : 'alert-mid';
    return `<tr>
      <td>${s.name}</td>
      <td style="color:var(--text-muted);font-size:12px">${s.roll_no}</td>
      <td><span class="${cls}">${s.avg_att}%</span></td>
    </tr>`;
  }).join('');
}

// ─── Students Table ───────────────────────────────────────────────────────
async function loadStudents(page = 1) {
  currentPage = page;
  const search = document.getElementById('studentSearch').value;
  const branch = document.getElementById('branchFilter').value;
  const year   = document.getElementById('yearFilter').value;
  const hostel = document.getElementById('hostelFilter').value;

  const params = new URLSearchParams({ search, branch, year, hostel, page, per_page: 10 });
  const res  = await fetch(`/api/students?${params}`);
  const data = await res.json();

  document.getElementById('resultCount').textContent = `${data.total} students found`;
  const tbody = document.getElementById('studentsBody');

  if (data.students.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:30px;color:var(--text-muted)">No students found</td></tr>';
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  tbody.innerHTML = data.students.map(s => {
    const hostelBadge = s.hostel_name
      ? `<span class="badge-hostel">🏢 ${s.hostel_name}</span>`
      : `<span class="badge-day">🏠 Day Scholar</span>`;

    let attCls = 'badge-att-ok';
    if (s.avg_attendance < 60) attCls = 'badge-att-danger';
    else if (s.avg_attendance < 75) attCls = 'badge-att-warn';

    return `<tr>
      <td style="font-weight:600;color:var(--accent-blue)">${s.roll_no}</td>
      <td>${s.name}</td>
      <td style="font-size:12px;color:var(--text-muted)">${s.branch}</td>
      <td style="text-align:center">${s.year}</td>
      <td><span class="pill total">${s.avg_marks ?? '—'}</span></td>
      <td><span class="${attCls}">${s.avg_attendance ?? '—'}%</span></td>
      <td style="text-align:center">${s.books_issued ?? 0} 📚</td>
      <td>${hostelBadge}</td>
      <td><button class="btn-view" onclick="openStudentModal(${s.id})">View</button></td>
    </tr>`;
  }).join('');

  renderPagination(data.page, data.total_pages);
}

function renderPagination(current, total) {
  const el = document.getElementById('pagination');
  if (total <= 1) { el.innerHTML = ''; return; }
  let html = `<button ${current === 1 ? 'disabled' : ''} onclick="loadStudents(${current - 1})">‹</button>`;
  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || Math.abs(i - current) <= 1) {
      html += `<button class="${i === current ? 'active' : ''}" onclick="loadStudents(${i})">${i}</button>`;
    } else if (Math.abs(i - current) === 2) {
      html += `<span style="color:var(--text-muted);padding:0 4px">…</span>`;
    }
  }
  html += `<button ${current === total ? 'disabled' : ''} onclick="loadStudents(${current + 1})">›</button>`;
  el.innerHTML = html;
}

// Filters
['studentSearch','branchFilter','yearFilter','hostelFilter'].forEach(id => {
  document.getElementById(id)?.addEventListener('input', () => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => loadStudents(1), 300);
  });
});

// Branches dropdown
async function populateBranches() {
  const res = await fetch('/api/branches');
  const branches = await res.json();
  const sel = document.getElementById('branchFilter');
  branches.forEach(b => {
    const opt = document.createElement('option');
    opt.value = b; opt.textContent = b;
    sel.appendChild(opt);
  });
}

// ─── Student Modal ────────────────────────────────────────────────────────
async function openStudentModal(studentId) {
  const overlay = document.getElementById('modalOverlay');
  const content = document.getElementById('modalContent');
  overlay.classList.add('open');
  content.innerHTML = '<div style="padding:40px;text-align:center"><div class="spinner"></div></div>';

  const res  = await fetch(`/api/student/${studentId}`);
  const data = await res.json();
  const s    = data.student;
  const initials = s.name.split(' ').map(n => n[0]).join('').slice(0, 2);

  content.innerHTML = `
    <div class="modal-header">
      <div class="modal-avatar">${initials}</div>
      <div>
        <div class="modal-student-name">${s.name}</div>
        <div class="modal-student-meta">
          ${s.roll_no} &nbsp;·&nbsp; ${s.branch} &nbsp;·&nbsp; Year ${s.year}, Div ${s.division}
          &nbsp;·&nbsp; ${s.email}
        </div>
      </div>
    </div>
    <div class="modal-tabs">
      <div class="modal-tab active" onclick="showTab('info')">Info</div>
      <div class="modal-tab" onclick="showTab('marks')">📊 Marks</div>
      <div class="modal-tab" onclick="showTab('attendance')">📅 Attendance</div>
      <div class="modal-tab" onclick="showTab('library')">📚 Library</div>
      <div class="modal-tab" onclick="showTab('hostel')">🏢 Hostel</div>
    </div>
    <div class="modal-body">
      ${renderInfoTab(s)}
      ${renderMarksTab(data.marks)}
      ${renderAttendanceTab(data.attendance)}
      ${renderLibraryTab(data.library)}
      ${renderHostelTab(data.hostel)}
    </div>
  `;
}

function showTab(name) {
  document.querySelectorAll('.modal-tab').forEach((t, i) => {
    const names = ['info','marks','attendance','library','hostel'];
    t.classList.toggle('active', names[i] === name);
  });
  document.querySelectorAll('.modal-tab-content').forEach(c => {
    c.classList.toggle('active', c.dataset.tab === name);
  });
}

function renderInfoTab(s) {
  return `<div class="modal-tab-content active" data-tab="info">
    <div class="student-info-grid">
      ${infoItem('Full Name', s.name)}
      ${infoItem('Roll Number', s.roll_no)}
      ${infoItem('Branch', s.branch)}
      ${infoItem('Year', `Year ${s.year}`)}
      ${infoItem('Division', s.division)}
      ${infoItem('Email', s.email)}
      ${infoItem('Phone', s.phone)}
    </div>
  </div>`;
}

function infoItem(label, value) {
  return `<div class="info-item"><div class="info-label">${label}</div><div class="info-value">${value}</div></div>`;
}

function renderMarksTab(marks) {
  const rows = marks.map(m => {
    const gradeClass = `grade-${m.grade.replace('+','p')}`;
    return `<div class="subject-row">
      <span class="subject-name">${m.subject}</span>
      <div class="marks-pills">
        <span class="pill ise1">ISE1: ${m.ise1}</span>
        <span class="pill ise2">ISE2: ${m.ise2}</span>
        <span class="pill endsem">End: ${m.end_sem}</span>
        <span class="pill total">Total: ${m.total}</span>
      </div>
      <span class="grade-badge ${gradeClass}">${m.grade}</span>
    </div>`;
  }).join('');
  return `<div class="modal-tab-content" data-tab="marks">${rows}</div>`;
}

function renderAttendanceTab(attendance) {
  const rows = attendance.map(a => {
    const pct = a.percentage;
    const color = pct >= 75 ? '#22c55e' : pct >= 60 ? '#f97316' : '#ef4444';
    return `<div class="subject-row">
      <span class="subject-name">${a.subject}</span>
      <div style="color:var(--text-muted);font-size:12px">${a.attended}/${a.total_lectures} lectures</div>
      <div class="att-bar-wrap">
        <div class="att-bar-bg"><div class="att-bar-fill" style="width:${pct}%;background:${color}"></div></div>
        <div class="att-pct" style="color:${color}">${pct}%</div>
      </div>
    </div>`;
  }).join('');
  return `<div class="modal-tab-content" data-tab="attendance">${rows}</div>`;
}

function renderLibraryTab(books) {
  if (!books.length) return `<div class="modal-tab-content" data-tab="library"><p class="no-books">No library records found.</p></div>`;
  const rows = books.map(b => {
    const stCls = b.status === 'Returned' ? 'status-returned' : b.status === 'Overdue' ? 'status-overdue' : 'status-issued';
    return `<tr>
      <td>${b.book_title}</td>
      <td style="color:var(--text-muted);font-size:12px">${b.book_author}</td>
      <td>${b.issue_date}</td>
      <td>${b.due_date}</td>
      <td><span class="${stCls}">${b.status}</span></td>
      <td>${b.fine > 0 ? `<span style="color:var(--accent-red)">₹${b.fine}</span>` : '—'}</td>
    </tr>`;
  }).join('');
  return `<div class="modal-tab-content" data-tab="library">
    <table class="lib-table">
      <thead><tr><th>Book Title</th><th>Author</th><th>Issue Date</th><th>Due Date</th><th>Status</th><th>Fine</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`;
}

function renderHostelTab(hostel) {
  if (!hostel) return `<div class="modal-tab-content" data-tab="hostel"><p class="no-hostel">This student is a Day Scholar and does not reside in the hostel.</p></div>`;
  return `<div class="modal-tab-content" data-tab="hostel">
    <div class="hostel-info-grid">
      ${infoItem('Hostel Name', hostel.hostel_name)}
      ${infoItem('Room Number', hostel.room_no)}
      ${infoItem('Block', hostel.block)}
      ${infoItem('Admitted Date', hostel.admitted_date)}
      ${infoItem('Fee Paid', `₹${hostel.fee_paid.toLocaleString()}`)}
      ${infoItem('Fee Due', hostel.fee_due > 0 ? `<span style="color:var(--accent-red)">₹${hostel.fee_due.toLocaleString()}</span>` : '<span style="color:var(--accent-green)">Nil</span>')}
    </div>
  </div>`;
}

// Close modal
document.getElementById('modalClose').addEventListener('click', () => {
  document.getElementById('modalOverlay').classList.remove('open');
});
document.getElementById('modalOverlay').addEventListener('click', e => {
  if (e.target === document.getElementById('modalOverlay'))
    document.getElementById('modalOverlay').classList.remove('open');
});

// Global search redirect
document.getElementById('globalSearch').addEventListener('input', e => {
  if (e.target.value.length > 0) {
    switchSection('students');
    document.getElementById('studentSearch').value = e.target.value;
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => loadStudents(1), 300);
  }
});

// ─── Init ─────────────────────────────────────────────────────────────────
(async function init() {
  await populateBranches();
  loadDashboard();
})();
