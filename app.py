from flask import Flask, render_template, request, redirect, flash, jsonify, abort, url_for
from datetime import datetime
from models import db, Idee, Utilisateur, Like, Commentaire
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, logout_user, current_user, login_user, LoginManager
from sqlalchemy import func
from flask_wtf import CSRFProtect
from forms import ConnexionForm, InscriptionForm, IdeeForm, CommentaireForm
import bleach

app = Flask(__name__)
app.secret_key = "une_chaine_secrete_a_changer"  # En production, changer par une clé aléatoire forte
csrf = CSRFProtect(app)

# Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///idees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = False  # True seulement en HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = "connexion"
login_manager.init_app(app)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    print("Connecté ? ->", current_user.is_authenticated)
    print("Utilisateur ->", current_user.email if current_user.is_authenticated else "None")
    form = IdeeForm()
    if form.validate_on_submit():
        titre = form.titre.data
        contenu = form.contenu.data

        nouvelle_idee = Idee(
            titre=titre,
            contenu=contenu,
            utilisateur_id=current_user.id,
            date_creation=datetime.utcnow()
        )
        db.session.add(nouvelle_idee)
        db.session.commit()
        flash("Idée publiée avec succès !", "success")
        return redirect("/")

    idees = Idee.query.order_by(Idee.date_creation.desc()).all()
    return render_template("index.html", idees=idees, form=form)


@app.route("/supprimer/<int:id>", methods=["POST"])
@login_required
def supprimer(id):
    idee = Idee.query.get(id)
    if idee and idee.utilisateur_id == current_user.id:
        db.session.delete(idee)
        db.session.commit()
        flash("Idée supprimée avec succès.", "success")
    else:
        return render_template("403.html"), 403
    return redirect("/")


@app.route("/modifier/<id>/form", methods=["GET"])
@login_required
def afficher_modifier(id):
    idee = Idee.query.get(id)
    if idee and idee.utilisateur_id == current_user.id:
        return render_template("modifier.html", idee=idee)
    else:
        return render_template("403.html"), 403


@app.route("/modifier/<int:id>", methods=["POST"])
@login_required
def modifier(id):
    idee = Idee.query.get(id)
    if idee and idee.utilisateur_id == current_user.id:
        titre = request.form["titre"]
        contenu = request.form["contenu"]

        if len(titre) < 3:
            flash("Le titre doit contenir au moins 3 caractères.", "error")
            return redirect(f"/modifier/{id}/form")

        if len(titre) > 100:
            flash("Le titre est trop long.", "error")
            return redirect(f"/modifier/{id}/form")

        if len(contenu) > 1000:
            flash("Le contenu est trop long.", "error")
            return redirect(f"/modifier/{id}/form")

        idee.titre = titre
        idee.contenu = contenu
        db.session.commit()
        flash("Idée modifiée avec succès.", "success")
        return redirect("/")
    else:
        return render_template("403.html"), 403


@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if current_user.is_authenticated:
        return redirect(url_for('toutes_les_idees'))

    form = InscriptionForm()

    if form.validate_on_submit():
        email = form.email.data.lower()
        mot_de_passe = form.mot_de_passe.data

        utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
        if utilisateur_existant:
            flash("Cet e-mail est déjà utilisé.", "error")
            return render_template("inscription.html", form=form)

        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        nouvel_utilisateur = Utilisateur(email=email, mot_de_passe=mot_de_passe_hash, date_creation=datetime.utcnow())

        db.session.add(nouvel_utilisateur)
        db.session.commit()
        flash("Inscription réussie, bienvenue !", "success")
        login_user(nouvel_utilisateur)

        return redirect("/")
    # Si la validation échoue, afficher les erreurs de champ en flash
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} : {error}", "error")

    return render_template("inscription.html", form=form)


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    print("REQUETE CONNEXION ->", request.method)
    print("UTILISATEUR AUTHENTIFIÉ ->", current_user.is_authenticated)

    if current_user.is_authenticated:
        print("Redirection directe vers / car déjà connecté")
        return redirect(url_for('index'))

    form = ConnexionForm()

    if form.validate_on_submit():
        email = form.email.data.lower()
        mot_de_passe = form.mot_de_passe.data

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and check_password_hash(utilisateur.mot_de_passe, mot_de_passe):
            print("Connexion réussie pour :", email)
            login_user(utilisateur)
            print("Redirection vers / après login_user")
            return redirect(url_for("index"))
        else:
            print("Échec de connexion")
            flash("Identifiants incorrects", "error")
            return redirect("/connexion")

    return render_template("connexion.html", form=form)


@app.route("/deconnexion")
@login_required
def deconnexion():
    logout_user()
    flash("Déconnecté avec succès.", "info")
    return redirect("/")


@app.route("/like/<int:idee_id>", methods=["POST"])
@login_required
def like(idee_id):
    idee = Idee.query.get(idee_id)
    if not idee:
        abort(404)

    like = Like.query.filter_by(utilisateur_id=current_user.id, idee_id=idee.id).first()

    if like:
        db.session.delete(like)
        db.session.commit()
    else:
        nouveau_like = Like(utilisateur_id=current_user.id, idee_id=idee.id)
        db.session.add(nouveau_like)
        db.session.commit()

    return redirect("/")


@app.route("/commentaire/<int:idee_id>", methods=["POST"])
@login_required
def commentaire(idee_id):
    form = CommentaireForm()

    if form.validate_on_submit():
        contenu = form.contenu.data

        nouveau_commentaire = Commentaire(contenu=contenu, utilisateur_id=current_user.id, idee_id=idee_id)

        db.session.add(nouveau_commentaire)
        db.session.commit()
        flash("Commentaire ajouté avec succès.", "success")
        return redirect("/")

    flash("Commentaire invalide.", "error")
    return redirect("/")


@app.route("/mes-idees")
@login_required
def mes_idees():
    idees = Idee.query.filter_by(utilisateur_id=current_user.id).order_by(Idee.date_creation.desc()).all()
    return render_template("mes_idees.html", idees=idees)


@app.route("/toutes-les-idees")
def toutes_les_idees():
    form = IdeeForm()
    idees = Idee.query.order_by(Idee.date_creation.desc()).all()
    return render_template("toutes_idees.html", form=form, idees=idees)


@app.route("/idees-populaires")
def idees_populaires():
    idees = Idee.query.all()
    idees_tries = sorted(idees, key=lambda i: len(i.likes), reverse=True)
    return render_template("idees_populaires.html", idees=idees_tries)


@app.route("/api/like/<int:idee_id>", methods=["POST"])
@login_required
def like_api(idee_id):
    idee = Idee.query.get_or_404(idee_id)
    like = Like.query.filter_by(utilisateur_id=current_user.id, idee_id=idee_id).first()

    if like:
        db.session.delete(like)
        action = "unliked"
    else:
        nouveau_like = Like(utilisateur_id=current_user.id, idee_id=idee_id)
        db.session.add(nouveau_like)
        action = "liked"

    db.session.commit()

    return jsonify({
        "status": "success",
        "action": action,
        "like_count": len(idee.likes)
    })


@app.route('/api/commentaire/<int:idee_id>', methods=["POST"])
@login_required
def commenter_idee_api(idee_id):

    contenu = bleach.clean(request.form.get("contenu", "").strip(), tags=['b', 'i', 'strong', 'em'], strip=True)

    if not contenu:
        return jsonify({"status": "error", "message": "Commentaire vide."}), 400

    idee = Idee.query.get(idee_id)
    if not idee:
        return jsonify({"status": "error", "message": "Idée introuvable."}), 404

    commentaire = Commentaire(contenu=contenu, utilisateur=current_user, idee=idee, date_commentaire=datetime.utcnow())
    db.session.add(commentaire)
    db.session.commit()

    return jsonify({
        "status": "success",
        "utilisateur": current_user.email,
        "contenu": contenu,
        "date": commentaire.date_commentaire.strftime('%d/%m/%Y %H:%M')
    })


@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))


@app.errorhandler(404)
def page_introuvable(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
