import os

class Config:
    # Konfigurationsvariablen für die Anwendung
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sichere-geheime-schluessel-fuer-entwicklung'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "sslmode": "require"
        }
    }
    
    # Server-Informationen
    SERVER_NAME = "Dein FiveM Roleplay Server"  # Ändern Sie dies zu Ihrem tatsächlichen Servernamen
    SERVER_IP = "connect yourserver.com"  # Ändern Sie dies zur tatsächlichen Server-IP oder Domain
    DISCORD_LINK = "https://discord.gg/yourserver"  # Ändern Sie dies zu Ihrem Discord-Link
    
    # Forumeinstellungen
    POSTS_PER_PAGE = 10
    
    # E-Mail-Einstellungen
    MAIL_DEFAULT_SENDER = "noreply@yourserver.com"
    SECURITY_PASSWORD_SALT = "wirklich-sicheres-salt-fuer-token-generierung"
    BASE_URL = "http://localhost:5000"
    EMAIL_CONFIRMATION_REQUIRED = True