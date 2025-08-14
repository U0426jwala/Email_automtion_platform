from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.campaign import get_campaigns
from app.models.contact import get_lists

# All necessary model functions are correctly imported
from app.models.sequence import (
    create_sequence, 
    get_sequences, 
    get_sequence,
    create_sequence_step, 
    get_sequence_steps, 
    get_sequence_step,
    update_sequence_step, 
    delete_sequence_step, 
    delete_sequence
)
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sequence_bp = Blueprint('sequence', __name__, url_prefix='/sequences')

@sequence_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_sequence_route():
    """Handles the creation of a new sequence with one or more steps."""
    if request.method == 'POST':
        sequence_name = request.form.get('sequence_name')
        step1_list_id = request.form.get('step[1][list_id]')

        if not sequence_name or not step1_list_id:
            flash('Sequence Name and a Contact List for Step 1 are required.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

        # Create the main sequence, correctly saving the integer user ID
        sequence_id = create_sequence(sequence_name, step1_list_id, current_user.id, status='active')

        if not sequence_id:
            flash('Failed to create sequence.', 'error')
            return redirect(url_for('sequence.create_sequence_route'))

        # Process all steps submitted with the form
        step_keys = [key for key in request.form if key.startswith('step[')]
        
        max_step = 0
        if step_keys:
            max_step = max([int(key.split('[')[1].split(']')[0]) for key in step_keys])

        steps_created = 0
        for i in range(1, max_step + 1):
            campaign_id = request.form.get(f'step[{i}][campaign_id]')
            schedule_time_str = request.form.get(f'step[{i}][schedule_time]')

            if campaign_id and schedule_time_str:
                try:
                    schedule_time = datetime.fromisoformat(schedule_time_str)
                    is_re_reply = (i > 1)

                    create_sequence_step(
                        sequence_id=sequence_id,
                        step_number=i,
                        type='mailer',
                        campaign_id=int(campaign_id),
                        schedule_time=schedule_time,
                        is_re_reply=is_re_reply,
                        status='scheduled'
                    )
                    steps_created += 1
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing form data for step {i}: {e}", exc_info=True)
                    flash(f'Invalid data for step {i}. It was skipped.', 'warning')
                    continue
        
        if steps_created == 0:
            flash('No valid steps were provided. The sequence was created but has no steps.', 'error')
            return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))

        flash(f"Sequence '{sequence_name}' created with {steps_created} scheduled step(s)!", 'success')
        return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))

    # For GET requests, display the form
    lists = get_lists()
    campaigns = get_campaigns()
    return render_template('create_sequence.html', lists=lists, campaigns=campaigns)


@sequence_bp.route('/list')
@login_required
def list_sequences():
    """Displays all created sequences."""
    sequences = get_sequences()
    return render_template('sequence.html', sequences=sequences)


@sequence_bp.route('/manage/<int:sequence_id>', methods=['GET'])
@login_required
def manage_sequence(sequence_id):
    """Displays the details and steps of a single sequence."""
    sequence = get_sequence(sequence_id)
    if not sequence:
        flash('Sequence not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    steps = get_sequence_steps(sequence_id)
    return render_template('manage_sequence.html', sequence=sequence, steps=steps)

@sequence_bp.route('/add_step/<int:sequence_id>', methods=['GET', 'POST'])
@login_required
def add_sequence_step_route(sequence_id):
    """Handles adding a new step to an existing sequence."""
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

        try:
            schedule_time = datetime.fromisoformat(schedule_time_str)
            campaign_id = int(campaign_id)
        except ValueError:
            flash('Invalid input format.', 'error')
            return redirect(url_for('sequence.add_sequence_step_route', sequence_id=sequence_id))

        steps = get_sequence_steps(sequence_id)
        next_step_number = len(steps) + 1
        is_re_reply = next_step_number > 1

        if create_sequence_step(sequence_id, next_step_number, 'mailer', campaign_id, schedule_time, is_re_reply, status='scheduled'):
            flash('New step added successfully!', 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))
        else:
            flash('Failed to add the new step.', 'error')

    # For GET requests, display the add step form
    campaigns = get_campaigns()
    return render_template('add_sequence_step.html', sequence=sequence, campaigns=campaigns)

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

        if not all([campaign_id, schedule_time_str]):
            flash('All fields are required.', 'error')
            return redirect(url_for('sequence.edit_sequence_step_route', step_id=step_id))

        try:
            schedule_time = datetime.fromisoformat(schedule_time_str)
            campaign_id = int(campaign_id)
        except ValueError:
            flash('Invalid input format.', 'error')
            return redirect(url_for('sequence.edit_sequence_step_route', step_id=step_id))

        is_re_reply = step['step_number'] > 1

        if update_sequence_step(step_id, step['step_number'], 'mailer', campaign_id, schedule_time, is_re_reply):
            flash('Step updated successfully!', 'success')
            return redirect(url_for('sequence.manage_sequence', sequence_id=step['sequence_id']))
        else:
            flash('Failed to update step.', 'error')
            
    # For GET requests, display the edit step form
    campaigns = get_campaigns()
    return render_template('edit_sequence_step.html', step=step, campaigns=campaigns)

@sequence_bp.route('/delete_step/<int:step_id>', methods=['POST'])
@login_required
def delete_step_route(step_id):
    """Handles deleting a single step."""
    step = get_sequence_step(step_id)
    if not step:
        flash('Step not found.', 'error')
        return redirect(url_for('sequence.list_sequences'))

    sequence_id = step['sequence_id']
    if delete_sequence_step(step_id):
        flash('Step deleted successfully.', 'success')
    else:
        flash('Failed to delete step.', 'error')
    return redirect(url_for('sequence.manage_sequence', sequence_id=sequence_id))

@sequence_bp.route('/delete_sequence/<int:sequence_id>', methods=['POST'])
@login_required
def delete_sequence_route(sequence_id):
    """Handles deleting an entire sequence."""
    if delete_sequence(sequence_id):
        flash('Sequence and all its steps have been deleted.', 'success')
    else:
        flash('Failed to delete sequence.', 'error')
    return redirect(url_for('sequence.list_sequences'))