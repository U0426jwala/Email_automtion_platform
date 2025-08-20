# app/routes/smtp_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
# --- MODIFICATION START: Added 'delete_smtp_config' to the import list ---
from app.models.smtp_config import save_smtp_config, get_smtp_configs, delete_smtp_config
# --- MODIFICATION END ---
import smtplib

smtp_bp = Blueprint('smtp', __name__, url_prefix='/smtp')

@smtp_bp.route('/configure', methods=['GET', 'POST'])
@login_required
def configure():
    if request.method == 'POST':
        name = request.form.get('name')
        host = request.form.get('host')
        port = request.form.get('port')
        username = request.form.get('username')
        password = request.form.get('password')
        use_tls = 'use_tls' in request.form
        from_email = request.form.get('from_email')
        from_name = request.form.get('from_name')

        if not all([name, host, port, username, password, from_email]):
            flash('All fields except "From Name" and "Use TLS" are required.', 'error')
            return redirect(url_for('smtp.configure'))

        if save_smtp_config(current_user.id, name, host, int(port), username, password, use_tls, from_email, from_name):
            flash(f"SMTP configuration '{name}' saved successfully!", 'success')
        else:
            flash('Failed to save SMTP configuration.', 'error')
        
        return redirect(url_for('smtp.configure'))

    configs = get_smtp_configs(current_user.id)
    return render_template('smtp_configure.html', configs=configs)

@smtp_bp.route('/test', methods=['POST'])
@login_required
def test_connection():
    data = request.json
    host = data.get('host')
    port = int(data.get('port', 587))
    username = data.get('username')
    password = data.get('password')
    use_tls = data.get('use_tls', True)

    try:
        server = smtplib.SMTP(host, port, timeout=10)
        if use_tls:
            server.starttls()
        server.login(username, password)
        server.quit()
        return jsonify({'success': True, 'message': 'Connection successful!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
@smtp_bp.route('/delete/<int:config_id>', methods=['POST'])
@login_required
def delete(config_id):
    """Deletes the specified SMTP configuration."""
    if delete_smtp_config(config_id, current_user.id):
        flash("SMTP configuration deleted successfully.", "success")
    else:
        flash("Error deleting configuration. You may not have permission or it may not exist.", "error")
    return redirect(url_for('smtp.configure'))