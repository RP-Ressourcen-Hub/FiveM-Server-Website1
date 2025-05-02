import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

# Erstelle Flask-App
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(Config)

# Datenbankverbindung anpassen (Postgres)
db_url = app.config['SQLALCHEMY_DATABASE_URI']
if db_url and db_url.startswith('postgres:'):
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres:', 'postgresql:')

# Initialisiere Erweiterungen
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Bitte melde dich an, um diese Seite zu sehen.'
login.login_message_category = 'warning'
bcrypt = Bcrypt(app)

from app import models

# Erstelle DB, falls nicht vorhanden
with app.app_context():
    db.create_all()
    
    # Admin-Benutzer erstellen, falls nicht vorhanden
    from app.models import User
    if not User.query.filter_by(username='admin').first():
        from app.models import create_admin_user
        create_admin_user()
        
    # Standardregelwerk erstellen, falls nicht vorhanden
    from app.models import RulesSection, Rule
    if not RulesSection.query.first():
        from app.models import create_default_rules
        create_default_rules()
    
    # Standard-Forumkategorien erstellen, falls nicht vorhanden
    from app.models import ForumCategory
    if not ForumCategory.query.first():
        from app.models import create_default_forum_categories
        create_default_forum_categories()
        
# Importiere Routen (nach der DB-Initialisierung)
from app import routes