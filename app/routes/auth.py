from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app.services.google_sheets import GoogleSheetsService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check in Google Sheets first
        sheets_service = GoogleSheetsService()
        if sheets_service.get_user_credentials(username, password):
            # Find or create user in local database
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(username=username)
                user.set_password(password)
                from app import db
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
