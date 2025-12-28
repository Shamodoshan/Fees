# Generated migration for StudentMonthlyStatus table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_draftexpense_structure'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentMonthlyStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('paid_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('Unpaid', 'Unpaid'), ('Half Paid', 'Half Paid'), ('Paid', 'Paid')], default='Unpaid', max_length=20)),
                ('student', models.ForeignKey(db_column='student_id', on_delete=models.deletion.CASCADE, to='core.student')),
            ],
            options={
                'unique_together': {('student', 'year', 'month')},
            },
        ),
    ]
