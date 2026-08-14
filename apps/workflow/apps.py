
# apps/workflow/apps.py
from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workflow"
    label = "workflow"
    verbose_name = "Workflow Engine"

    def ready(self) -> None:
        # import signals later
        pass
