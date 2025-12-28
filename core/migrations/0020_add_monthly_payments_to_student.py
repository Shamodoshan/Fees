# Generated migration for adding monthly_payments field
 
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0019_merge_20251228_1404'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='student',
                    name='year',
                    field=models.IntegerField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='student',
                    name='month',
                    field=models.IntegerField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='student',
                    name='paid_amount',
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                migrations.AddField(
                    model_name='student',
                    name='payment_status',
                    field=models.CharField(choices=[('Unpaid', 'Unpaid'), ('Half Paid', 'Half Paid'), ('Paid', 'Paid')], default='Unpaid', max_length=20),
                ),
                migrations.DeleteModel(
                    name='StudentMonthlyStatus',
                ),
            ],
        ),
    ]
