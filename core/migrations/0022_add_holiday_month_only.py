# Generated migration for HolidayMonth model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_add_monthly_payments_to_student'),
    ]

    operations = [
        migrations.CreateModel(
            name='HolidayMonth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('month', models.IntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')])),
                ('reason', models.TextField(blank=True, help_text='Optional reason for the holiday')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'core_holidaymonth',
                'unique_together': {('year', 'month')},
                'ordering': ['-year', 'month'],
                'indexes': [models.Index(fields=['year', 'month'], name='core_holida_year_779adf_idx')],
            },
        ),
    ]
