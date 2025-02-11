from flask import Flask, abort,jsonify, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode as qrcode_module
from datetime import datetime
import os
from hashlib import sha256
import uuid
import os
import hashlib
import qrcode
import re

app = Flask(__name__)
# Configure database
app.config['SECRET_KEY'] = 'votre-clé-secrète-ici'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://administrateur:AVNS_6ypK_dlVSrNNVhjEMWt@mysql-2ef51fa8-hammouda-9afc.h.aivencloud.com:19722/team-building-events'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configure upload folder and ensure it exists
UPLOAD_FOLDER = 'static/uploads'
QR_CODE_FOLDER = 'static/qrcode'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['QR_CODE_FOLDER'] = QR_CODE_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['QR_CODE_FOLDER']):
    os.makedirs(app.config['QR_CODE_FOLDER'])


db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_bon = db.Column(db.String(50), unique=True, nullable=False)
    nom_carnet = db.Column(db.String(100), nullable=False)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    entreprise = db.Column(db.String(100), nullable=False)
    fonction = db.Column(db.String(100), nullable=False)
    image_bon = db.Column(db.String(200), nullable=False)
    data_hash = db.Column(db.String(256), unique=True, nullable=False)
    date_confirmation = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return f'<Participant {self.nom}>'
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Identifiants invalides', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    participants = Participant.query.order_by(Participant.date_confirmation.desc()).all()
    return render_template('admin/dashboard.html', participants=participants)

# ROUTE POUR MODIFIER UN PARTICIPANT (AJAX)
@app.route('/edit_participant/<int:id>', methods=['POST'])
def edit_participant(id):
    participant = Participant.query.get_or_404(id)
    data = request.get_json()

    participant.nom = data["nom"]
    participant.prenom = data["prenom"]
    participant.telephone = data["telephone"]
    participant.numero_bon = data["numeroBon"]
    participant.nom_carnet = data["nomCarnet"]

    try:
        db.session.commit()
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

# ROUTE POUR SUPPRIMER UN PARTICIPANT (AJAX)
@app.route('/delete_participant/<int:id>', methods=['POST'])
def delete_participant(id):
    participant = Participant.query.get_or_404(id)

    try:
        db.session.delete(participant)
        db.session.commit()
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

def generate_hash(nom, prenom, telephone, numero_bon, nom_carnet):
    data = f"{nom}{prenom}{telephone}{numero_bon}{nom_carnet}"
    return hashlib.sha256(data.encode()).hexdigest()

# Fonction pour générer un QR code et l'enregistrer
def generate_qr_code(participant_id, data_hash):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data_hash)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")

    # Assurez-vous que le dossier `static/qrcode/` existe
    qr_directory = "static/qrcode"
    if not os.path.exists(qr_directory):
        os.makedirs(qr_directory)

    qr_path = f"{qr_directory}/{participant_id}.png"
    img.save(qr_path)
    return qr_path

# Route pour ajouter un participant
@app.route('/add_participant', methods=['POST'])
def add_participant():
    try:
        data = request.get_json()

        # Générer le hash
        data_hash = generate_hash(
            data["nom"], data["prenom"], data["telephone"], data["numeroBon"], data["nomCarnet"]
        )

        # Création du participant
        new_participant = Participant(
            nom=data["nom"],
            prenom=data["prenom"],
            telephone=data["telephone"],
            numero_bon=data["numeroBon"],
            nom_carnet=data["nomCarnet"],
            email=f"{data['nom']}.{data['prenom']}@example.com",
            entreprise="Inconnue",
            fonction="Inconnue",
            image_bon="default.jpg",
            data_hash=data_hash
        )

        db.session.add(new_participant)
        db.session.commit()  # Permet d'obtenir l'ID généré

        # Générer le QR code
        qr_code_path = generate_qr_code(new_participant.id, data_hash)

        # Mise à jour du chemin du QR code en base de données
        new_participant.qr_code_url = qr_code_path
        db.session.commit()

        return jsonify({"success": True, "qr_code": qr_code_path})
    
    except Exception as e:
        print("Erreur lors de l'ajout du participant :", e)  # Affichage de l'erreur pour le debug
        return jsonify({"success": False, "error": str(e)})


@app.route('/verifier', methods=['GET', 'POST'])
@login_required
def verifier():
    if not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        hash_participant = request.form['hash']  # Le hash du participant scanné depuis le QR code

        # Recherche du participant dans la base de données
        participant = Participant.query.filter_by(hash=hash_participant).first()

        if participant:
            return render_template('verifier.html', participant=participant)
        else:
            return render_template('verifier.html', error="Participant introuvable.")
    
    return render_template('verifier.html')

@app.route('/search-participant')
def search_participant():
    data_hash = request.args.get('hash')
    if not data_hash:
        return jsonify({"found": False, "error": "Aucun hash fourni"}), 400
    
    # Recherche du participant dans la base de données par le hash
    participant = Participant.query.filter_by(data_hash=data_hash).first()
    
    if participant:
        return jsonify({
            "found": True,
            "id": participant.id,
            "nom": participant.nom,
            "prenom": participant.prenom,
            "evenement":participant.nom_carnet,
        })
    else:
        return jsonify({"found": False, "error": "Participant non trouvé"}), 404




# Fonction pour valider l'email et éliminer les caractères spéciaux
def validate_email(email):
    # Filtrage des caractères spéciaux
    email = re.sub(r'[^\w\.-@]', '', email)  # Garde seulement les lettres, chiffres, '.', '-', et '@'
    
    # Expression régulière pour valider l'email
    regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}$'
    return re.match(regex, email)

def validate_phone(phone):
    # Suppression des espaces et autres caractères non numériques sauf le '+'
    phone = re.sub(r'\s+', '', phone)  # Supprime les espaces
    phone = re.sub(r'[^\d+]', '', phone)  # Garde uniquement les chiffres et '+'
    
    # Expression régulière pour valider le téléphone (8 à 15 chiffres)
    regex = r'^\+?\d{8,15}$'
    
    # Validation
    if not re.match(regex, phone):
        return {"error": "Numéro de téléphone invalide", "success": False}
    return {"success": True}

@app.route('/inscription', methods=['POST','GET'])
def inscription():
    if request.method == 'POST':
        try:
            numero_bon = request.form['numero_bon']
            nom_carnet = request.form['nom_carnet']
            nom = request.form['nom']
            prenom = request.form['prenom']
            email = request.form['email']
            telephone = request.form['telephone']

            # Hachage des données sensibles
            data_hash = generate_hash(
            nom, prenom,telephone, numero_bon, nom_carnet
            )

            

            # Création du participant
            new_participant = Participant(
                nom=nom,
                prenom=prenom,
                telephone=telephone,
                numero_bon=numero_bon,
                nom_carnet=nom_carnet,
                email=f"{nom}.{prenom}@example.com",
                entreprise="Inconnue",
                fonction="Inconnue",
                image_bon="default.jpg",
                data_hash=data_hash
            )

            db.session.add(new_participant)
            db.session.commit()  # Permet d'obtenir l'ID généré
            participant=Participant.query.filter_by(nom=nom,prenom=prenom,numero_bon=numero_bon,nom_carnet=nom_carnet,telephone=telephone).first()
            # Générer le QR code
            qr_code_path = generate_qr_code(participant.id, data_hash)
            new_participant.qr_code_url = qr_code_path
            db.session.commit()
            return jsonify({"success": True, "qr_code_path": qr_code_path})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    else:
        return render_template('inscription.html')


@app.route('/inscription_confirmation', methods=['GET'])
def inscription_confirmation():
    return render_template('inscription_confirmee.html')

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin_password'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
