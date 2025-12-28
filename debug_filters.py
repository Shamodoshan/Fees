
from django.conf import settings
from django.template import Template, Context
from decimal import Decimal
import django

# Setup minimal settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'core'
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }],
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    )
    django.setup()

try:
    t = Template('Result: {{ v|stringformat:".2f" }}')
    c = Context({'v': Decimal('1000.00')})
    print(t.render(c))
except Exception as e:
    print(f"Error: {e}")
