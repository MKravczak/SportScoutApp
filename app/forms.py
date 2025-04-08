# app/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, FloatField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User, Sport, Club


class LoginForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    remember_me = BooleanField('Zapamiętaj mnie')
    submit = SubmitField('Zaloguj się')


class RegistrationForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    password2 = PasswordField('Powtórz hasło', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Zarejestruj się')


    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ta nazwa użytkownika jest już zajęta.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ten adres email jest już zajęty.')


class ClubLoginForm(FlaskForm):
    name = StringField('Nazwa klubu', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    remember_me = BooleanField('Zapamiętaj mnie')
    submit = SubmitField('Zaloguj się')


class ClubRegistrationForm(FlaskForm):
    name = StringField('Nazwa klubu', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    password2 = PasswordField('Powtórz hasło', validators=[DataRequired(), EqualTo('password')])
    city = StringField('Miasto', validators=[DataRequired()])
    description = TextAreaField('Opis')
    logo = FileField('Logo klubu', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Tylko pliki obrazów!')])
    submit = SubmitField('Zarejestruj klub')

    def validate_name(self, name):
        club = Club.query.filter_by(name=name.data).first()
        if club:
            raise ValidationError('Klub o takiej nazwie już istnieje.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ten adres email jest już używany.')


class ClubForm(FlaskForm):
    name = StringField('Nazwa klubu', validators=[DataRequired()])
    city = StringField('Miasto', validators=[DataRequired()])
    description = TextAreaField('Opis')
    logo = FileField('Logo klubu', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Tylko pliki obrazów!')])
    submit = SubmitField('Zapisz')
    
    def validate_name(self, name):
        club = Club.query.filter_by(name=name.data).first()
        if club and club.id != getattr(self, '_obj_id', None):
            raise ValidationError('Klub o takiej nazwie już istnieje.')


class AssignScoutForm(FlaskForm):
    club = SelectField('Klub', coerce=int)
    submit = SubmitField('Przypisz')


class SportForm(FlaskForm):
    name = StringField('Nazwa dyscypliny', validators=[DataRequired()])
    description = TextAreaField('Opis')
    submit = SubmitField('Zapisz')
    
    def validate_name(self, name):
        # Sprawdzenie unikalności przy edycji
        sport = Sport.query.filter_by(name=name.data).first()
        if sport and sport.id != getattr(self, '_obj_id', None):
            raise ValidationError('Dyscyplina o takiej nazwie już istnieje.')


class UserRoleForm(FlaskForm):
    role = SelectField('Rola użytkownika', choices=[
        ('user', 'Użytkownik'),
        ('scout', 'Scout'),
        ('club_manager', 'Zarząd klubu'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    submit = SubmitField('Zapisz')


class PlayerForm(FlaskForm):
    first_name = StringField('Imię', validators=[DataRequired()])
    last_name = StringField('Nazwisko', validators=[DataRequired()])
    birth_date = DateField('Data urodzenia', format='%Y-%m-%d', validators=[DataRequired()])
    sport = SelectField('Dyscyplina', coerce=int, validators=[DataRequired()])
    position = StringField('Pozycja', validators=[DataRequired()])
    height = FloatField('Wzrost (cm)', validators=[DataRequired()])
    weight = FloatField('Waga (kg)', validators=[DataRequired()])
    photo = FileField('Zdjęcie zawodnika', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Tylko pliki obrazów!')])
    submit = SubmitField('Zapisz')