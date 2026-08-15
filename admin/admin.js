// Trabuild Admin Dashboard JavaScript Logic

const API_BASE = window.location.origin;

document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadLicenses();
  loadCourses();
  
  // Set endpoint display
  const endpointEl = document.getElementById('apiEndpointText');
  if (endpointEl) endpointEl.innerText = API_BASE;
});

function switchTab(tabId) {
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  
  const target = document.getElementById(tabId);
  if (target) target.classList.add('active');
  if (event && event.target) event.target.classList.add('active');
}

// ----------------------------------------------------
// 1. Stats and Analytics
// ----------------------------------------------------
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/stats`);
    const data = await res.json();
    if (data.success) {
      document.getElementById('statTotalStudents').innerText = data.stats.total_students;
      document.getElementById('statActiveStudents').innerText = data.stats.active_students;
      document.getElementById('statBannedStudents').innerText = data.stats.banned_students;
      document.getElementById('statTotalLessons').innerText = data.stats.total_lessons;
    }
  } catch (err) {
    console.error("Error fetching stats:", err);
  }
}

// ----------------------------------------------------
// 2. Licenses & Students Management
// ----------------------------------------------------
async function loadLicenses() {
  const tbody = document.getElementById('licensesTableBody');
  tbody.innerHTML = '<tr><td colspan="8" class="text-center">جاري تحديث قائمة الطلاب...</td></tr>';

  try {
    const res = await fetch(`${API_BASE}/api/admin/licenses`);
    const data = await res.json();
    if (!data.success || !data.licenses.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center">لا توجد تراخيص منشأة بعد.</td></tr>';
      return;
    }

    tbody.innerHTML = '';
    data.licenses.forEach((item, index) => {
      const tr = document.createElement('tr');
      
      const isBanned = item.status === 'banned';
      const isWaiting = !item.hwid || item.status === 'waiting';
      
      let statusBadge = `<span class="badge badge-active">🟢 نشط ومفعل</span>`;
      if (isBanned) {
        statusBadge = `<span class="badge badge-banned">🚫 محظور</span>`;
      } else if (isWaiting) {
        statusBadge = `<span class="badge badge-waiting">🟡 بانتظار التفعيل</span>`;
      }

      const hwidDisplay = item.hwid 
        ? `<span class="hwid-tag" title="${item.hwid}">${item.hwid.substring(0, 14)}...</span>` 
        : `<span style="color:#94a3b8; font-size:11px;">لم يفعّل جهازه بعد</span>`;

      tr.innerHTML = `
        <td>${index + 1}</td>
        <td><strong>${item.student_name}</strong></td>
        <td>${item.phone || 'غير مسجل'}</td>
        <td><code style="color:#007ea7; font-weight:700;">${item.key}</code></td>
        <td>${hwidDisplay}</td>
        <td>${statusBadge}</td>
        <td><small style="color:#64748b;">${item.last_active || item.created_at}</small></td>
        <td>
          <div class="actions-group">
            <button class="btn btn-sm ${isBanned ? 'btn-success' : 'btn-danger'}" onclick="toggleBan('${item.key}')">
              ${isBanned ? 'فك الحظر ✅' : 'حظر 🚫'}
            </button>
            <button class="btn btn-sm btn-warning" onclick="resetHwid('${item.key}')" title="السماح للطالب بالتفعيل على حاسبة جديدة">
              تصفير 🔄
            </button>
            <button class="btn btn-sm" style="background:#fee2e2; color:#991b1b; border:1px solid #f87171;" onclick="deleteLicense('${item.key}', '${item.student_name}')" title="مسح الحساب نهائياً">
              مسح 🗑️
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading licenses:", err);
    tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="color:red;">خطأ في الاتصال بالسيرفر!</td></tr>';
  }
}

async function createLicense() {
  const name = document.getElementById('genName').value.trim();
  const phone = document.getElementById('genPhone').value.trim();
  const courseId = document.getElementById('genCourse').value;

  if (!name) {
    alert("يرجى إدخال اسم الطالب أولاً!");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/admin/licenses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, phone, course_id: courseId })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('newKeyText').innerText = data.license.key;
      document.getElementById('newKeyAlert').classList.remove('hidden');
      
      // Clear inputs
      document.getElementById('genName').value = '';
      document.getElementById('genPhone').value = '';

      loadLicenses();
      loadStats();
    } else {
      alert("خطأ: " + data.message);
    }
  } catch (err) {
    alert("فشل الاتصال بالسيرفر: " + err);
  }
}

function copyKey() {
  const key = document.getElementById('newKeyText').innerText;
  navigator.clipboard.writeText(key).then(() => {
    alert("تم نسخ مفتاح الترخيص بنجاح: " + key);
  });
}

async function toggleBan(key) {
  if (!confirm(`هل أنت متأكد من تغيير حالة الحظر لهذا الترخيص (${key})؟`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/admin/licenses/${key}/toggle-ban`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      loadLicenses();
      loadStats();
    }
  } catch (err) {
    alert("فشل تنفيذ الإجراء: " + err);
  }
}

async function resetHwid(key) {
  if (!confirm(`هل أنت متأكد من تصفير بصمة الجهاز للترخيص (${key})؟\nسيتمكن الطالب من تفعيله على جهاز جديد.`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/admin/licenses/${key}/reset-hwid`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      loadLicenses();
      loadStats();
    }
  } catch (err) {
    alert("فشل تنفيذ الإجراء: " + err);
  }
}

async function deleteLicense(key, name) {
  if (!confirm(`⚠️ تحذير: هل أنت متأكد من مسح حساب الطالب (${name}) نهائياً من المنظومة؟`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/admin/licenses/${key}/delete`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      loadLicenses();
      loadStats();
    } else {
      alert("خطأ: " + data.message);
    }
  } catch (err) {
    alert("فشل تنفيذ الإجراء: " + err);
  }
}

// ----------------------------------------------------
// 3. Courses & Lessons Management
// ----------------------------------------------------
async function loadCourses() {
  const container = document.getElementById('coursesContainer');
  container.innerHTML = '<p>جاري تحميل الكورسات...</p>';

  try {
    const res = await fetch(`${API_BASE}/api/courses`);
    const data = await res.json();
    if (!data.success || !data.courses.length) {
      container.innerHTML = '<p>لا توجد كورسات مضافة بعد.</p>';
      return;
    }

    container.innerHTML = '';
    data.courses.forEach(course => {
      const courseCard = document.createElement('div');
      courseCard.className = 'course-item';
      
      let lessonsHtml = '';
      if (!course.lessons || !course.lessons.length) {
        lessonsHtml = '<div style="color:#64748b; font-size:13px; padding:10px;">لا توجد محاضرات في هذا الكورس بعد.</div>';
      } else {
        course.lessons.forEach((lesson, i) => {
          lessonsHtml += `
            <div class="lesson-row">
              <div>
                <strong>${i + 1}. ${lesson.title}</strong>
                <div style="color:#64748b; font-size:12px; margin-top:2px;">
                  المدة: ${lesson.duration} | Bunny ID: <code>${lesson.bunny_id}</code>
                </div>
              </div>
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="badge badge-active">جاهز للبث</span>
                <button class="btn btn-sm" style="background:#fee2e2; color:#dc2626; border:1px solid #fecaca;" onclick="deleteLesson(${course.id}, ${lesson.id}, '${lesson.title}')" title="مسح هذه المحاضرة">
                  مسح 🗑️
                </button>
              </div>
            </div>
          `;
        });
      }

      courseCard.innerHTML = `
        <div class="course-item-header" style="display:flex; justify-content:space-between; align-items:center;">
          <div>📖 <strong id="courseTitle_${course.id}">${course.title}</strong> (${(course.lessons || []).length} محاضرة)</div>
          <button class="btn btn-sm btn-secondary" onclick="renameCourse(${course.id})">
            تعديل اسم الكورس ✏️
          </button>
        </div>
        <div class="lessons-list">${lessonsHtml}</div>
      `;
      container.appendChild(courseCard);
    });
  } catch (err) {
    console.error("Error loading courses:", err);
  }
}

async function renameCourse(courseId) {
  const currentTitleEl = document.getElementById(`courseTitle_${courseId}`);
  const currentTitle = currentTitleEl ? currentTitleEl.innerText : '';
  const newTitle = prompt("أدخل الاسم الجديد للكورس:", currentTitle);
  
  if (!newTitle || newTitle.trim() === '' || newTitle.trim() === currentTitle) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/admin/courses/${courseId}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle.trim() })
    });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      loadCourses();
    } else {
      alert("خطأ: " + data.message);
    }
  } catch (err) {
    alert("فشل تعديل اسم الكورس: " + err);
  }
}

async function deleteLesson(courseId, lessonId, title) {
  if (!confirm(`هل أنت متأكد من حذف المحاضرة:\n("${title}")؟`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/admin/courses/${courseId}/lessons/${lessonId}/delete`, {
      method: 'POST'
    });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      loadCourses();
      loadStats();
    } else {
      alert("خطأ: " + data.message);
    }
  } catch (err) {
    alert("فشل حذف المحاضرة: " + err);
  }
}

async function addLesson() {
  const title = document.getElementById('lessonTitle').value.trim();
  const duration = document.getElementById('lessonDuration').value.trim();
  const bunnyId = document.getElementById('bunnyId').value.trim();
  const streamUrl = document.getElementById('lessonUrl').value.trim();

  if (!title || !streamUrl) {
    alert("يرجى كتابة عنوان المحاضرة ورابط الفيديو أولاً!");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/admin/courses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        course_id: 1,
        title,
        duration: duration || "45:00 دقيقة",
        bunny_id: bunnyId,
        stream_url: streamUrl
      })
    });
    const data = await res.json();
    if (data.success) {
      alert("تمت إضافة المحاضرة بنجاح!");
      document.getElementById('lessonTitle').value = '';
      document.getElementById('lessonDuration').value = '';
      document.getElementById('bunnyId').value = '';
      document.getElementById('lessonUrl').value = '';
      loadCourses();
      loadStats();
    } else {
      alert("خطأ: " + data.message);
    }
  } catch (err) {
    alert("فشل الاتصال بالسيرفر: " + err);
  }
}
