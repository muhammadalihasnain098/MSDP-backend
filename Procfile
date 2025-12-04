# For Railway deployment
release: python manage.py migrate --noinput && python generate_forecasts.py
web: gunicorn config.wsgi:application --timeout 300 --workers 2
worker: celery -A config worker -l info
beat: celery -A config beat -l info
