import os
from celery import Celery

# Django settings module set karo
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_engine.settings')

app = Celery('stock_engine')

# Django settings se config uthao (namespace='CELERY')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Sare apps se tasks.py khud dhoond lo
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')