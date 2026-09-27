"""Lightweight factories + role/user helpers for the forms test suite."""
from __future__ import annotations

import factory
from django.contrib.auth import get_user_model

from apps.accounts.models import Role

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user_{n}")
    password = factory.django.Password("pass-12345")
    is_active = True

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for code in extracted:
                role, _ = Role.objects.get_or_create(
                    code=code, defaults={"name": code, "priority": 50}
                )
                self.assign_role(role)


_NATIONAL_CODE = iter(f"0000{n:06d}" for n in range(1000000))
_PERSON_SEQ = iter(range(100000))


def make_person(user=None, person_type="student", **kwargs):
    """persons.Person linked to a user (Person.user OneToOne, reverse: user.person)."""
    from apps.persons.models import Person

    defaults = {
        "national_code": next(_NATIONAL_CODE),
        "first_name": "Test",
        "last_name": f"Person{next(_PERSON_SEQ)}",
        "mobile": "09120000000",
        "person_type": person_type,
    }
    defaults.update(kwargs)
    person = Person.objects.create(**defaults)
    if user is not None:
        person.user = user
        person.save(update_fields=["user", "updated_at"])
    return person


def make_term(**kwargs):
    from apps.academics.models import AcademicTerm

    defaults = {"title": "ترم تست", "start_date": "2026-01-01", "end_date": "2026-12-01"}
    defaults.update(kwargs)
    return AcademicTerm.objects.create(**defaults)


_CLASS_SEQ = iter(range(1000))


def make_class_group(term=None, teacher=None, **kwargs):
    from apps.academics.models import ClassGroup

    term = term or make_term()
    defaults = {
        "term": term,
        "code": f"cls-{next(_CLASS_SEQ)}",
        "name": "کلاس تست",
    }
    defaults.update(kwargs)
    group = ClassGroup.objects.create(**defaults)
    if teacher is not None:
        group.teacher = teacher
        group.save(update_fields=["teacher", "updated_at"])
    return group


def make_enrollment(class_group, student):
    from apps.academics.models import ClassEnrollment

    return ClassEnrollment.objects.create(
        class_group=class_group, student=student, enrollment_date="2026-02-01"
    )


def make_schema(slug="test-form", fields=None, **kwargs):
    from apps.forms.models import FormSchema

    fields = fields or [
        {"key": "title", "type": "text", "order": 1, "label": "عنوان", "required": True,
         "max_length": 200},
        {"key": "count", "type": "number", "order": 2, "label": "تعداد",
         "min": 0, "max": 100},
    ]
    defaults = {"slug": slug, "title": "فرم تست", "version": 1, "fields": fields}
    defaults.update(kwargs)
    if "workflow_config" not in defaults:
        workflow = defaults.get("workflow_definition")
        request_type = defaults.get("request_type")
        if request_type is not None:
            workflow = getattr(request_type, "workflow_definition", None) or workflow
        if workflow is not None:
            defaults["workflow_config"] = {
                "execution_mode": "workflow",
                "allow_on_behalf": False,
                "eligible_initiator_roles": [],
                "routing_rules": [],
            }
    return FormSchema.objects.create(**defaults)
