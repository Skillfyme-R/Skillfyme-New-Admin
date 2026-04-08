"""
Migration: add instructor FK + cost columns to the Batch model.
All fields are nullable → zero impact on existing data.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('instructors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='instructor',
            field=models.ForeignKey(
                blank=True,
                db_column='instructor_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='batches',
                to='instructors.instructor',
            ),
        ),
        migrations.AddField(
            model_name='batch',
            name='base_cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='batch',
            name='gst_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='batch',
            name='total_cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]