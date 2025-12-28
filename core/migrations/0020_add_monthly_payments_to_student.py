# Generated migration for adding monthly_payments field

from django.db import migrations, models
import django.core.serializers.json


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0019_merge_20251228_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='monthly_payments',
            field=models.JSONField(
                default=dict,
                encoder=django.core.serializers.json.DjangoJSONEncoder,
                help_text='Monthly payment status and amounts in JSON format'
            ),
        ),
    ]
