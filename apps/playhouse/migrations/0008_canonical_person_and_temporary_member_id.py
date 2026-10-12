import uuid

from django.db import migrations, models
import django.db.models.deletion


def link_existing_members(apps, schema_editor):
    Member = apps.get_model("playhouse", "PlayhouseMember")
    Person = apps.get_model("persons", "Person")
    db = schema_editor.connection.alias
    for member in Member.objects.using(db).select_related("person").iterator():
        person = member.person
        if person:
            if person.temporary_id and not member.temporary_id:
                member.temporary_id = person.temporary_id
                member.save(using=db, update_fields=["temporary_id"])
            continue
        code = (member.national_code or "").strip()
        if code:
            person = Person.objects.using(db).filter(
                national_code=code, is_deleted=False
            ).first()
            if person and Member.objects.using(db).filter(person_id=person.pk).exists():
                person = None
                # Preserve the legacy duplicate row without violating the
                # canonical person's unique national-code constraint.
                code = ""
        if person is None:
            person = Person.objects.using(db).create(
                national_code=code or None,
                first_name=member.first_name,
                last_name=member.last_name,
                mobile=member.guardian_mobile or "",
                person_type="student",
                is_temporary=not bool(code),
                temporary_id=uuid.uuid4() if not code else None,
            )
        member.person_id = person.pk
        member.temporary_id = person.temporary_id
        member.save(using=db, update_fields=["person", "temporary_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("playhouse", "0007_playhouse_cafe_preset"),
        ("persons", "0011_temporary_person_identity"),
    ]

    operations = [
        migrations.AddField(
            model_name="playhousemember",
            name="temporary_id",
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
        migrations.RunPython(link_existing_members, migrations.RunPython.noop),
    ]
