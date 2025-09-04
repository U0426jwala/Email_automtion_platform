# app/routes/sequence_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.sequence import (
    create_sequence, get_sequences_by_user, get_sequence, delete_sequence,
    create_sequence_step, get_sequence_steps, get_sequence_step,
    update_sequence_step, delete_sequence_step, get_previous_step_subject
)
from app.models.contact import get_lists
from app.models.campaign import get_campaigns
from app.models.smtp_config import get_smtp_configs
from datetime import datetime
import pytz
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
sequence_bp = Blueprint('sequence', __name__, url_prefix='/sequences')

LOCAL_TIMEZONE = pytz.timezone('Asia/Kolkata')

def convert_to_utc(naive_dt):
    if not naive_dt: return None
    local_dt = LOCAL_TIMEZONE.localize(naive_dt, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt

@sequence_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_sequence_route():
    if request.method == 'POST':
        try:
            name = request.form.get('sequence_name')
            list_id = request.form.get('list_id')
            config_id = request.form.get('sending_config')
            sequence_id = create_sequence(name, int(list_id), current_user.id, 'smtp', int(config_id))
            if sequence_id:
                steps_data = {}
                step_pattern = re.compile(r'step\[(\d+)\]\[(\w+)\]')
                for key, value in request.form.items():
                    match = step_pattern.match(key)
                    if match:
                        step_number, field_name = match.groups()
                        if step_number not in steps_data: steps_data[step_number] = {}
                        steps_data[step_number][field_name] = value
                
                for step_num_str in sorted(steps_data.keys(), key=int):
                    step_data = steps_data[step_num_str]
                    naive_schedule_time = datetime.fromisoformat(step_data['schedule_time'])
                    utc_schedule_time = convert_to_utc(naive_schedule_time)
                    create_sequence_step(
                        sequence_id=sequence_id, 
                        step_number=int(step_num_str), 
                        step_type='mailer',
                        schedule_time=utc_schedule_time,
                        is_re_reply='is_re_reply' in step_data, # Correctly checks for the toggle
                        campaign_id=step_data.get('campaign_id'), 
                        reply_body=step_data.get('reply_body')
                    )
                flash('Sequence created successfully!', 'success')
                return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
        except Exception as e:
            logger.error(f"Error during sequence creation: {e}")
            flash('An error occurred during creation.', 'error')
    
    lists = get_lists()
    smtp_configs = get_smtp_configs(current_user.id)
    campaigns = get_campaigns()
    return render_template('create_sequence.html', lists=lists, smtp_configs=smtp_configs, campaigns=campaigns)

@sequence_bp.route('/add_step/<int:sequence_id>', methods=['GET', 'POST'])
@login_required
def add_sequence_step_route(sequence_id):
    sequence = get_sequence(sequence_id)
    steps = get_sequence_steps(sequence_id)
    next_step_number = len(steps) + 1
    if request.method == 'POST':
        naive_schedule_time = datetime.fromisoformat(request.form.get('schedule_time'))
        utc_schedule_time = convert_to_utc(naive_schedule_time)
        create_sequence_step(
            sequence_id, 
            next_step_number, 
            'mailer',
            schedule_time=utc_schedule_time,
            is_re_reply='is_re_reply' in request.form, # Correctly checks for the toggle
            reply_body=request.form.get('reply_body')
        )
        flash('New step added!', 'success')
        return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
    
    previous_subject = get_previous_step_subject(sequence_id, next_step_number)
    return render_template('add_sequence_step.html', sequence=sequence, step_number=next_step_number, previous_subject=previous_subject)

@sequence_bp.route('/edit_step/<int:step_id>', methods=['GET', 'POST'])
@login_required
def edit_sequence_step_route(step_id):
    step = get_sequence_step(step_id)
    if not step:
        flash('Step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    if request.method == 'POST':
        naive_schedule_time = datetime.fromisoformat(request.form.get('schedule_time'))
        utc_schedule_time = convert_to_utc(naive_schedule_time)
        update_sequence_step(
            step_id, 
            step['step_number'], 
            utc_schedule_time,
            'is_re_reply' in request.form, # Correctly checks for the toggle
            request.form.get('campaign_id'), 
            request.form.get('reply_body')
        )
        flash('Step updated successfully!', 'success')
        return redirect(url_for('sequence.manage_sequence', sequence_id=step['sequence_id']))

    previous_subject = get_previous_step_subject(step['sequence_id'], step['step_number'])
    campaigns = get_campaigns()
    # Ensure schedule_time is a datetime object before passing to template
    if step and isinstance(step.get('schedule_time'), str):
        step['schedule_time'] = datetime.fromisoformat(step['schedule_time'])
        
    return render_template('edit_sequence_step.html', step=step, campaigns=campaigns, previous_subject=previous_subject)

# --- Other routes (list, manage, delete) remain the same ---
@sequence_bp.route('/')
@login_required
def list_sequences():
    sequences = get_sequences_by_user(current_user.id)
    return render_template('sequence.html', sequences=sequences)

@sequence_bp.route('/manage/<int:sequence_id>')
@login_required
def manage_sequence(sequence_id):
    sequence = get_sequence(sequence_id)
    steps = get_sequence_steps(sequence_id)
    return render_template('manage_sequence.html', sequence=sequence, steps=steps)

@sequence_bp.route('/delete/<int:sequence_id>', methods=['POST'])
@login_required
def delete_sequence_route(sequence_id):
    if delete_sequence(sequence_id): flash('Sequence deleted.', 'success')
    else: flash('Error deleting sequence.', 'error')
    return redirect(url_for('sequence.list_sequences'))

@sequence_bp.route('/delete_step/<int:step_id>', methods=['POST'])
@login_required
def delete_sequence_step_route(step_id):
    step = get_sequence_step(step_id)
    if not step:
        flash('Step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))
    sequence_id = step['sequence_id']
    if delete_sequence_step(step_id): flash('Step deleted successfully.', 'success')
    else: flash('Error deleting step.', 'error')
    return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))