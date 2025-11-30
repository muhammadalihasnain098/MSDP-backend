#!/bin/bash
# Quick Setup Script for MSDP Backend (Linux/Mac)

echo "🚀 MSDP Backend Setup Script"
echo "================================"
echo ""

# Check Python version
echo "📦 Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $python_version =~ Python\ 3\.(1[0-9]|[2-9][0-9]) ]]; then
    echo "✓ $python_version detected"
else
    echo "✗ Python 3.10+ required. Please install from python.org"
    exit 1
fi

# Create virtual environment
echo ""
echo "🌍 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "✓ Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file
echo ""
echo "⚙️  Setting up environment variables..."
if [ -f ".env" ]; then
    echo "✓ .env file already exists"
else
    cp .env.example .env
    
    # Generate SECRET_KEY
    secret_key=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    sed -i "s/your-secret-key-here-change-in-production/$secret_key/" .env
    
    echo "✓ .env file created with generated SECRET_KEY"
    echo "⚠️  Please update DATABASE_URL and REDIS_URL in .env"
fi

# Create storage directories
echo ""
echo "📁 Creating storage directories..."
mkdir -p storage/model_registry
mkdir -p media
echo "✓ Directories created"

# Run migrations
echo ""
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create superuser
echo ""
echo "👤 Create a superuser account..."
echo "   This will be your admin account for Django admin panel"
python manage.py createsuperuser

# Success message
echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Update .env file with your database and Redis URLs"
echo "2. Start Django: python manage.py runserver"
echo "3. Start Celery Worker: celery -A config worker -l info"
echo "4. Start Celery Beat: celery -A config beat -l info"
echo ""
echo "Admin panel: http://localhost:8000/admin/"
echo "API docs: See README.md"
echo ""
