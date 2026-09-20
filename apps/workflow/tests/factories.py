from __future__ import annotations

import uuid

import factory
from django.utils import timezone

from apps.accounts.models import Role

# We define lightweight factories here (no heavy faker).
# Full factories with Faker can be added later in apps/accounts/factories.py etc.


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Role"
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"test_role_{n}")
    name = factory.Sequence(lambda n: f"Test Role {n}")
    is_active = True
    is_deleted = False
    priority = 100


class WorkflowDefinitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "workflow.WorkflowDefinition"
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"test_wf_{n}")
    name = factory.Sequence(lambda n: f"Test Workflow {n}")
    is_active = True
    version = 1


class StateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "workflow.State"

    workflow_definition = factory.SubFactory(WorkflowDefinitionFactory)
    code = factory.Sequence(lambda n: f"state_{n}")
    name = factory.Sequence(lambda n: f"State {n}")
    is_initial = False
    is_final = False


class TransitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "workflow.Transition"

    workflow_definition = factory.SubFactory(WorkflowDefinitionFactory)
    from_state = factory.SubFactory(StateFactory)
    to_state = factory.SubFactory(StateFactory)
    name = factory.Sequence(lambda n: f"transition_{n}")
    allowed_role_codes = []
    requires_comment = False
    guard_expression = {}


class InstanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "workflow.Instance"

    workflow_definition = factory.SubFactory(WorkflowDefinitionFactory)
    requester = factory.SubFactory("apps.accounts.tests.UserFactory")
    title = factory.Sequence(lambda n: f"Instance {n}")
    status = "running"
    subject_person = None  # optional FK — set explicitly in tests