from flask import session, request, render_template, redirect, url_for, flash
from functools import wraps
import hashlib
import secrets
from datetime import datetime
import MySQLdb.cursors

class AuthModule:
    def __init__(self, app, db_connection):
        self.app = app
        self.get_db = db_connection
        self.register_routes()
    
    def register_routes(self):
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                
                db = self.get_db()
                cursor = db.cursor()
                
                # Hash password for comparison (in production use proper password hashing)
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute("""
                    SELECT u.*, 
                           p.patient_id, d.doctor_id, s.staff_id,
                           p.first_name as p_first, p.last_name as p_last,
                           d.first_name as d_first, d.last_name as d_last
                    FROM users u
                    LEFT JOIN patients p ON u.user_id = p.user_id
                    LEFT JOIN doctors d ON u.user_id = d.user_id
                    LEFT JOIN staff s ON u.user_id = s.user_id
                    WHERE u.username = %s AND u.password_hash = %s AND u.is_active = 1
                """, (username, password_hash))
                
                user = cursor.fetchone()
                
                if user:
                    session.clear()
                    session['user_id'] = user['user_id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['email'] = user['email']
                    
                    # Store specific IDs based on role
                    if user['patient_id']:
                        session['patient_id'] = user['patient_id']
                        session['patient_name'] = f"{user['p_first']} {user['p_last']}"
                    if user['doctor_id']:
                        session['doctor_id'] = user['doctor_id']
                        session['doctor_name'] = f"Dr. {user['d_first']} {user['d_last']}"
                    
                    # Update last login
                    cursor.execute("UPDATE users SET last_login = %s WHERE user_id = %s", 
                                 (datetime.now(), user['user_id']))
                    db.commit()
                    
                    flash(f'Welcome back, {user["username"]}!', 'success')
                    
                    # Redirect based on role
                    if user['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    elif user['role'] == 'doctor':
                        return redirect(url_for('doctor_dashboard'))
                    elif user['role'] == 'receptionist':
                        return redirect(url_for('dashboard'))
                    elif user['role'] == 'pharmacist':
                        return redirect(url_for('pharmacy_dashboard'))
                    elif user['role'] == 'lab_technician':
                        return redirect(url_for('lab_dashboard'))
                    else:
                        return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password!', 'danger')
                
                db.close()
            
            return render_template('login.html')
        
        @self.app.route('/logout')
        def logout():
            session.clear()
            flash('You have been logged out successfully.', 'info')
            return redirect(url_for('index'))
        
        @self.app.route('/change-password', methods=['GET', 'POST'])
        def change_password():
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            if request.method == 'POST':
                current_password = request.form['current_password']
                new_password = request.form['new_password']
                confirm_password = request.form['confirm_password']
                
                if new_password != confirm_password:
                    flash('New passwords do not match!', 'danger')
                    return redirect(url_for('change_password'))
                
                current_hash = hashlib.sha256(current_password.encode()).hexdigest()
                new_hash = hashlib.sha256(new_password.encode()).hexdigest()
                
                db = self.get_db()
                cursor = db.cursor()
                
                cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (session['user_id'],))
                user = cursor.fetchone()
                
                if user and user['password_hash'] == current_hash:
                    cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", 
                                 (new_hash, session['user_id']))
                    db.commit()
                    flash('Password changed successfully!', 'success')
                else:
                    flash('Current password is incorrect!', 'danger')
                
                db.close()
            
            return render_template('change_password.html')
    
    @staticmethod
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def role_required(*roles):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    flash('Please login to access this page.', 'warning')
                    return redirect(url_for('login'))
                if session.get('role') not in roles:
                    flash('You do not have permission to access this page.', 'danger')
                    return redirect(url_for('dashboard'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator