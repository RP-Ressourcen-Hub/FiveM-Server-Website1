from flask import render_template, flash, redirect, url_for, request, abort, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from datetime import datetime

from app import app, db
from app.models import User, RulesSection, Rule, ForumCategory, ForumTopic, ForumPost
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm
from app.forms import ResetPasswordForm, PostForm, TopicForm

# Aktualisiere den "Zuletzt gesehen" Zeitstempel
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# Index / Home Route
@app.route('/')
@app.route('/index')
def index():
    # Für die Startseite können wir aktuelle Ankündigungen abrufen
    announcements = ForumTopic.query.join(ForumCategory).filter(
        ForumCategory.title == 'Ankündigungen'
    ).order_by(ForumTopic.created_at.desc()).limit(3).all()
    
    # Serverstatistiken
    user_count = User.query.count()
    
    return render_template('index.html', title='Home', 
                          announcements=announcements,
                          user_count=user_count)

# Regeln anzeigen
@app.route('/rules')
def rules():
    sections = RulesSection.query.order_by(RulesSection.order).all()
    return render_template('rules.html', title='Serverregeln', sections=sections)

# Forum Übersicht
@app.route('/forum')
def forum():
    categories = ForumCategory.query.order_by(ForumCategory.order).all()
    user_count = User.query.count()
    topic_count = ForumTopic.query.count()
    post_count = ForumPost.query.count()
    return render_template('forum/index.html', 
                          title='Forum', 
                          categories=categories, 
                          ForumTopic=ForumTopic,
                          user_count=user_count,
                          topic_count=topic_count,
                          post_count=post_count)

# Kategorie anzeigen
@app.route('/forum/category/<int:id>')
def forum_category(id):
    category = ForumCategory.query.get_or_404(id)
    
    # Private Kategorien nur für eingeloggte Benutzer
    if category.is_private and not current_user.is_authenticated:
        flash('Sie müssen angemeldet sein, um auf diese Kategorie zuzugreifen.', 'warning')
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    topics = ForumTopic.query.filter_by(category_id=id)\
                            .order_by(ForumTopic.is_pinned.desc(), ForumTopic.updated_at.desc())\
                            .paginate(page=page, per_page=app.config['POSTS_PER_PAGE'])
    
    return render_template('forum/category.html', title=category.title, 
                          category=category, topics=topics, ForumPost=ForumPost)

# Thema anzeigen
@app.route('/forum/topic/<int:id>')
def forum_topic(id):
    topic = ForumTopic.query.get_or_404(id)
    
    # Erhöhe die Ansichtszahl
    topic.views += 1
    db.session.commit()
    
    page = request.args.get('page', 1, type=int)
    posts = ForumPost.query.filter_by(topic_id=id)\
                           .order_by(ForumPost.created_at.asc())\
                           .paginate(page=page, per_page=app.config['POSTS_PER_PAGE'])
    
    return render_template('forum/topic.html', title=topic.title, 
                          topic=topic, posts=posts)

# Neues Thema erstellen
@app.route('/forum/category/<int:category_id>/new_topic', methods=['GET', 'POST'])
@login_required
def new_topic(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    form = TopicForm()
    form.category_id.data = category.id  # Kategorie vorauswählen
    
    if form.validate_on_submit():
        topic = ForumTopic(
            title=form.title.data,
            category_id=category.id,
            user_id=current_user.id
        )
        db.session.add(topic)
        db.session.flush()  # ID generieren lassen
        
        # Ersten Beitrag zum Thema hinzufügen
        post = ForumPost(
            content=form.content.data,
            topic_id=topic.id,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        
        flash('Dein Thema wurde erfolgreich erstellt!', 'success')
        return redirect(url_for('forum_topic', id=topic.id))
    
    return render_template('forum/new_topic.html', title='Neues Thema', 
                          form=form, category=category)

# Neue Antwort schreiben
@app.route('/forum/topic/<int:topic_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Überprüfen, ob das Thema gesperrt ist
    if topic.is_locked and not (current_user.is_admin or current_user.is_mod):
        flash('Dieses Thema ist gesperrt.', 'warning')
        return redirect(url_for('forum_topic', id=topic.id))
    
    form = PostForm()
    
    if form.validate_on_submit():
        post = ForumPost(
            content=form.content.data,
            topic_id=topic.id,
            user_id=current_user.id
        )
        db.session.add(post)
        
        # Aktualisiere das Thema (Zeitstempel)
        topic.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Deine Antwort wurde erfolgreich hinzugefügt!', 'success')
        return redirect(url_for('forum_topic', id=topic.id))
    
    return render_template('forum/reply.html', title=f'Antworten: {topic.title}', 
                          form=form, topic=topic)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Hinweis: LoginForm wird später in forms.py definiert
    # Dies ist ein Platzhalter für die Implementierung
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Ungültiger Benutzername oder Passwort', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        
        flash(f'Willkommen zurück, {user.username}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Anmelden', form=form)

# Logout Route
@app.route('/logout')
def logout():
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'success')
    return redirect(url_for('index'))

# Registrierung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # E-Mail-Bestätigung senden
        if app.config['EMAIL_CONFIRMATION_REQUIRED']:
            from app.email import send_confirmation_email
            send_confirmation_email(user)
            flash('Registrierung erfolgreich! Bitte bestätige deine E-Mail-Adresse, um dein Konto zu aktivieren.', 'success')
        else:
            flash('Registrierung erfolgreich! Du kannst dich jetzt anmelden.', 'success')
            
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', title='Registrieren', form=form)

# E-Mail-Bestätigung
@app.route('/confirm/<token>')
def confirm_email(token):
    from app.email import confirm_token
    
    if current_user.is_authenticated and current_user.email_confirmed:
        flash('Deine E-Mail-Adresse wurde bereits bestätigt.', 'info')
        return redirect(url_for('index'))
    
    email = confirm_token(token)
    if not email:
        flash('Der Bestätigungslink ist ungültig oder abgelaufen.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Die E-Mail-Adresse konnte nicht gefunden werden.', 'danger')
        return redirect(url_for('index'))
    
    if user.email_confirmed:
        flash('Deine E-Mail-Adresse wurde bereits bestätigt.', 'info')
    else:
        user.email_confirmed = True
        user.email_confirmed_at = datetime.utcnow()
        db.session.commit()
        flash('Vielen Dank für die Bestätigung deiner E-Mail-Adresse!', 'success')
    
    # Wenn Benutzer bereits angemeldet ist, zum Index weiterleiten
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Andernfalls zum Login weiterleiten
    return redirect(url_for('login'))

# Bestätigungs-E-Mail erneut senden
@app.route('/resend-confirmation')
@login_required
def resend_confirmation():
    if current_user.email_confirmed:
        flash('Deine E-Mail-Adresse wurde bereits bestätigt.', 'info')
        return redirect(url_for('index'))
    
    from app.email import send_confirmation_email
    send_confirmation_email(current_user)
    flash('Eine neue Bestätigungs-E-Mail wurde gesendet.', 'success')
    return redirect(url_for('index'))

# Profil anzeigen
@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Zeige die letzten Beiträge des Benutzers
    posts = ForumPost.query.filter_by(user_id=user.id)\
                           .order_by(ForumPost.created_at.desc())\
                           .limit(5).all()
    
    return render_template('user/profile.html', title=f'Profil von {user.username}',
                          user=user, posts=posts)

# Platzhalter für weitere Benutzer-Funktionen (werden später implementiert)
# - Profil bearbeiten
# - Passwort zurücksetzen
# - Benutzeravatar ändern

# Admin Routes (nur für Administratoren zugänglich)
@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Überprüfen, ob der Benutzer ein Administrator ist
    if not current_user.is_admin:
        flash('Du hast keinen Zugriff auf den Admin-Bereich.', 'danger')
        return redirect(url_for('index'))
    
    # Statistiken abrufen
    user_count = User.query.count()
    topic_count = ForumTopic.query.count()
    post_count = ForumPost.query.count()
    rule_count = Rule.query.count()
    
    return render_template('admin/dashboard.html', title='Admin Dashboard',
                          user_count=user_count, topic_count=topic_count,
                          post_count=post_count, rule_count=rule_count)

@app.route('/admin/users')
@login_required
def admin_users():
    # Überprüfen, ob der Benutzer ein Administrator ist
    if not current_user.is_admin:
        flash('Du hast keinen Zugriff auf den Admin-Bereich.', 'danger')
        return redirect(url_for('index'))
    
    # Benutzer abrufen (paginiert)
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=20)
    
    return render_template('admin/users.html', title='Benutzerverwaltung', users=users)

@app.route('/admin/forum')
@login_required
def admin_forum():
    # Überprüfen, ob der Benutzer ein Administrator ist
    if not current_user.is_admin:
        flash('Du hast keinen Zugriff auf den Admin-Bereich.', 'danger')
        return redirect(url_for('index'))
    
    # Kategorien abrufen
    categories = ForumCategory.query.order_by(ForumCategory.order).all()
    
    return render_template('admin/forum.html', title='Forumverwaltung', categories=categories)

@app.route('/admin/rules')
@login_required
def admin_rules():
    # Überprüfen, ob der Benutzer ein Administrator ist
    if not current_user.is_admin:
        flash('Du hast keinen Zugriff auf den Admin-Bereich.', 'danger')
        return redirect(url_for('index'))
    
    # Regeln und Abschnitte abrufen
    sections = RulesSection.query.order_by(RulesSection.order).all()
    
    return render_template('admin/rules.html', title='Regelwerk-Verwaltung', sections=sections)

@app.route('/admin/settings')
@login_required
def admin_settings():
    # Überprüfen, ob der Benutzer ein Administrator ist
    if not current_user.is_admin:
        flash('Du hast keinen Zugriff auf den Admin-Bereich.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/settings.html', title='Server-Einstellungen')

# 404 Error Handler
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

# 500 Error Handler
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500