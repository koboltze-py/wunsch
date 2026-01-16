from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import secrets
import hashlib
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# CORS-Konfiguration für React Frontend
CORS(app, 
     supports_credentials=True,
     origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'DELETE', 'OPTIONS'])

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
    email = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(64), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    force_password_change = db.Column(db.Boolean, default=False)
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
    confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship('User', backref='messages')
    read_by = db.relationship('MessageRead', backref='message', lazy=True, cascade='all, delete-orphan')

class MessageRead(db.Model):
    __tablename__ = 'message_reads'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.now)
    admin = db.relationship('User')

def hash_password(password):
    """Erstelle einen Hash des Passworts"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """Überprüfe ob Passwort korrekt ist"""
    return stored_hash == hash_password(password)

def generate_temp_password(length=12):
    """Generiere ein temporäres Passwort"""
    import string
    import random
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for _ in range(length))

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
        # Unterstütze sowohl JSON als auch Form-Data
        if request.is_json:
            data = request.json
        else:
            data = request.form
            
        name = data.get('name', '').strip()
        password = data.get('password', '')
        new_password = data.get('new_password', '')
        
        if not name:
            return jsonify({'success': False, 'error': 'Name ist erforderlich'}), 400
        
        if not password:
            return jsonify({'success': False, 'error': 'Passwort ist erforderlich'}), 400
        
        user = User.query.filter_by(name=name).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'Benutzer nicht gefunden'}), 401
        
        # Passwort prüfen
        if not verify_password(user.password, password):
            return jsonify({'success': False, 'error': 'Falsches Passwort'}), 401
        
        # Prüfe ob Passwort geändert werden muss
        if user.force_password_change:
            if not new_password:
                return jsonify({
                    'success': False, 
                    'force_password_change': True,
                    'error': 'Sie müssen Ihr Passwort ändern'
                }), 403
            
            # Neues Passwort setzen
            user.password = hash_password(new_password)
            user.force_password_change = False
            db.session.commit()
        
        # Benutzer in Session speichern
        session['user_name'] = name
        
        # Für normale Formulare: Redirect
        if not request.is_json:
            return redirect(url_for('index'))
        
        return jsonify({'success': True, 'is_admin': user.is_admin})
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    """Registrierung für neue Benutzer"""
    try:
        # Unterstütze sowohl JSON als auch Form-Data
        if request.is_json:
            data = request.json
        else:
            data = request.form
            
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not name:
            return jsonify({'success': False, 'error': 'Name ist erforderlich'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'success': False, 'error': 'Passwort muss mindestens 6 Zeichen lang sein'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwörter stimmen nicht überein'}), 400
        
        # Prüfe ob Benutzer bereits existiert
        if User.query.filter_by(name=name).first():
            return jsonify({'success': False, 'error': 'Dieser Name ist bereits vergeben'}), 400
        
        # Prüfe ob E-Mail bereits existiert (falls angegeben)
        if email and User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Diese E-Mail-Adresse ist bereits vergeben'}), 400
        
        # Erstelle neuen Benutzer
        new_user = User(
            name=name,
            email=email if email else None,
            password=hash_password(password),
            is_admin=False,
            force_password_change=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Für normale Formulare: Redirect zum Login
        if not request.is_json:
            return redirect(url_for('login'))
        
        return jsonify({'success': True, 'message': 'Registrierung erfolgreich! Sie können sich jetzt anmelden.'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

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
    
    # Lade alle Benutzer
    all_users = User.query.order_by(User.name).all()
    users_data = []
    for u in all_users:
        users_data.append({
            'id': u.id,
            'name': u.name,
            'is_admin': u.is_admin,
            'created_at': u.created_at.isoformat(),
            'shift_count': len(u.shift_requests)
        })
    
    # Lade alle Dienstwünsche mit Benutzernamen
    all_requests = []
    for req in ShiftRequest.query.order_by(ShiftRequest.date).all():
        all_requests.append({
            'id': str(req.id),
            'user_id': req.user_id,
            'user_name': req.user.name,
            'date': req.date.isoformat(),
            'shiftType': req.shift_type,
            'remarks': req.remarks,
            'status': req.status,
            'confirmed': req.confirmed,
            'createdAt': req.created_at.isoformat()
        })
    
    return render_template('admin_dashboard.html', 
                         requests=all_requests,
                         users=users_data,
                         user_name=user.name)

# Admin API Endpoints
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    """Hole alle Benutzer (nur Admin)"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    try:
        users = User.query.order_by(User.name).all()
        users_data = []
        for u in users:
            users_data.append({
                'id': u.id,
                'name': u.name,
                'is_admin': u.is_admin,
                'created_at': u.created_at.isoformat(),
                'shift_count': len(u.shift_requests)
            })
        
        return jsonify({'success': True, 'data': users_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
def toggle_admin(user_id):
    """Admin-Rolle umschalten (nur Admin)"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Benutzer nicht gefunden'}), 404
        
        # Verhindere, dass der letzte Admin sich selbst degradiert
        if user.is_admin:
            admin_count = User.query.filter_by(is_admin=True).count()
            if admin_count <= 1:
                return jsonify({'success': False, 'error': 'Es muss mindestens ein Admin geben'}), 400
        
        user.is_admin = not user.is_admin
        db.session.commit()
        
        return jsonify({'success': True, 'is_admin': user.is_admin})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    """Passwort zurücksetzen (nur Admin)"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Benutzer nicht gefunden'}), 404
        
        # Generiere temporäres Passwort
        temp_password = generate_temp_password()
        user.password = hash_password(temp_password)
        user.force_password_change = True
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'temp_password': temp_password,
            'message': f'Neues Passwort für {user.name}: {temp_password}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/shift-requests/<int:request_id>/confirm', methods=['POST'])
def confirm_shift_request(request_id):
    """Dienstwunsch bestätigen (nur Admin)"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    try:
        shift_request = ShiftRequest.query.get(request_id)
        if not shift_request:
            return jsonify({'success': False, 'error': 'Dienstwunsch nicht gefunden'}), 404
        
        shift_request.confirmed = not shift_request.confirmed
        db.session.commit()
        
        return jsonify({'success': True, 'confirmed': shift_request.confirmed})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/messages', methods=['GET', 'POST'])
def messages():
    """Nachrichten senden und abrufen"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    user = get_current_user()
    
    if request.method == 'POST':
        # Neue Nachricht senden
        data = request.json if request.is_json else request.form
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Nachricht darf nicht leer sein'}), 400
        
        try:
            message = Message(user_id=user.id, content=content)
            db.session.add(message)
            db.session.commit()
            
            return jsonify({'success': True, 'message_id': message.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:
        # Nachrichten abrufen (nur für Admins)
        if not is_admin():
            return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
        
        messages_data = []
        all_messages = Message.query.order_by(Message.created_at.desc()).all()
        
        for msg in all_messages:
            # Prüfe welche Admins diese Nachricht gelesen haben
            read_by_admins = []
            for read in msg.read_by:
                read_by_admins.append({
                    'admin_id': read.admin_id,
                    'admin_name': read.admin.name,
                    'read_at': read.read_at.isoformat()
                })
            
            # Prüfe ob aktueller Admin gelesen hat
            has_read = any(read.admin_id == user.id for read in msg.read_by)
            
            messages_data.append({
                'id': msg.id,
                'user_id': msg.user_id,
                'user_name': msg.user.name,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'has_read': has_read,
                'read_by': read_by_admins
            })
        
        return jsonify({'success': True, 'messages': messages_data})

@app.route('/api/messages/<int:message_id>/read', methods=['POST'])
def mark_message_read(message_id):
    """Nachricht als gelesen markieren"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    user = get_current_user()
    
    try:
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'success': False, 'error': 'Nachricht nicht gefunden'}), 404
        
        # Prüfe ob bereits gelesen
        existing = MessageRead.query.filter_by(message_id=message_id, admin_id=user.id).first()
        if existing:
            return jsonify({'success': True, 'already_read': True})
        
        # Als gelesen markieren
        read_entry = MessageRead(message_id=message_id, admin_id=user.id)
        db.session.add(read_entry)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/export')
def export_shift_requests():
    """Exportiere alle Dienstwünsche als JSON"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    try:
        # Gruppiere Dienstwünsche nach Nutzern
        users = User.query.order_by(User.name).all()
        export_data = []
        
        for user in users:
            user_requests = []
            for req in user.shift_requests:
                user_requests.append({
                    'date': req.date.strftime('%d.%m.%Y'),
                    'shift_type': req.shift_type,
                    'remarks': req.remarks,
                    'confirmed': req.confirmed
                })
            
            if user_requests:  # Nur Benutzer mit Dienstwünschen
                export_data.append({
                    'user_name': user.name,
                    'shift_requests': user_requests
                })
        
        return jsonify({'success': True, 'data': export_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/export/excel')
def export_excel():
    """Exportiere Dienstwünsche als Excel-Datei"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    try:
        # Erstelle Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Dienstwünsche"
        
        # Styles
        header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Header
        headers = ['Mitarbeiter', 'Datum', 'Wochentag', 'Schichtart', 'Bemerkungen', 'Status']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Daten
        row = 2
        all_requests = ShiftRequest.query.order_by(ShiftRequest.user_id, ShiftRequest.date).all()
        
        for req in all_requests:
            ws.cell(row=row, column=1, value=req.user.name).border = border
            ws.cell(row=row, column=2, value=req.date.strftime('%d.%m.%Y')).border = border
            ws.cell(row=row, column=3, value=req.date.strftime('%A')).border = border
            ws.cell(row=row, column=4, value=req.shift_type).border = border
            ws.cell(row=row, column=5, value=req.remarks or '').border = border
            status_cell = ws.cell(row=row, column=6, value='Bestätigt' if req.confirmed else 'Offen')
            status_cell.border = border
            if req.confirmed:
                status_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                status_cell.font = Font(color="006100")
            row += 1
        
        # Spaltenbreiten
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 30
        ws.column_dimensions['F'].width = 12
        
        # Speichern in BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'Dienstwünsche_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/export/pdf')
def export_pdf():
    """Exportiere Dienstwünsche als PDF-Datei"""
    auth_error = require_login()
    if auth_error:
        return auth_error
    
    if not is_admin():
        return jsonify({'success': False, 'error': 'Nicht autorisiert'}), 403
    
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm,
                              topMargin=1*cm, bottomMargin=1*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Titel
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#C00000'),
            spaceAfter=30,
            alignment=1  # Center
        )
        title = Paragraph(f"Dienstwünsche - Übersicht vom {datetime.now().strftime('%d.%m.%Y')}", title_style)
        elements.append(title)
        
        # Tabelle
        data = [['Mitarbeiter', 'Datum', 'Wochentag', 'Schicht', 'Bemerkungen', 'Status']]
        
        all_requests = ShiftRequest.query.order_by(ShiftRequest.user_id, ShiftRequest.date).all()
        
        for req in all_requests:
            data.append([
                req.user.name,
                req.date.strftime('%d.%m.%Y'),
                req.date.strftime('%A'),
                req.shift_type,
                req.remarks[:30] + '...' if req.remarks and len(req.remarks) > 30 else (req.remarks or ''),
                '✓ Bestätigt' if req.confirmed else 'Offen'
            ])
        
        table = Table(data, colWidths=[3.5*cm, 2.5*cm, 3*cm, 2*cm, 6*cm, 2.5*cm])
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
        ]))
        
        elements.append(table)
        
        # Fußzeile
        elements.append(Spacer(1, 20))
        footer = Paragraph("🏥 DRK Köln - Erste-Hilfe-Station Flughafen", styles['Normal'])
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Dienstwünsche_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
                'confirmed': req.confirmed,
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
                'confirmed': new_request.confirmed,
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
    print("\n✅ Dienstwunsch-Anwendung startet...")
    print("🌐 Öffne im Browser: http://localhost:5000")
    print("⛔ Zum Beenden: STRG + C\n")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
