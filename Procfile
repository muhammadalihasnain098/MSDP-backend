# For Railway deployment
release: python manage.py migrate --noinput
web: gunicorn config.wsgi:application
worker: celery -A config worker -l info
beat: celery -A config beat -l info
