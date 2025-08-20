# app/routes/reports_routes.py
# --- MODIFICATION START: Added jsonify to the import list ---
from flask import Blueprint, render_template, request, jsonify
# --- MODIFICATION END ---
from flask_login import login_required
from app.models import reports
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def reports_dashboard():
    current_year = datetime.utcnow().year
    current_month = datetime.utcnow().month
    selected_year = request.args.get('year', default=current_year, type=int)
    selected_month = request.args.get('month', default=current_month, type=int)

    stats = {
        'total_sent': reports.get_total_sent_count(),
        'total_scheduled': reports.get_total_scheduled_count(),
        'total_contacts': reports.get_total_contacts_count(),
        'total_lists': reports.get_total_lists_count(),
        'sent_last_24h': reports.get_sent_last_24_hours_count(),
        'sent_monthly': reports.get_sent_monthly_count(selected_year, selected_month),
        'scheduled_monthly': reports.get_scheduled_monthly_count(selected_year, selected_month)
    }
    
    # Fetch the bounced emails list
    bounced_emails = reports.get_bounced_emails_report()
    
    months = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    years = list(range(current_year - 5, current_year + 2))

    return render_template('reports_dashboard.html', 
                           stats=stats, 
                           months=months,
                           years=years,
                           selected_month=selected_month,
                           selected_year=selected_year,
                           bounced_emails=bounced_emails) # Pass the list to the template

@reports_bp.route('/reports/data')
@login_required
def reports_data():
    """This route provides the raw dashboard data as JSON for live updates."""
    stats = {
        'total_sent': reports.get_total_sent_count(),
        'total_scheduled': reports.get_total_scheduled_count(),
        'total_contacts': reports.get_total_contacts_count(),
        'total_lists': reports.get_total_lists_count(),
        'sent_last_24h': reports.get_sent_last_24_hours_count()
    }
    return jsonify(stats)