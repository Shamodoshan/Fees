
from django.conf import settings
from django.template import Template, Context
import django

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.auth', 'core'],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }]
    )
    django.setup()

try:
    # Test with string input mimicking request.POST
    t = Template('Result: "{{ v|stringformat:".2f" }}"')
    c = Context({'v': "1000.00"})
    print(f"Input string: {t.render(c)}")
except Exception as e:
    print(f"Error: {e}")
