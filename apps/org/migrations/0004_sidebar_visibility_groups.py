from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("org", "0003_sidebar_visibility"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="sidebarvisibilityrule",
            name="uniq_org_sidebar_role_item_live",
        ),
        migrations.RemoveConstraint(
            model_name="sidebarvisibilityrule",
            name="org_sidebar_visibility_scope_valid",
        ),
        migrations.AddField(
            model_name="sidebarvisibilityrule",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sidebar_visibility_rules",
                to="auth.group",
            ),
        ),
        migrations.AddConstraint(
            model_name="sidebarvisibilityrule",
            constraint=models.UniqueConstraint(
                condition=models.Q(("group__isnull", True), ("is_deleted", False), ("user__isnull", True)),
                fields=("role_code", "item_key"),
                name="uniq_org_sidebar_role_item_live",
            ),
        ),
        migrations.AddConstraint(
            model_name="sidebarvisibilityrule",
            constraint=models.UniqueConstraint(
                condition=models.Q(("group__isnull", False), ("is_deleted", False)),
                fields=("group", "item_key"),
                name="uniq_org_sidebar_group_item_live",
            ),
        ),
        migrations.AddConstraint(
            model_name="sidebarvisibilityrule",
            constraint=models.CheckConstraint(
                condition=models.Q(models.Q(("group__isnull", True), ("user__isnull", True), models.Q(("role_code", ""), _negated=True)), models.Q(("group__isnull", True), ("role_code", ""), ("user__isnull", False)), models.Q(("group__isnull", False), ("role_code", ""), ("user__isnull", True)), _connector="OR"),
                name="org_sidebar_visibility_scope_valid",
            ),
        ),
    ]
