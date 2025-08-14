from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import reports
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def reports_dashboard():
    # Get the current year and month as defaults
    current_year = datetime.utcnow().year
    current_month = datetime.utcnow().month

    # Get selected month/year from user, or use current month/year as default
    selected_year = request.args.get('year', default=current_year, type=int)
    selected_month = request.args.get('month', default=current_month, type=int)

    # Fetch all the statistics
    stats = {
        'total_sent': reports.get_total_sent_count(),
        'total_scheduled': reports.get_total_scheduled_count(),
        'total_contacts': reports.get_total_contacts_count(),
        'total_lists': reports.get_total_lists_count(),
        'sent_last_24h': reports.get_sent_last_24_hours_count(),
        # Fetch the new monthly stats based on user selection
        'sent_monthly': reports.get_sent_monthly_count(selected_year, selected_month),
        'scheduled_monthly': reports.get_scheduled_monthly_count(selected_year, selected_month)
    }
    
    # Data for the dropdowns
    months = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    years = list(range(current_year - 5, current_year + 2)) # Range of years for the dropdown

    return render_template('reports_dashboard.html', 
                           stats=stats, 
                           today=datetime.utcnow(),
                           months=months,
                           years=years,
                           selected_month=selected_month,
                           selected_year=selected_year)

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