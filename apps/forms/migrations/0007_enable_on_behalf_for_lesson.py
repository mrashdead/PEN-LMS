from django.db import migrations


def enable_lesson_on_behalf(apps, schema_editor):
    FormSchema = apps.get_model("forms", "FormSchema")
    database = schema_editor.connection.alias
    schemas = FormSchema.objects.using(database).filter(
        slug="lesson", is_active=True, is_deleted=False
    )
    for schema in schemas.iterator():
        config = dict(schema.workflow_config or {})
        config.setdefault("execution_mode", "workflow" if schema.workflow_definition_id else "direct")
        config["allow_on_behalf"] = True
        eligible = config.get("eligible_initiator_roles") or []
        if not eligible:
            eligible = list(
                schema.allowed_roles.using(database)
                .filter(is_active=True, is_deleted=False)
                .values_list("code", flat=True)
            )
        if not eligible:
            eligible = ["manager", "supervisor", "workflow_admin"]
        config["eligible_initiator_roles"] = eligible
        config.setdefault("routing_rules", [])
        schema.category = "courses"
        schema.workflow_config = config
        schema.save(using=database, update_fields=["category", "workflow_config"])


class Migration(migrations.Migration):
    dependencies = [("forms", "0006_formschema_category_formschema_workflow_config_and_more")]

    operations = [
        migrations.RunPython(enable_lesson_on_behalf, migrations.RunPython.noop),
    ]
