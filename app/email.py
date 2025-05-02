import os
import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import current_app, url_for, render_template
from itsdangerous import URLSafeTimedSerializer

def get_serializer():
    """Erstellt einen sicheren Serializer für Token-Generierung."""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_confirmation_token(email):
    """Erstellt ein Token für E-Mail-Bestätigung."""
    serializer = get_serializer()
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=86400):  # 24 Stunden
    """Bestätigt ein Token für E-Mail-Bestätigung."""
    serializer = get_serializer()
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except:
        return False

def send_email(to_email, subject, template_name, **kwargs):
    """Sendet eine E-Mail mit SendGrid."""
    # Sicherstellen, dass der API-Key vorhanden ist
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if not sendgrid_key:
        current_app.logger.error('SendGrid API-Key fehlt. E-Mail kann nicht gesendet werden.')
        return False
    
    # Hinzufügen von aktuellen Datum für die Templates
    kwargs['now'] = datetime.datetime.utcnow()
    kwargs['config'] = current_app.config
    
    # HTML-Inhalt aus Template rendern
    html_content = render_template(f'email/{template_name}.html', **kwargs)
    
    # SendGrid-Nachricht erstellen
    message = Mail(
        from_email=Email(current_app.config['MAIL_DEFAULT_SENDER']),
        to_emails=To(to_email),
        subject=subject,
        html_content=html_content
    )
    
    # E-Mail senden
    try:
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        current_app.logger.info(f'E-Mail an {to_email} gesendet. Status: {response.status_code}')
        return True
    except Exception as e:
        current_app.logger.error(f'Fehler beim Senden der E-Mail: {e}')
        return False

def send_confirmation_email(user):
    """Sendet eine Bestätigungs-E-Mail an einen neuen Benutzer."""
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    
    return send_email(
        to_email=user.email,
        subject='Bitte bestätige deine E-Mail-Adresse',
        template_name='confirmation_email',
        user=user,
        confirm_url=confirm_url
    )

def send_password_reset_email(user):
    """Sendet eine E-Mail zum Zurücksetzen des Passworts."""
    token = generate_confirmation_token(user.email)
    reset_url = url_for('reset_password', token=token, _external=True)
    
    return send_email(
        to_email=user.email,
        subject='Passwort zurücksetzen',
        template_name='password_reset_email',
        user=user,
        reset_url=reset_url
    )