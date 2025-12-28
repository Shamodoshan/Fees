
import django
from django.conf import settings
from django.template import Template, Context
from decimal import Decimal

# Configure minimal settings if not already configured
if not settings.configured:
    settings.configure(
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }],
        INSTALLED_APPS=['django.contrib.humanize', 'core']
    )
    django.setup()

t_floatform = Template("{{ value|floatform:2 }}")
t_stringformat = Template("{{ value|stringformat:'.2f' }}")
c = Context({"value": Decimal("1000.00")})

print(f"Floatform: '{t_floatform.render(c)}'")
print(f"Stringformat: '{t_stringformat.render(c)}'")
