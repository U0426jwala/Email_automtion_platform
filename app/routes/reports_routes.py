# app/routes/reports_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models import reports
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

# --- (The reports_dashboard and reports_data routes remain unchanged) ---
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
    bounced_emails = reports.get_bounced_emails_report()
    months = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    years = list(range(current_year - 5, current_year + 2))
    return render_template('reports_dashboard.html',
                           stats=stats,
                           months=months,
                           years=years,
                           selected_month=selected_month,
                           selected_year=selected_year,
                           bounced_emails=bounced_emails)


@reports_bp.route('/reports/data')
@login_required
def reports_data():
    stats = {
        'total_sent': reports.get_total_sent_count(),
        'total_scheduled': reports.get_total_scheduled_count(),
        'total_contacts': reports.get_total_contacts_count(),
        'total_lists': reports.get_total_lists_count(),
        'sent_last_24h': reports.get_sent_last_24_hours_count()
    }
    return jsonify(stats)


@reports_bp.route('/reports/future-scheduled')
@login_required
def future_scheduled_emails():
    return render_template('future_scheduled_emails.html')


# --- MODIFICATION START: Removed the get_active_lists route ---
# The route @reports_bp.route('/reports/active-lists') has been removed as it's no longer needed.
# --- MODIFICATION END ---


@reports_bp.route('/reports/future-scheduled/events')
@login_required
def future_scheduled_emails_events():
    # --- MODIFICATION START: Simplified to fetch all events without filtering ---
    # The list_name_filter logic has been removed.

    # Fetch the aggregated summary for all upcoming emails.
    scheduled_summary_utc = reports.get_future_scheduled_emails_summary()
    # --- MODIFICATION END ---

    ist_offset = timedelta(hours=5, minutes=30)
    events = []
    for item in scheduled_summary_utc:
        if item.get('schedule_time'):
            ist_time = item['schedule_time'] + ist_offset

            list_names = item.get('list_names', 'Unknown List')
            total_recipients = item.get('total_recipients', 0)

            # --- MODIFICATION START: Changed event title to show the aggregated count ---
            # The title now clearly states the total number of emails for that time slot.
            event_title = f"{int(total_recipients)} Emails"
            # --- MODIFICATION END ---

            events.append({
                'title': event_title,
                'start': ist_time.isoformat(),
                'extendedProps': {
                    'sequenceNames': item.get('sequence_names'),
                    'listNames': list_names,
                    'recipientCount': int(total_recipients)
                }
            })

    return jsonify(events)