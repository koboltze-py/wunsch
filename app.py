from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import secrets
import hashlib

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Datenbank-Konfiguration
# Verwende PostgreSQL auf Render, SQLite lokal
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dienstwuensche.db')
# Fix für Render (postgres:// -> postgresql://)
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Datenbank-Modelle
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    shift_requests = db.relationship('ShiftRequest', backref='user', lazy=True, cascade='all, delete-orphan')

class ShiftRequest(db.Model):
    __tablename__ = 'shift_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)
    remarks = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.now)

def hash_password(password):
    """Erstelle einen Hash des Passworts"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """Überprüfe ob Passwort korrekt ist"""
    return stored_hash == hash_password(password)

def get_current_user():
    """Hole den aktuell angemeldeten Benutzer"""
    user_name = session.get('user_name')
    if not user_name:
        return None
    return User.query.filter_by(name=user_name).first()

def is_admin():
    """Prüfe ob aktueller Benutzer Admin ist"""
    user = get_current_user()
    return user and user.is_admin

def require_login():
    """Prüfe ob Benutzer angemeldet ist"""
    if not get_current_user():
        return jsonify({'success': False, 'error': 'Nicht angemeldet'}), 401
    return None

def init_db():
    """Initialisiere Datenbank"""
    with app.app_context():
        db.create_all()
        # Erstelle Initial-Admin falls keine Benutzer existieren
        if User.query.count() == 0:
            admin = User(
                name='Groß',
                password=hash_password('mettwurst'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Initial-Admin 'Groß' erstellt")

@app.route('/')
def index():
    """Hauptseite mit Formular"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    # Admins zur Admin-Seite umleiten
    if user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return render_template('shift_request_form.html', user_name=user.name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    if request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        password = data.get('password', '')
        
        if not name:
            return jsonify({'success': False, 'error': 'Name ist erforderlich'}), 400
        
        if not password:
            return jsonify({'success': False, 'error': 'Passwort ist erforderlich'}), 400
        
        user = User.query.filter_by(name=name).first()
        
        if user:
            # Bestehender Benutzer - Passwort prüfen
            if not verify_password(user.password, password):
                return jsonify({'success': False, 'error': 'Falsches Passwort'}), 401
        else:
            # Neuer Benutzer - Account erstellen
            user = User(
                name=name,
                password=hash_password(password),
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
        
        # Benutzer in Session speichern
        session['user_name'] = name
        
        return jsonify({'success': True, 'is_admin': user.is_admin})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('user_name', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    """Admin-Dashboard mit allen Dienstwünschen"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if not user.is_admin:
        return redirect(url_for('index'))
    
    # Lade alle Dienstwünsche mit Benutzernamen
    all_requests = []
    for req in ShiftRequest.query.order_by(ShiftRequest.date).all():
        all_requests.append({
            'id': str(req.id),
            'user_name': req.user.name,
            'date': req.date.isoformat(),
            'shiftType': req.shift_type,
            'remarks': req.remarks,
            'status': req.status,
            'createdAt': req.created_at.isoformat()
        })
    
    return render_template('admin_dashboard.html', 
                         requests=all_requests, 
                         user_name=user.name)

@app.route('/api/shift-requests', methods=['GET'])
def get_shift_requests():
    """Hole alle Dienstwünsche des Benutzers für den aktuellen Monat"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    try:
        user = get_current_user()
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Filtere nach Benutzer und aktuellem Monat
        requests = ShiftRequest.query.filter_by(user_id=user.id).filter(
            db.extract('month', ShiftRequest.date) == current_month,
            db.extract('year', ShiftRequest.date) == current_year
        ).order_by(ShiftRequest.date).all()
        
        filtered = []
        for req in requests:
            filtered.append({
                'id': str(req.id),
                'user_name': user.name,
                'date': req.date.isoformat(),
                'shiftType': req.shift_type,
                'remarks': req.remarks,
                'status': req.status,
                'createdAt': req.created_at.isoformat()
            })
        
        return jsonify({'success': True, 'data': filtered})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shift-requests', methods=['POST'])
def create_shift_request():
    """Erstelle einen neuen Dienstwunsch"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    try:
        user = get_current_user()
        data = request.json
        
        # Validierung
        if not data.get('date'):
            return jsonify({'success': False, 'error': 'Datum ist erforderlich'}), 400
        
        if not data.get('shiftType'):
            return jsonify({'success': False, 'error': 'Schichtart ist erforderlich'}), 400
        
        # Prüfe ob Datum in der Vergangenheit liegt
        request_date = datetime.fromisoformat(data['date'])
        if request_date.date() < datetime.now().date():
            return jsonify({
                'success': False, 
                'error': 'Das Datum darf nicht in der Vergangenheit liegen'
            }), 400
        
        # Prüfe ob bereits ein Wunsch für diesen Tag und Benutzer existiert
        existing = ShiftRequest.query.filter_by(
            user_id=user.id,
            date=request_date.date()
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Sie haben bereits einen Wunsch für dieses Datum eingereicht'
            }), 400
        
        # Erstelle neuen Wunsch
        new_request = ShiftRequest(
            user_id=user.id,
            date=request_date.date(),
            shift_type=data['shiftType'],
            remarks=data.get('remarks', ''),
            status='PENDING'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'data': {
                'id': str(new_request.id),
                'user_name': user.name,
                'date': new_request.date.isoformat(),
                'shiftType': new_request.shift_type,
                'remarks': new_request.remarks,
                'status': new_request.status,
                'createdAt': new_request.created_at.isoformat()
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shift-requests/<request_id>', methods=['DELETE'])
def delete_shift_request(request_id):
    """Lösche einen Dienstwunsch"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    try:
        user = get_current_user()
        
        # Finde den Wunsch
        shift_request = ShiftRequest.query.get(int(request_id))
        
        if not shift_request:
            return jsonify({'success': False, 'error': 'Wunsch nicht gefunden'}), 404
        
        # Prüfe ob der Wunsch dem aktuellen Benutzer gehört
        if shift_request.user_id != user.id:
            return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
        
        # Lösche den Wunsch
        db.session.delete(shift_request)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("\n Dienstwunsch-Anwendung startet...")
    print(" Öffne im Browser: http://localhost:5000")
    print("  Zum Beenden: STRG + C\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
