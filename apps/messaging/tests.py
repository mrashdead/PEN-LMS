"""Tests for internal messaging (services + API)."""
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.messaging import services
from apps.messaging.models import Message, Thread, ThreadParticipant


class MessagingTestCase(TestCase):
    def setUp(self):
        self.manager_role = Role.objects.create(code="manager", name="مدیر")
        self.teacher_role = Role.objects.create(code="teacher", name="معلم")
        self.student_role = Role.objects.create(code="student", name="دانش‌آموز")

        self.boss = User.objects.create_user(username="boss", password="x", first_name="علی", last_name="مدیری")
        self.teacher = User.objects.create_user(username="teach", password="x", first_name="مریم", last_name="معلمی")
        self.student = User.objects.create_user(username="stud", password="x", first_name="رضا", last_name="دانشی")
        self.boss.assign_role(self.manager_role.code)
        self.teacher.assign_role(self.teacher_role.code)
        self.student.assign_role(self.student_role.code)

    # ── services ──────────────────────────────────────────────────────

    def test_staff_directory_excludes_students(self):
        ids = set(services.staff_directory().values_list("pk", flat=True))
        self.assertIn(self.boss.pk, ids)
        self.assertIn(self.teacher.pk, ids)
        self.assertNotIn(self.student.pk, ids)

    def test_start_thread_creates_participants_and_unread(self):
        thread = services.start_thread(
            sender=self.boss,
            recipient_ids=[str(self.teacher.pk)],
            subject="جلسهٔ فردا",
            body="ساعت ۱۰ بیایید.",
        )
        self.assertEqual(thread.participants.count(), 2)
        sender_row = thread.participants.get(user=self.boss)
        recv_row = thread.participants.get(user=self.teacher)
        self.assertEqual(sender_row.unread_count, 0)
        self.assertEqual(recv_row.unread_count, 1)
        self.assertEqual(thread.messages.count(), 1)

    def test_start_thread_rejects_non_staff_recipient(self):
        with self.assertRaises(services.MessagingError):
            services.start_thread(
                sender=self.boss,
                recipient_ids=[str(self.student.pk)],
                subject="x", body="y",
            )

    def test_start_thread_requires_subject_and_body(self):
        with self.assertRaises(services.MessagingError):
            services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="", body="hi")
        with self.assertRaises(services.MessagingError):
            services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="hi", body="")

    def test_reply_bumps_other_participants(self):
        thread = services.start_thread(
            sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b"
        )
        services.reply(sender=self.teacher, thread_id=thread.pk, body="چشم")
        self.assertEqual(thread.participants.get(user=self.boss).unread_count, 1)
        self.assertEqual(thread.participants.get(user=self.teacher).unread_count, 0)
        self.assertEqual(thread.messages.count(), 2)

    def test_reply_by_non_participant_rejected(self):
        thread = services.start_thread(
            sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b"
        )
        outsider = User.objects.create_user(username="out", password="x")
        outsider.assign_role(self.manager_role.code)
        with self.assertRaises(services.MessagingError):
            services.reply(sender=outsider, thread_id=thread.pk, body="hacked")

    def test_mark_read_and_total_unread(self):
        services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b")
        self.assertEqual(services.total_unread(self.teacher), 1)
        thread = Thread.objects.first()
        services.mark_thread_read(user=self.teacher, thread_id=thread.pk)
        self.assertEqual(services.total_unread(self.teacher), 0)

    def test_hide_is_viewer_only(self):
        thread = services.start_thread(
            sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b"
        )
        services.hide_thread(user=self.teacher, thread_id=thread.pk)
        self.assertFalse(ThreadParticipant.objects.filter(thread=thread, user=self.teacher, is_hidden=False).exists())
        # boss still sees it
        self.assertTrue(ThreadParticipant.objects.filter(thread=thread, user=self.boss, is_hidden=False).exists())


class MessagingAPITestCase(MessagingTestCase):
    def _login(self, user):
        self.client.force_login(user)

    def test_inbox_requires_staff(self):
        self._login(self.student)
        resp = self.client.get(reverse("messaging-inbox"))
        self.assertEqual(resp.status_code, 403)

    def test_inbox_lists_my_threads(self):
        services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b")
        self._login(self.teacher)
        resp = self.client.get(reverse("messaging-inbox"))
        self.assertEqual(resp.status_code, 200)
        rows = resp.json()["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["unread_count"], 1)

    def test_create_thread_via_api(self):
        self._login(self.boss)
        resp = self.client.post(
            reverse("messaging-thread-create"),
            {"recipients": [str(self.teacher.pk)], "subject": "hi", "body": "hello"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(services.total_unread(self.teacher), 1)

    def test_detail_404_for_non_participant(self):
        thread = services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b")
        outsider = User.objects.create_user(username="out2", password="x")
        outsider.assign_role(self.manager_role.code)
        self._login(outsider)
        resp = self.client.get(reverse("messaging-thread-detail", kwargs={"pk": thread.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_detail_marks_read(self):
        thread = services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b")
        self._login(self.teacher)
        resp = self.client.get(reverse("messaging-thread-detail", kwargs={"pk": thread.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["messages"]), 1)
        self.assertEqual(services.total_unread(self.teacher), 0)

    def test_reply_via_api(self):
        thread = services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b")
        self._login(self.teacher)
        resp = self.client.post(
            reverse("messaging-thread-reply", kwargs={"pk": thread.pk}),
            {"body": "سلام"}, content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(thread.messages.count(), 2)

    def test_unread_count_endpoint(self):
        services.start_thread(sender=self.boss, recipient_ids=[str(self.teacher.pk)], subject="s", body="b")
        self._login(self.teacher)
        resp = self.client.get(reverse("messaging-unread-count"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)

    def test_directory_excludes_self_and_students(self):
        self._login(self.boss)
        resp = self.client.get(reverse("messaging-directory"))
        ids = {u["id"] for u in resp.json()}
        self.assertIn(str(self.teacher.pk), ids)
        self.assertNotIn(str(self.boss.pk), ids)
        self.assertNotIn(str(self.student.pk), ids)
