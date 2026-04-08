# instructors/migrations/0002_batch_instructor_fk.py
from django.db import migrations


class Migration(migrations.Migration):
    """
    Placeholder migration — the actual FK column on the Batch table is added
    by core/migrations/0002_batch_instructor_fk.py.
    This file exists only so Django's migration state can resolve the
    dependency chain: core.0002 depends on instructors.0001, not instructors.0002.
    """

    dependencies = [
        ('instructors', '0001_initial'),
    ]

    operations = []