from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember_me = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')

class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('E-Mail', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Passwort', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Passwort wiederholen', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Dieser Benutzername ist bereits vergeben. Bitte wählen Sie einen anderen.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Diese E-Mail-Adresse wird bereits verwendet. Bitte wählen Sie eine andere.')

class EditProfileForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('E-Mail', validators=[DataRequired(), Email(), Length(max=120)])
    bio = TextAreaField('Über mich', validators=[Length(max=500)])
    steam_id = StringField('Steam ID', validators=[Length(max=64)])
    discord_id = StringField('Discord ID', validators=[Length(max=64)])
    submit = SubmitField('Speichern')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Dieser Benutzername ist bereits vergeben. Bitte wählen Sie einen anderen.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Diese E-Mail-Adresse wird bereits verwendet. Bitte wählen Sie eine andere.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Passwort zurücksetzen')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Neues Passwort', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Passwort wiederholen', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Passwort zurücksetzen')

class PostForm(FlaskForm):
    content = TextAreaField('Inhalt', validators=[DataRequired(), Length(min=1, max=10000)])
    submit = SubmitField('Antworten')

class TopicForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Inhalt', validators=[DataRequired(), Length(min=10, max=10000)])
    category_id = SelectField('Kategorie', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Thema erstellen')
    
    def __init__(self, *args, **kwargs):
        super(TopicForm, self).__init__(*args, **kwargs)
        from app.models import ForumCategory
        self.category_id.choices = [(c.id, c.title) for c in 
                                   ForumCategory.query.order_by(ForumCategory.title).all()]