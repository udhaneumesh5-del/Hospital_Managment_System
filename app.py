from flask import Flask, render_template, session, redirect, url_for, flash
from config import config, DevelopmentConfig
from modules.auth import AuthModule
from modules.patient import PatientModule
from modules.doctor import DoctorModule
from modules.appointment import AppointmentModule
from modules.billing import BillingModule
from modules.pharmacy import PharmacyModule
from modules.labtest import LabTestModule
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)
from datetime import datetime

@app.template_filter('format_datetime')
def format_datetime(value):
    if value is None:
        return ""
    return value.strftime("%d-%m-%Y %H:%M")
app.config.from_object(DevelopmentConfig)

# Database connection function
def get_db():
    return MySQLdb.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        cursorclass=MySQLdb.cursors.DictCursor,
        autocommit=False
    )

# Initialize all modules
auth = AuthModule(app, get_db)
patient = PatientModule(app, get_db)
doctor = DoctorModule(app, get_db)
appointment = AppointmentModule(app, get_db)
billing = BillingModule(app, get_db)
pharmacy = PharmacyModule(app, get_db)
labtest = LabTestModule(app, get_db)

# Home Route
@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()

    # Get available doctors for appointment form
    cursor.execute("""
        SELECT d.doctor_id, d.first_name, d.last_name, d.specialization, dept.dept_name
        FROM doctors d
        LEFT JOIN departments dept ON d.department_id = dept.dept_id
        WHERE d.is_available = 1
        ORDER BY d.first_name
    """)
    doctors = cursor.fetchall()
    db.close()

    return render_template('index.html', doctors=doctors)

# Dashboard Routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get statistics for dashboard
    cursor.execute("SELECT COUNT(*) as count FROM patients WHERE is_active = 1")
    total_patients = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM doctors WHERE is_available = 1")
    total_doctors = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = CURDATE() AND status = 'Scheduled'")
    today_appointments = cursor.fetchone()['count']
    
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM billing WHERE MONTH(bill_date) = MONTH(CURDATE())")
    monthly_revenue = cursor.fetchone()['revenue']
    
    cursor.execute("SELECT COUNT(*) as count FROM admissions WHERE status = 'Admitted'")
    current_admissions = cursor.fetchone()['count']
    
    # Recent activities
    cursor.execute("""
        (SELECT 'appointment' as type, appointment_date as date, 
                CONCAT('Appointment scheduled for ', p.first_name, ' ', p.last_name) as description
         FROM appointments a JOIN patients p ON a.patient_id = p.patient_id
         WHERE a.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
         ORDER BY a.created_at DESC LIMIT 5)
        UNION ALL
        (SELECT 'patient' as type, created_at as date,
                CONCAT('New patient registered: ', first_name, ' ', last_name) as description
         FROM patients
         WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
         ORDER BY created_at DESC LIMIT 5)
        ORDER BY date DESC LIMIT 10
    """)
    recent_activities = cursor.fetchall()
    
    db.close()
    
    return render_template('dashboard.html',
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         today_appointments=today_appointments,
                         monthly_revenue=monthly_revenue,
                         current_admissions=current_admissions,
                         recent_activities=recent_activities)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Admin specific statistics
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM staff) as total_staff,
            (SELECT COUNT(*) FROM departments) as total_departments,
            (SELECT COUNT(*) FROM rooms WHERE is_available = 1) as available_rooms,
            (SELECT COALESCE(SUM(total_amount), 0) FROM billing WHERE payment_status = 'Pending') as pending_amount
    """)
    stats = cursor.fetchone()
    
    # Revenue by month for chart
    cursor.execute("""
        SELECT DATE_FORMAT(bill_date, '%Y-%m') as month, SUM(total_amount) as revenue
        FROM billing
        WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(bill_date, '%Y-%m')
        ORDER BY month
    """)
    revenue_chart = cursor.fetchall()
    
    db.close()
    
    return render_template('admin/admin_dashboard.html', stats=stats, revenue_chart=revenue_chart)

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db = get_db()
    db.rollback()
    db.close()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    # Temporary direct routes for appointments (ADD THIS AFTER appointment = AppointmentModule(...))

@app.route('/appointment/new', methods=['GET', 'POST'])
def temp_new_appointment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        try:
            patient_id = request.form.get('patient_id')
            doctor_id = request.form.get('doctor_id')
            appointment_date = request.form.get('appointment_date')
            appointment_time = request.form.get('appointment_time')
            appointment_type = request.form.get('appointment_type')
            symptoms = request.form.get('symptoms', '')
            
            # Generate appointment number
            cursor.execute("SELECT COALESCE(MAX(appointment_id), 0) + 1 FROM appointments")
            result = cursor.fetchone()
            new_id = result['COALESCE(MAX(appointment_id), 0) + 1'] if result else 1
            appointment_number = f"APT{new_id:06d}"
            
            cursor.execute("""
                INSERT INTO appointments 
                (appointment_number, patient_id, doctor_id, appointment_date, 
                 appointment_time, appointment_type, symptoms, status, payment_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Scheduled', 'Pending')
            """, (appointment_number, patient_id, doctor_id, appointment_date, 
                  appointment_time, appointment_type, symptoms))
            
            db.commit()
            appointment_id = cursor.lastrowid
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('appointment_detail', appointment_id=appointment_id))
            
        except Exception as e:
            db.rollback()
            flash(f'Error creating appointment: {str(e)}', 'error')
        finally:
            db.close()
        
        return redirect(url_for('new_appointment'))
    
    # GET request
    cursor.execute("SELECT patient_id, first_name, last_name, mr_number FROM patients WHERE is_active = 1")
    patients = cursor.fetchall()
    
    cursor.execute("SELECT doctor_id, first_name, last_name, specialization FROM doctors WHERE is_available = 1")
    doctors = cursor.fetchall()
    
    db.close()
    
    return render_template('reception/new_appointment.html', patients=patients, doctors=doctors)