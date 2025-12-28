# Generated migration for Student table structure change

from django.db import migrations, models
import django.utils.timezone


class SafeRemoveField(migrations.operations.base.Operation):
    reduces_to_sql = True
    reversible = True

    def __init__(self, model_name, name):
        self.model_name = model_name
        self.name = name

    def state_forwards(self, app_label, state):
        try:
            state.remove_field(app_label, self.model_name.lower(), self.name)
        except KeyError:
            pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = from_state.apps.get_model(app_label, self.model_name)
        try:
            field = model._meta.get_field(self.name)
        except Exception:
            return
        try:
            schema_editor.remove_field(model, field)
        except Exception:
            pass

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def describe(self):
        return f"Safely remove field {self.name} from {self.model_name}"


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_student_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='student',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='student',
            name='monthly_fee',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='student',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        SafeRemoveField(
            model_name='student',
            name='last_paid_date',
        ),
    ]
