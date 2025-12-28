# Generated migration for DraftExpense table structure change

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_alter_draftpayment_structure'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draftexpense',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.RenameField(
            model_name='draftexpense',
            old_name='expense_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='draftexpense',
            old_name='created_at',
            new_name='created_time',
        ),
        migrations.AlterField(
            model_name='draftexpense',
            name='created_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='draftexpense',
            name='oath_user',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='draftexpense',
            name='user',
            field=models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=models.deletion.SET_NULL, to='auth.user'),
        ),
        migrations.AlterField(
            model_name='draftexpense',
            name='status',
            field=models.CharField(choices=[('Draft', 'Draft'), ('Accepted', 'Accepted'), ('Declined', 'Declined')], default='Draft', max_length=20),
        ),
    ]
