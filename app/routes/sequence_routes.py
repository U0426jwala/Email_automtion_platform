from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.contact import get_lists
from app.models.campaign import get_campaigns
from app.models.sequence import (
    create_sequence, get_sequences, get_sequence,
    create_sequence_step, get_sequence_steps, get_sequence_step,
    update_sequence_step, delete_sequence_step, delete_sequence
)
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sequence_bp = Blueprint('sequence', __name__, url_prefix='/sequences')

@sequence_bp.route('/create_sequence', methods=['GET', 'POST'])
@login_required
def create_sequence_route():
    if request.method == 'POST':
        sequence_name = request.form.get('sequence_name')
        list_id = request.form.get('list_id')
        selected_campaign_id = request.form.get('campaign_id')
        schedule_time_str = request.form.get('schedule_time')
        is_re_reply = request.form.get('is_re_reply') == 'on'

        if not all([sequence_name, list_id, selected_campaign_id, schedule_time_str]):
            flash('All fields (Sequence Name, List, Initial Campaign, Schedule Time) are required.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

        try:
            schedule_time = datetime.fromisoformat(schedule_time_str)
        except ValueError:
            flash('Invalid schedule time format. Please use the provided date/time picker.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

        sequence_id = create_sequence(sequence_name, list_id, current_user.username, status='active')
        
        if sequence_id:
            create_sequence_step(sequence_id, 1, selected_campaign_id, 0, is_re_reply)
            
            flash(f"Sequence '{sequence_name}' created! You can now add more steps.", 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
        else:
            flash('Failed to create sequence.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

    # --- GET Request Logic ---
    lists = get_lists()
    campaigns = get_campaigns()
    
    # CORRECTED: Create the data structure needed for the JavaScript preview
    campaigns_data = [
        {'id': c.get('id'), 'name': c.get('name'), 'subject': c.get('subject'), 'body': c.get('body')}
        for c in campaigns
    ]

    # CORRECTED: Pass the new data to the template
    return render_template(
        'create_sequence.html', 
        lists=lists, 
        campaigns=campaigns,
        campaigns_data=campaigns_data
    )

@sequence_bp.route('/list', methods=['GET'])
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
    campaigns = get_campaigns()
    campaign_map = {c['id']: c['name'] for c in campaigns}

    return render_template('manage_sequence.html',
                           sequence=sequence,
                           steps=steps,
                           campaigns=campaigns,
                           campaign_map=campaign_map)

@sequence_bp.route('/add_step/<int:sequence_id>', methods=['GET', 'POST'])
@login_required
def add_sequence_step_route(sequence_id):
    sequence = get_sequence(sequence_id)
    if not sequence:
        flash('Sequence not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    campaigns = get_campaigns()

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        day = request.form.get('day')
        schedule_offset_minutes = request.form.get('schedule_offset_minutes', 0)
        is_re_reply = request.form.get('is_re_reply') == 'on'

        if not all([campaign_id, day]):
            flash('Campaign and Day fields are required.', 'error')
            return render_template('add_sequence_step.html', sequence=sequence, campaigns=campaigns)

        try:
            day = int(day)
            schedule_offset_minutes = int(schedule_offset_minutes)
            campaign_id = int(campaign_id)
        except (ValueError, TypeError):
            flash('Day and Schedule Offset must be valid numbers.', 'error')
            return render_template('add_sequence_step.html', sequence=sequence, campaigns=campaigns)

        step_id = create_sequence_step(sequence_id, day, campaign_id, schedule_offset_minutes, is_re_reply)
        if step_id:
            flash('Sequence step added successfully!', 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
        else:
            flash('Failed to add sequence step. A step for that day might already exist.', 'error')
            return render_template('add_sequence_step.html', sequence=sequence, campaigns=campaigns)

    return render_template('add_sequence_step.html', sequence=sequence, campaigns=campaigns)

@sequence_bp.route('/edit_step/<int:step_id>', methods=['GET', 'POST'])
@login_required
def edit_sequence_step_route(step_id):
    step = get_sequence_step(step_id)
    if not step:
        flash('Sequence step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    sequence = get_sequence(step['sequence_id'])
    campaigns = get_campaigns()

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        day = request.form.get('day')
        schedule_offset_minutes = request.form.get('schedule_offset_minutes', 0)
        is_re_reply = request.form.get('is_re_reply') == 'on'

        if not all([campaign_id, day]):
            flash('All step fields are required.', 'error')
            return render_template('edit_sequence_step.html', step=step, sequence=sequence, campaigns=campaigns)

        try:
            day = int(day)
            schedule_offset_minutes = int(schedule_offset_minutes)
            campaign_id = int(campaign_id)
        except (ValueError, TypeError):
            flash('Day and Schedule Offset must be valid numbers.', 'error')
            return render_template('edit_sequence_step.html', step=step, sequence=sequence, campaigns=campaigns)

        if update_sequence_step(step_id, day, campaign_id, schedule_offset_minutes, is_re_reply):
            flash('Sequence step updated successfully!', 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=step['sequence_id']))
        else:
            flash('Failed to update sequence step.', 'error')

    return render_template('edit_sequence_step.html', step=step, sequence=sequence, campaigns=campaigns)

@sequence_bp.route('/delete_step/<int:step_id>', methods=['POST'])
@login_required
def delete_step_route(step_id):
    step = get_sequence_step(step_id)
    if not step:
        flash('Sequence step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    sequence_id = step['sequence_id']
    if delete_sequence_step(step_id):
        flash('Sequence step deleted successfully!', 'success')
    else:
        flash('Failed to delete sequence step.', 'error')
    return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))

@sequence_bp.route('/delete_sequence/<int:sequence_id>', methods=['POST'])
@login_required
def delete_sequence_route(sequence_id):
    if delete_sequence(sequence_id):
        flash('Sequence deleted successfully!', 'success')
    else:
        flash('Failed to delete sequence.', 'error')
    return redirect(url_for('sequence.list_sequences'))