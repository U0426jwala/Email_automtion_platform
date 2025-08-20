# app/routes/sequence_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.campaign import get_campaigns
from app.models.contact import get_lists
# --- MODIFICATION START ---
# Simplified imports
from app.models.smtp_config import get_smtp_configs, get_smtp_config_by_id
from app.models.sequence import (
    create_sequence, get_sequences, get_sequence, create_sequence_step, 
    get_sequence_steps, get_sequence_step, update_sequence_step, 
    delete_sequence_step, delete_sequence
)
# --- MODIFICATION END ---
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sequence_bp = Blueprint('sequence', __name__, url_prefix='/sequences')

@sequence_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_sequence_route():
    if request.method == 'POST':
        sequence_name = request.form.get('sequence_name')
        list_id = request.form.get('list_id')
        # --- MODIFICATION START ---
        config_id = request.form.get('sending_config')

        if not all([sequence_name, list_id, config_id]):
            flash('Sequence Name, a Contact List, and an SMTP Configuration are required.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

        sequence_id = create_sequence(
            name=sequence_name, 
            list_id=int(list_id), 
            created_by=current_user.id,
            config_type='smtp', # Hardcoded to smtp
            config_id=int(config_id),
            status='active'
        )
        # --- MODIFICATION END ---

        if not sequence_id:
            flash('Failed to create sequence.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

        # (Step creation logic remains the same)
        step_keys = [key for key in request.form if key.startswith('step[')]
        max_step = 0
        if step_keys:
            try:
                max_step = max([int(key.split('[')[1].split(']')[0]) for key in step_keys])
            except (ValueError, IndexError): pass
        
        steps_created = 0
        for i in range(1, max_step + 1):
            campaign_id = request.form.get(f'step[{i}][campaign_id]')
            schedule_time_str = request.form.get(f'step[{i}][schedule_time]')
            if campaign_id and schedule_time_str:
                try:
                    schedule_time = datetime.fromisoformat(schedule_time_str)
                    is_re_reply = f'step[{i}][is_re_reply]' in request.form
                    create_sequence_step(sequence_id, i, 'mailer', int(campaign_id), schedule_time, is_re_reply)
                    steps_created += 1
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing form data for step {i}: {e}", exc_info=True)
                    flash(f'Invalid data for step {i}. It was skipped.', 'warning')
        
        flash(f"Sequence '{sequence_name}' created with {steps_created} step(s)!", 'success')
        return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))

    lists = get_lists()
    campaigns = get_campaigns()
    smtp_configs = get_smtp_configs(current_user.id)

    return render_template('create_sequence.html', 
                           lists=lists, 
                           campaigns=campaigns,
                           smtp_configs=smtp_configs)

@sequence_bp.route('/list')
@login_required
def list_sequences():
    sequences = get_sequences()
    return render_template('sequence.html', sequences=sequences)

@sequence_bp.route('/manage/<int:sequence_id>', methods=['GET'])
@login_required
def manage_sequence(sequence_id):
    sequence = get_sequence(sequence_id)
    if not sequence:
        flash('Sequence not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))
    steps = get_sequence_steps(sequence_id)
    
    # --- MODIFICATION START ---
    # Fetch specific SMTP config details for a better display
    sending_config_details = "Not Found"
    if sequence.get('config_type') == 'smtp':
        config = get_smtp_config_by_id(sequence['config_id'])
        if config:
            sending_config_details = f"SMTP: {config['name']}"
    # --- MODIFICATION END ---
    
    return render_template('manage_sequence.html', 
                           sequence=sequence, 
                           steps=steps, 
                           sending_config_details=sending_config_details)

# (The rest of the routes file - add, edit, delete steps - remains the same)
@sequence_bp.route('/add_step/<int:sequence_id>', methods=['GET', 'POST'])
@login_required
def add_sequence_step_route(sequence_id):
    sequence = get_sequence(sequence_id)
    if not sequence:
        flash('Sequence not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))
    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        schedule_time_str = request.form.get('schedule_time')
        if not all([campaign_id, schedule_time_str]):
            flash('Campaign and Schedule Time are required.', 'error')
            return redirect(url_for('sequence.add_sequence_step_route', sequence_id=sequence_id))
        schedule_time = datetime.fromisoformat(schedule_time_str)
        is_re_reply = 'is_re_reply' in request.form
        steps = get_sequence_steps(sequence_id)
        next_step_number = len(steps) + 1
        if create_sequence_step(sequence_id, next_step_number, 'mailer', int(campaign_id), schedule_time, is_re_reply):
            flash('New step added successfully!', 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
        else:
            flash('Failed to add the new step.', 'error')
    campaigns = get_campaigns()
    return render_template('add_sequence_step.html', sequence=sequence, campaigns=campaigns)

@sequence_bp.route('/edit_step/<int:step_id>', methods=['GET', 'POST'])
@login_required
def edit_sequence_step_route(step_id):
    step = get_sequence_step(step_id)
    if not step:
        flash('Step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))
    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        schedule_time_str = request.form.get('schedule_time')
        is_re_reply = 'is_re_reply' in request.form
        schedule_time = datetime.fromisoformat(schedule_time_str)
        if update_sequence_step(step_id, step['step_number'], 'mailer', int(campaign_id), schedule_time, is_re_reply):
            flash('Step updated successfully!', 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=step['sequence_id']))
        else:
            flash('Failed to update step.', 'error')
    campaigns = get_campaigns()
    return render_template('edit_sequence_step.html', step=step, campaigns=campaigns)

@sequence_bp.route('/delete_step/<int:step_id>', methods=['POST'])
@login_required
def delete_step_route(step_id):
    step = get_sequence_step(step_id)
    sequence_id = step['sequence_id']
    if delete_sequence_step(step_id):
        flash('Step deleted successfully.', 'success')
    else:
        flash('Failed to delete step.', 'error')
    return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))

@sequence_bp.route('/delete_sequence/<int:sequence_id>', methods=['POST'])
@login_required
def delete_sequence_route(sequence_id):
    if delete_sequence(sequence_id):
        flash('Sequence and all its steps have been deleted.', 'success')
    else:
        flash('Failed to delete sequence.', 'error')
    return redirect(url_for('sequence.list_sequences'))