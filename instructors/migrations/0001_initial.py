from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('email', models.EmailField(unique=True)),
                ('phone', models.CharField(blank=True, default='', max_length=20)),
                ('cost_per_hour', models.DecimalField(decimal_places=2, max_digits=10)),
                ('gst_applicable', models.BooleanField(default=False)),
                ('gst_percentage', models.DecimalField(decimal_places=2, default=18.0, max_digits=5)),
                ('gstin', models.CharField(blank=True, default='', max_length=15)),
                ('status', models.CharField(
                    choices=[('active', 'Active'), ('inactive', 'Inactive')],
                    default='active',
                    max_length=10,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'instructors',
                'ordering': ['name'],
            },
        ),
    ]