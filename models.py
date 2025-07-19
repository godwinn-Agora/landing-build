from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Idee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur = db.relationship("Utilisateur", backref="idees")
    likes = db.relationship("Like", backref="idee")
    commentaires = db.relationship("Commentaire", backref="idee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Idée {self.id} - {self.titre}>"


class Utilisateur(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship("Like", backref="utilisateur")
    commentaires = db.relationship("Commentaire", backref="utilisateur", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Utilisateur {self.id} - {self.email}>"


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    idee_id = db.Column(db.Integer, db.ForeignKey('idee.id'), nullable=False)
    date_like = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('utilisateur_id', 'idee_id', name='unique_like'),)

    def __repr__(self):
        return f"<Like {self.id} - {self.utilisateur_id} - {self.idee_id}>"


class Commentaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    date_commentaire = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'),  nullable=False)
    idee_id = db.Column(db.Integer, db.ForeignKey('idee.id'),  nullable=False)

    def __repr__(self):
        return f"<Commentaire {self.id} - {self.utilisateur_id} - {self.idee_id}>"

