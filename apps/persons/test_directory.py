"""Regression coverage for directory ordering and secondary person types."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.persons.models import Person, PersonTypeAssignment


class DirectoryTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser(
            username="directory-admin", password="test-only-password",
        )
        self.client.force_login(self.actor)
        self.people = [
            Person.objects.create(
                national_code=f"812345678{index}", first_name="Test",
                last_name=name, person_type=Person.Type.TEACHER,
            )
            for index, name in enumerate(["Alpha", "Beta", "Gamma"])
        ]

    def test_cursor_preserves_requested_order_without_count(self):
        response = self.client.get('/api/persons/', {'ordering': 'last_name', 'page_size': 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('count', data)
        self.assertEqual(data['results'][0]['last_name'], 'Alpha')
        from urllib.parse import urlsplit
        following = urlsplit(data['next'])
        data = self.client.get(f'{following.path}?{following.query}').json()
        self.assertEqual(data['results'][0]['last_name'], 'Beta')

    def test_guardian_group_includes_current_secondary_assignments_only(self):
        for person, expiry in zip(self.people, [None, timezone.now() - timedelta(days=1)]):
            PersonTypeAssignment.objects.create(
                person=person, type=Person.Type.GUARDIAN, valid_to=expiry,
            )
        response = self.client.get('/api/persons/', {'role': 'guardian'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row['id'] for row in response.json()['results']],
            [str(self.people[0].pk)],
        )
