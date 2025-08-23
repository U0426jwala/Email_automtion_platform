# app/routes/sequence_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.sequence import (
    create_sequence, get_sequences, get_sequences_by_user, get_sequence, delete_sequence,
    create_sequence_step, get_sequence_steps, get_sequence_step,
    update_sequence_step, delete_sequence_step
)
from app.models.contact import get_lists
from app.models.campaign import get_campaigns, get_campaign
from app.models.smtp_config import get_smtp_configs
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sequence_bp = Blueprint('sequence', __name__, url_prefix='/sequences')

@sequence_bp.route('/')
@login_required
def list_sequences():
    """Renders the main sequences page."""
    # --- FIX: Call the correct function designed for user-specific sequences ---
    sequences = get_sequences_by_user(current_user.id)
    return render_template('sequence.html', sequences=sequences)

@sequence_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_sequence_route():
    """Handles the creation of a new sequence and its initial steps."""
    if request.method == 'POST':
        # --- FIX 1: Use the correct form names from the HTML ---
        name = request.form.get('sequence_name')
        list_id = request.form.get('list_id')
        config_id = request.form.get('sending_config')

        if not all([name, list_id, config_id]):
            flash('Sequence Name, Send Using, and Contact List are required.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

        # Create the main sequence record first
        sequence_id = create_sequence(
            name=name,
            list_id=int(list_id),
            created_by=current_user.id,
            config_type='smtp',
            config_id=int(config_id)
        )

        if sequence_id:
            # --- FIX 2: Add logic to parse and save the initial steps ---
            try:
                steps_data = {}
                # Use regex to find all form keys related to steps (e.g., "step[1][campaign_id]")
                step_pattern = re.compile(r'step\[(\d+)\]\[(\w+)\]')

                for key, value in request.form.items():
                    match = step_pattern.match(key)
                    if match:
                        step_number, field_name = match.groups()
                        if step_number not in steps_data:
                            steps_data[step_number] = {}
                        steps_data[step_number][field_name] = value

                # Loop through the parsed steps, sorted by their number, and create them
                for step_number in sorted(steps_data.keys(), key=int):
                    step = steps_data[step_number]
                    campaign_id = step.get('campaign_id')
                    schedule_time_str = step.get('schedule_time')
                    is_re_reply = 'is_re_reply' in step

                    if campaign_id and schedule_time_str:
                        schedule_time = datetime.fromisoformat(schedule_time_str)
                        create_sequence_step(
                            sequence_id=sequence_id,
                            step_number=int(step_number),
                            step_type='mailer',
                            related_id=int(campaign_id),
                            schedule_time=schedule_time,
                            is_re_reply=is_re_reply
                        )

                flash('Sequence and its initial steps were created successfully!', 'success')
                return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))

            except Exception as e:
                logger.error(f"Error creating sequence steps for sequence_id {sequence_id}: {e}")
                flash('Sequence was created, but there was an error adding the steps.', 'error')
                return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
        else:
            flash('Failed to create the sequence.', 'error')

    # This part handles the GET request (page load)
    lists = get_lists()
    smtp_configs = get_smtp_configs(current_user.id)
    campaigns = get_campaigns()

    return render_template('create_sequence.html', lists=lists, smtp_configs=smtp_configs, campaigns=campaigns)


@sequence_bp.route('/manage/<int:sequence_id>')
@login_required
def manage_sequence(sequence_id):
    """Manages a specific sequence, showing its steps."""
    sequence = get_sequence(sequence_id)
    if not sequence:
        flash('Sequence not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    steps = get_sequence_steps(sequence_id)
    return render_template('manage_sequence.html', sequence=sequence, steps=steps)

@sequence_bp.route('/delete/<int:sequence_id>', methods=['POST'])
@login_required
def delete_sequence_route(sequence_id):
    """Deletes a sequence and its steps."""
    if delete_sequence(sequence_id):
        flash('Sequence deleted successfully.', 'success')
    else:
        flash('Error deleting sequence.', 'error')
    return redirect(url_for('sequence.list_sequences'))

@sequence_bp.route('/add_step/<int:sequence_id>', methods=['GET', 'POST'])
@login_required
def add_sequence_step_route(sequence_id):
    """Handles adding a new step to a sequence."""
    sequence = get_sequence(sequence_id)
    if not sequence:
        flash('Sequence not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    steps = get_sequence_steps(sequence_id)
    next_step_number = len(steps) + 1

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        schedule_time_str = request.form.get('schedule_time')

        if not all([campaign_id, schedule_time_str]):
            flash('Campaign and Schedule Time are required.', 'error')
            return render_template('add_sequence_step.html', sequence=sequence, campaigns=get_campaigns(), step_number=next_step_number)

        try:
            schedule_time = datetime.fromisoformat(schedule_time_str)
        except ValueError:
            flash('Invalid datetime format.', 'error')
            return render_template('add_sequence_step.html', sequence=sequence, campaigns=get_campaigns(), step_number=next_step_number)

        is_re_reply = 'is_re_reply' in request.form

        if create_sequence_step(sequence_id, next_step_number, 'mailer', int(campaign_id), schedule_time, is_re_reply):
            flash('New step added successfully!', 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
        else:
            flash('Failed to add the new step.', 'error')

    campaigns = get_campaigns()
    return render_template('add_sequence_step.html', sequence=sequence, campaigns=campaigns, step_number=next_step_number)


@sequence_bp.route('/edit_step/<int:step_id>', methods=['GET', 'POST'])
@login_required
def edit_sequence_step_route(step_id):
    """Handles editing an existing sequence step."""
    step = get_sequence_step(step_id)
    if not step:
        flash('Step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        schedule_time_str = request.form.get('schedule_time')
        is_re_reply = 'is_re_reply' in request.form

        if not all([campaign_id, schedule_time_str]):
            flash('All fields are required.', 'error')
            return redirect(url_for('sequence.edit_sequence_step_route', step_id=step_id))

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
def delete_sequence_step_route(step_id):
    """Deletes a sequence step."""
    step = get_sequence_step(step_id)
    if not step:
        flash('Step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    sequence_id = step['sequence_id']
    if delete_sequence_step(step_id):
        flash('Step deleted successfully.', 'success')
    else:
        flash('Error deleting step.', 'error')
    return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))