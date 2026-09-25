/*
 * Pen LMS — submission detail page actions (no build step).
 * All authorization lives on the server; on error we surface the API's
 * field-keyed payload or its `error` message verbatim.
 *
 * Reads context from window.__PEN_DETAIL_CTX__ (submission_detail.html).
 */
(function () {
  'use strict';

  var ctx = window.__PEN_DETAIL_CTX__ || {};
  if (!ctx.submissionId) return;

  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  function postJson(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: Object.assign(
        { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        window.penCsrfHeader ? window.penCsrfHeader() : {}
      ),
      body: JSON.stringify(body || {}),
    }).then(function (resp) {
      return resp.json().catch(function () { return {}; }).then(function (payload) {
        return { ok: resp.ok, status: resp.status, body: payload };
      });
    });
  }

  function failureMessage(res) {
    var b = res.body || {};
    var first = b.error || b.detail ||
      (b.non_field_errors && b.non_field_errors[0]) || null;
    if (!first) {
      var key = Object.keys(b)[0];
      if (key) {
        var v = b[key];
        first = key + ': ' + (Array.isArray(v) ? v.join('؛ ') : String(v));
      }
    }
    return first || ('خطا (' + res.status + ')');
  }

  var submitBtn = document.getElementById('do-submit');
  submitBtn && submitBtn.addEventListener('click', function () {
    submitBtn.disabled = true;
    submitBtn.setAttribute('aria-busy', 'true');
    postJson(ctx.requestId ? '/api/forms/requests/' + ctx.requestId + '/submit/' : ctx.submitUrl, {})
      .then(function (res) {
        if (res.status === 409) {
          window.penToast('این فرم قبلاً ارسال شده است.', 'danger');
          return;
        }
        if (!res.ok) {
          window.penToast(failureMessage(res), 'danger');
          return;
        }
        window.location.reload();
      })
      .catch(function (err) { window.penToast('خطا: ' + err, 'danger'); })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.removeAttribute('aria-busy');
      });
  });

  var transitionBtn = document.getElementById('do-transition');
  transitionBtn && transitionBtn.addEventListener('click', function () {
    var select = document.getElementById('transition-id');
    var comment = document.getElementById('transition-comment');
    if (!select || !select.value) return;
    transitionBtn.disabled = true;
    postJson(ctx.requestId ? '/api/forms/requests/' + ctx.requestId + '/transition/' : ctx.transitionUrl, {
      transition_id: select.value,
      comment: comment ? comment.value : '',
    })
      .then(function (res) {
        if (!res.ok) {
          window.penToast(failureMessage(res), 'danger');
          return;
        }
        window.location.reload();
      })
      .catch(function (err) { window.penToast('خطا: ' + err, 'danger'); })
      .finally(function () { transitionBtn.disabled = false; });
  });

  var commentForm = document.getElementById('comment-form');
  commentForm && commentForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var input = document.getElementById('comment-body');
    if (!input || !input.value.trim()) return;
    var button = commentForm.querySelector('button[type="submit"]');
    button && (button.disabled = true);
    postJson(ctx.commentsUrl, { body: input.value.trim() })
      .then(function (res) {
        if (!res.ok) {
          window.penToast(failureMessage(res), 'danger');
          return;
        }
        window.location.reload();
      })
      .catch(function (err) { window.penToast('خطا: ' + err, 'danger'); })
      .finally(function () { button && (button.disabled = false); });
  });
})();
