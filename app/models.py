from datetime import datetime
from app import db, login, bcrypt
from flask_login import UserMixin
from sqlalchemy.sql import func

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_mod = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(200), default='default-avatar.png')
    bio = db.Column(db.Text, default='')
    steam_id = db.Column(db.String(64), nullable=True)
    discord_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # Neue Felder für E-Mail-Verifizierung
    email_confirmed = db.Column(db.Boolean, default=False)
    email_confirmed_at = db.Column(db.DateTime, nullable=True)
    
    # Beziehungen
    topics = db.relationship('ForumTopic', backref='author', lazy='dynamic')
    posts = db.relationship('ForumPost', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# Regelwerk Models
class RulesSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0)
    
    # Beziehungen
    rules = db.relationship('Rule', backref='section', lazy='dynamic', order_by='Rule.paragraph')
    
    def __repr__(self):
        return f'<RulesSection {self.title}>'

class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paragraph = db.Column(db.String(10), nullable=False)  # z.B. "§1.1"
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    punishment = db.Column(db.String(200), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('rules_section.id'), nullable=False)
    
    def __repr__(self):
        return f'<Rule {self.paragraph}: {self.title}>'

# Forum Models
class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='fas fa-comments')
    order = db.Column(db.Integer, default=0)
    is_private = db.Column(db.Boolean, default=False)
    
    # Beziehungen
    topics = db.relationship('ForumTopic', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ForumCategory {self.title}>'

class ForumTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    
    # Fremdschlüssel
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Beziehungen
    posts = db.relationship('ForumPost', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ForumTopic {self.title}>'

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime, nullable=True)
    
    # Fremdschlüssel
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topic.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<ForumPost by {self.user_id} in topic {self.topic_id}>'

# Hilfsfunktionen zum Erstellen von Beispieldaten
def create_admin_user():
    admin = User(
        username='admin',
        email='admin@example.com',
        is_admin=True,
        is_mod=True
    )
    admin.set_password('admin123')  # Sicheres Passwort in Produktion verwenden!
    db.session.add(admin)
    db.session.commit()
    print("Admin-Benutzer erstellt!")

def create_default_rules():
    # Erstellen der Regelwerk-Abschnitte
    sections = [
        RulesSection(title='Allgemeine Regeln', description='Grundlegende Regeln, die für alle Spieler gelten', order=1),
        RulesSection(title='Roleplay Richtlinien', description='Regeln für das Roleplay-Verhalten', order=2),
        RulesSection(title='Strafen und Konsequenzen', description='Mögliche Strafen bei Regelverstößen', order=3)
    ]
    
    for section in sections:
        db.session.add(section)
    
    db.session.commit()
    
    # Allgemeine Regeln
    rules = [
        Rule(paragraph='§1.1', title='Respektvoller Umgang', 
             content='Alle Spieler müssen respektvoll miteinander umgehen. Beleidigungen, Diskriminierung und Belästigung werden nicht toleriert.',
             punishment='Temporärer bis permanenter Bann je nach Schwere',
             section_id=1),
        
        Rule(paragraph='§1.2', title='Voice-Chat', 
             content='Im Voice-Chat dürfen nur RP-relevante Gespräche geführt werden. Störende Geräusche und Musik sind zu unterlassen.',
             punishment='Verwarnung bis temporärer Bann',
             section_id=1),
        
        Rule(paragraph='§1.3', title='Bugs und Exploits', 
             content='Das Ausnutzen von Bugs und Exploits ist strengstens untersagt und muss umgehend den Administratoren gemeldet werden.',
             punishment='Temporärer bis permanenter Bann',
             section_id=1),
        
        # Roleplay Richtlinien
        Rule(paragraph='§2.1', title='Charaktertod (PermaDeath)', 
             content='Der permanente Tod eines Charakters kann nur durch explizite Zustimmung des Spielers oder bei schwerwiegenden RP-Verstößen eintreten.',
             punishment='N/A',
             section_id=2),
        
        Rule(paragraph='§2.2', title='New-Life-Rule', 
             content='Nach dem Tod deines Charakters darfst du dich nicht an vorherige Ereignisse erinnern, die zum Tod geführt haben.',
             punishment='Verwarnung bis temporärer Bann',
             section_id=2),
        
        Rule(paragraph='§2.3', title='Powergaming', 
             content='Handlungen, die im echten Leben nicht möglich wären oder einem anderen Spieler keine Reaktionsmöglichkeit lassen, sind verboten.',
             punishment='Verwarnung bis temporärer Bann',
             section_id=2),
        
        Rule(paragraph='§2.4', title='Metagaming', 
             content='Die Nutzung von Informationen, die dein Charakter nicht IC (In-Character) erhalten hat, ist verboten.',
             punishment='Verwarnung bis temporärer Bann',
             section_id=2),
        
        # Strafen und Konsequenzen
        Rule(paragraph='§3.1', title='Verwarnungssystem', 
             content='Bei Regelverstößen wird ein Stufensystem angewendet: 1. Verwarnung, 2. Temporärer Bann (1-7 Tage), 3. Längerer Bann (bis zu 30 Tage), 4. Permanenter Bann.',
             punishment='N/A',
             section_id=3),
        
        Rule(paragraph='§3.2', title='Berufungsverfahren', 
             content='Gegen eine Strafe kann innerhalb von 7 Tagen Berufung im Discord eingelegt werden. Ein Administrator wird den Fall überprüfen.',
             punishment='N/A',
             section_id=3)
    ]
    
    for rule in rules:
        db.session.add(rule)
    
    db.session.commit()
    print("Standard-Regelwerk erstellt!")

def create_default_forum_categories():
    categories = [
        ForumCategory(title='Ankündigungen', description='Offizielle Server-Ankündigungen und Updates', icon='fas fa-bullhorn', order=1),
        ForumCategory(title='Allgemeine Diskussion', description='Allgemeine Diskussionen rund um den Server', icon='fas fa-comments', order=2),
        ForumCategory(title='Support', description='Hilfe bei Fragen und Problemen', icon='fas fa-life-ring', order=3),
        ForumCategory(title='Vorstellungen', description='Stellt euch und eure Charaktere vor', icon='fas fa-user-circle', order=4),
        ForumCategory(title='Whitelist-Bewerbungen', description='Bewerbt euch für die Whitelist des Servers', icon='fas fa-clipboard-check', order=5, is_private=True),
        ForumCategory(title='Fraktions-Bewerbungen', description='Bewerbungen für offizielle Fraktionen', icon='fas fa-users', order=6),
    ]
    
    for category in categories:
        db.session.add(category)
    
    db.session.commit()
    print("Standard-Forumkategorien erstellt!")