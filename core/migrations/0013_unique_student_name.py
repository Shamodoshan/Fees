# Generated migration to add unique constraint to student name

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_studentmonthlystatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
