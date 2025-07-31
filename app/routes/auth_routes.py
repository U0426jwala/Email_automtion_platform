from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from werkzeug.security import check_password_hash
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logger.info(f"Attempting login for username: {username}")
        
        user = User.get_by_username(username)
        logger.info(f"User found: {user}")

        if user and check_password_hash(user.password_hash, password):
            logger.info(f"Login successful for {username}")
            login_user(user)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.home'))

        logger.warning(f"Login failed for {username}")
        flash('Invalid credentials')
        
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    logger.info(f"User {username} logged out")
    return redirect(url_for('auth.login'))
