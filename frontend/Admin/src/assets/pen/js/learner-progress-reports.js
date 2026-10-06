/* Resolves the learner's permitted student record before loading reports. */
(function () {
  'use strict';

  var root = document.getElementById('progress-learner-page');
  if (!root) return;
  var row = document.getElementById('progress-learner-switch-row');
  var choices = document.getElementById('progress-learner-switch');
  var history = document.getElementById('progress-learner-history');
  var back = document.getElementById('progress-learner-back');
  var version = 0;

  function esc(value) { return window.htmlEscape ? window.htmlEscape(value) : String(value || ''); }
  function params() { return new URLSearchParams(location.search); }
  function showStudents(students, selected) {
    if (!students || students.length < 2) { row.hidden = true; return; }
    row.hidden = false;
    choices.innerHTML = students.map(function (student) {
      var active = student.id === selected;
      return '<button type="button" class="btn btn-sm ' + (active ? 'btn-primary' : 'btn-outline-primary') + '" data-student="' + esc(student.id) + '">' + esc(student.name) + '</button>';
    }).join('');
    choices.querySelectorAll('[data-student]').forEach(function (button) {
      button.addEventListener('click', function () { select(button.dataset.student); });
    });
  }
  function select(studentId) {
    var requestVersion = ++version;
    history.innerHTML = '<p class="text-muted">در حال دریافت گزارش‌ها…</p>';
    fetch('/api/education/portal/?student=' + encodeURIComponent(studentId), {credentials: 'same-origin'})
      .then(function (response) {
        return response.json().then(function (body) {
          if (!response.ok && response.status !== 403) throw new Error(body.detail || 'اطلاعات دانش‌آموز دریافت نشد.');
          return {ok: response.ok, body: body};
        });
      })
      .then(function (result) {
        if (requestVersion !== version) return;
        var students = result.body.students || [];
        showStudents(students, result.body.student && result.body.student.id);
        if (!result.ok || !result.body.student) {
          if (!studentId && students.length === 1) { select(students[0].id); return; }
          history.innerHTML = '<p class="pen-empty">برای مشاهدهٔ گزارش‌ها، دانش‌آموز را انتخاب کنید.</p>';
          return;
        }
        var chosen = result.body.student.id;
        var query = params(); query.set('student', chosen);
        window.history.replaceState(null, '', location.pathname + '?' + query.toString());
        back.href = '/workspace/portal/?student=' + encodeURIComponent(chosen);
        document.dispatchEvent(new CustomEvent('pen:learner-selected', {detail: {student: chosen}}));
      })
      .catch(function (error) {
        if (requestVersion === version) history.innerHTML = '<p class="pen-empty">' + esc(error.message) + '</p>';
      });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var studentId = params().get('student') || '';
    select(studentId);
  });
})();
