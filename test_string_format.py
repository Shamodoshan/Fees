
from django.template import Template, Context
try:
    t = Template('Result: "{{ v|stringformat:".2f" }}"')
    res = t.render(Context({"v": "1000.00"}))
    print(f"Output with string input: {res}")
    
    t2 = Template('Result: "{{ v|stringformat:".2f" }}"')
    from decimal import Decimal
    res2 = t2.render(Context({"v": Decimal("1000.00")}))
    print(f"Output with Decimal input: {res2}")

except Exception as e:
    print(f"Error: {e}")
