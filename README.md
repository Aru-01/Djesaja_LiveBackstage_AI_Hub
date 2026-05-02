# LiveBackstage Automation System 🚀

LiveBackstage is a professional, AI-powered backend automation platform designed specifically for TikTok Live agencies. It streamlines the complex workflows of managing creators, tracking live performance, and generating daily reports, eliminating the need for repetitive manual data entry.

## ✨ Key Features

- **Automated Performance Tracking**: Real-time monitoring and data collection for TikTok Live creators.
- **AI-Driven Insights**: Advanced analytics using AI to provide actionable feedback on creator performance.
- **Creator & Manager Management**: Comprehensive system for managing creator profiles and agency manager permissions.
- **Daily Reporting Automation**: Generate professional performance reports automatically.
- **Scalable API Architecture**: Built with Django REST Framework for seamless integration with frontend dashboards.
- **Automated Data Scraping**: Integrated with Playwright for robust data collection from various sources.
- **Interactive API Documentation**: Fully documented endpoints via Swagger and Redoc.

## 🛠️ Tech Stack

- **Backend Framework**: [Django 6.0+](https://www.djangoproject.com/)
- **API Framework**: [Django REST Framework (DRF)](https://www.django-rest-framework.org/)
- **Database**: SQLite (Development) / PostgreSQL (Production ready)
- **Automation & Scraping**: [Playwright](https://playwright.dev/python/)
- **Authentication**: JWT (JSON Web Tokens) via SimpleJWT
- **API Documentation**: Swagger (drf-yasg) & Redoc
- **Configuration**: Python Decouple (Environment variables management)
- **Static Files**: WhiteNoise

## 🚀 Installation & Local Setup

Follow these steps to get the project running on your local machine:

### 1. Clone the Repository
```bash
git clone https://github.com/Aru-01/Djesaja_LiveBackstage_AI_Hub
cd Djesaja_LiveBackstage_AI_Hub
```

### 2. Set Up Virtual Environment
```bash
# Using venv
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
```bash
playwright install
```

### 5. Environment Configuration
Create a `.env` file in the root directory and add the following variables:
```env
SECRET_KEY=your_django_secret_key
DEBUG=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

### 6. Database Migrations
```bash
python manage.py migrate
```

### 7. Run the Server
```bash
python manage.py runserver
```
The API will be available at `http://127.0.0.1:8000/`.

## 📖 Usage & Documentation

Once the server is running, you can access the interactive API documentation at:
- **Swagger UI**: `http://127.0.0.1:8000/swagger/`
- **Redoc**: `http://127.0.0.1:8000/redoc/`

Use these interfaces to explore the available endpoints for `accounts`, `creators`, `managers`, and `ai_insights`.

## 📁 Folder Structure

```text
├── accounts/          # User authentication and profile management
├── ai_insights/       # AI-powered performance analysis logic
├── api/               # Core API serializers and views
├── creators/          # Creator-specific data and management
├── managers/          # Agency manager configurations
├── Djesaja_LiveBackstage/ # Main project settings and URLs
├── media/             # Storage for uploaded files
├── staticfiles/       # Collected static files
├── manage.py          # Django management script
└── requirements.txt   # Project dependencies
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Built with passion by **[Arif](https://www.linkedin.com/in/aru01/)** 🖤💻
