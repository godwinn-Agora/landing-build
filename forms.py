from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField,  StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from wtforms.fields import EmailField


class ConnexionForm(FlaskForm):
    email = EmailField("Adresse email", validators=[DataRequired(), Email(message="Adresse email invalide"), Length(max=150)])
    mot_de_passe = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6, max=200)])
    submit = SubmitField("Se connecter")


class InscriptionForm(FlaskForm):
    email = EmailField("Adresse email", validators=[
        DataRequired(),
        Email(message="Adresse email invalide"),
        Length(max=150)
    ])

    mot_de_passe = PasswordField("Mot de passe", validators=[
        DataRequired(),
        Length(min=6, max=200)
    ])

    submit = SubmitField("S'inscrire")


class IdeeForm(FlaskForm):
    titre = StringField("Titre", validators=[DataRequired(), Length(max=100)])
    contenu = TextAreaField("Contenu", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Soumettre l'idée")


class CommentaireForm(FlaskForm):
    contenu = TextAreaField("Contenu", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Commenter")
