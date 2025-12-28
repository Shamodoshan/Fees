# Generated migration for DraftPayment table structure change

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_student_structure'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draftpayment',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.RenameField(
            model_name='draftpayment',
            old_name='created_at',
            new_name='created_date',
        ),
        migrations.AlterField(
            model_name='draftpayment',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='draftpayment',
            name='month',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='draftpayment',
            name='year',
            field=models.IntegerField(default=2025),
        ),
        migrations.AddField(
            model_name='draftpayment',
            name='oath_user',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='draftpayment',
            name='student',
            field=models.ForeignKey(blank=True, db_column='student_id', null=True, on_delete=models.deletion.SET_NULL, to='core.student'),
        ),
        migrations.AlterField(
            model_name='draftpayment',
            name='user',
            field=models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=models.deletion.SET_NULL, to='auth.user'),
        ),
        migrations.AlterField(
            model_name='draftpayment',
            name='status',
            field=models.CharField(choices=[('Draft', 'Draft'), ('Accepted', 'Accepted'), ('Declined', 'Declined'), ('Half Paid', 'Half Paid')], default='Draft', max_length=20),
        ),
        migrations.RemoveField(
            model_name='draftpayment',
            name='student_name',
        ),
    ]
