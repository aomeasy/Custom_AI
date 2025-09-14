from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services.google_sheets import GoogleSheetsService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    # Get sheets summary for dashboard
    sheets_service = GoogleSheetsService()
    summary = sheets_service.get_sheet_summary()
    
    return render_template('dashboard.html', 
                         user=current_user, 
                         sheets_summary=summary)

@main_bp.route('/guide')
@login_required
def guide():
    return render_template('guide.html')
