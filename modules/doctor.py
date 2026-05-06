from flask import request, render_template, redirect, url_for, flash, session, jsonify
from datetime import datetime

class DoctorModule:
    def __init__(self, app, db_connection):
        self.app = app
        self.get_db = db_connection
        self.register_routes()
    
    def register_routes(self):
        
        @self.app.route('/doctors')
        def doctors():
            if 'user_id' not in session:
                return redirect(url_for('login'))

            # If logged in as doctor, redirect to their own profile
            if session.get('role') == 'doctor':
                doctor_id = session.get('doctor_id')
                if doctor_id:
                    return redirect(url_for('doctor_detail', doctor_id=doctor_id))
                else:
                    flash('Doctor profile not found!', 'warning')
                    return redirect(url_for('dashboard'))

            search_query = request.args.get('search', '')
            department = request.args.get('department', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            query = """
                SELECT d.*, dept.dept_name,
                       (SELECT COUNT(*) FROM appointments WHERE doctor_id = d.doctor_id AND status = 'Scheduled' AND appointment_date = CURDATE()) as today_appointments,
                       d.rating as avg_rating
                FROM doctors d
                LEFT JOIN departments dept ON d.department_id = dept.dept_id
                WHERE 1=1
            """
            params = []
            
            if search_query:
                query += " AND (d.first_name LIKE %s OR d.last_name LIKE %s OR d.specialization LIKE %s)"
                params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
            
            if department:
                query += " AND dept.dept_name = %s"
                params.append(department)
            
            query += " ORDER BY d.first_name"
            
            cursor.execute(query, params)
            doctors = cursor.fetchall()
            
            db.close()
            
            return render_template('doctors/doctors.html',
                                 doctors=doctors,
                                 search_query=search_query,
                                 department=department)
        
        @self.app.route('/doctor/new', methods=['GET'])
        def new_doctor():
            """Show add doctor form"""
            if 'user_id' not in session or session.get('role') != 'admin':
                flash('You do not have permission to add doctors!', 'danger')
                return redirect(url_for('doctors'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Get departments for dropdown
            try:
                cursor.execute("SELECT dept_id, dept_name FROM departments ORDER BY dept_name")
                departments = cursor.fetchall()
            except:
                departments = []
            
            db.close()
            
            return render_template('admin/new_doctor.html', departments=departments)
        
        @self.app.route('/add_doctor', methods=['POST'])
        def add_doctor():
            """Add new doctor (POST)"""
            print("=" * 50)
            print("ADD DOCTOR FUNCTION CALLED")
            print("=" * 50)
            
            # Check authentication
            if 'user_id' not in session:
                flash('Please login first!', 'danger')
                return redirect(url_for('login'))
            
            if session.get('role') != 'admin':
                flash('You do not have permission to add doctors!', 'danger')
                return redirect(url_for('doctors'))
            
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            specialization = request.form.get('specialization')
            department_id = request.form.get('department_id')
            qualification = request.form.get('qualification')
            experience_years = request.form.get('experience_years', 0)
            phone = request.form.get('phone')
            email = request.form.get('email')
            consultation_fee = request.form.get('consultation_fee', 0)
            available_days = request.form.get('available_days')
            available_time_start = request.form.get('available_time_start')
            available_time_end = request.form.get('available_time_end')
            bio = request.form.get('bio')
            
            # Validation
            if not first_name or not last_name or not specialization or not phone:
                flash('Please fill all required fields!', 'danger')
                return redirect(url_for('new_doctor'))
            
            # Generate doctor code
            doctor_code = f"DOC{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            print(f"Doctor Code: {doctor_code}")
            print(f"Name: {first_name} {last_name}")
            print(f"Specialization: {specialization}")
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                # Check if doctor with same phone exists
                cursor.execute("SELECT doctor_id FROM doctors WHERE phone = %s", (phone,))
                existing = cursor.fetchone()
                if existing:
                    flash('A doctor with this phone number already exists!', 'danger')
                    return redirect(url_for('new_doctor'))
                
                # Insert doctor
                insert_query = """
                    INSERT INTO doctors (
                        doctor_code, first_name, last_name, specialization, department_id,
                        qualification, experience_years, phone, email, consultation_fee,
                        available_days, available_time_start, available_time_end, bio, is_available
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                """
                
                insert_values = (
                    doctor_code, first_name, last_name, specialization, 
                    department_id if department_id else None,
                    qualification, experience_years, phone, email, consultation_fee,
                    available_days, available_time_start, available_time_end, bio
                )
                
                print(f"Executing query: {insert_query}")
                print(f"Values: {insert_values}")
                
                cursor.execute(insert_query, insert_values)
                db.commit()
                
                doctor_id = cursor.lastrowid
                print(f"Doctor inserted with ID: {doctor_id}")
                
                flash(f'Doctor {first_name} {last_name} added successfully! Code: {doctor_code}', 'success')
                return redirect(url_for('doctor_detail', doctor_id=doctor_id))
                
            except Exception as e:
                db.rollback()
                print(f"ERROR: {str(e)}")
                flash(f'Error adding doctor: {str(e)}', 'danger')
                return redirect(url_for('new_doctor'))
            finally:
                db.close()
        
        @self.app.route('/doctor/<int:doctor_id>')
        def doctor_detail(doctor_id):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT d.*, dept.dept_name,
                       (SELECT COUNT(*) FROM appointments WHERE doctor_id = d.doctor_id) as total_appointments
                FROM doctors d
                LEFT JOIN departments dept ON d.department_id = dept.dept_id
                WHERE d.doctor_id = %s
            """, (doctor_id,))
            doctor = cursor.fetchone()
            
            if not doctor:
                flash('Doctor not found!', 'danger')
                return redirect(url_for('doctors'))
            
            # Get today's appointments
            cursor.execute("""
                SELECT a.*, p.first_name, p.last_name, p.mr_number, p.phone
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.doctor_id = %s AND a.appointment_date = CURDATE()
                ORDER BY a.appointment_time
            """, (doctor_id,))
            today_appointments = cursor.fetchall()
            
            # Get upcoming appointments
            cursor.execute("""
                SELECT a.*, p.first_name, p.last_name, p.mr_number
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.doctor_id = %s AND a.appointment_date > CURDATE() AND a.status = 'Scheduled'
                ORDER BY a.appointment_date, a.appointment_time
                LIMIT 20
            """, (doctor_id,))
            upcoming_appointments = cursor.fetchall()
            
            db.close()
            
            return render_template('doctors/doctor_detail.html',
                                 doctor=doctor,
                                 today_appointments=today_appointments,
                                 upcoming_appointments=upcoming_appointments)
        
        @self.app.route('/doctor/<int:doctor_id>/edit', methods=['GET', 'POST'])
        def edit_doctor(doctor_id):
            if 'user_id' not in session or session.get('role') != 'admin':
                flash('You do not have permission to edit doctors!', 'danger')
                return redirect(url_for('doctors'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            if request.method == 'POST':
                try:
                    cursor.execute("""
                        UPDATE doctors SET
                            first_name = %s, last_name = %s, specialization = %s,
                            department_id = %s, qualification = %s, experience_years = %s,
                            phone = %s, email = %s, consultation_fee = %s,
                            available_days = %s, available_time_start = %s,
                            available_time_end = %s, bio = %s, is_available = %s
                        WHERE doctor_id = %s
                    """, (
                        request.form.get('first_name'),
                        request.form.get('last_name'),
                        request.form.get('specialization'),
                        request.form.get('department_id') if request.form.get('department_id') else None,
                        request.form.get('qualification'),
                        request.form.get('experience_years', 0),
                        request.form.get('phone'),
                        request.form.get('email'),
                        request.form.get('consultation_fee', 0),
                        request.form.get('available_days'),
                        request.form.get('available_time_start'),
                        request.form.get('available_time_end'),
                        request.form.get('bio'),
                        1 if request.form.get('is_available') else 0,
                        doctor_id
                    ))
                    
                    db.commit()
                    flash('Doctor updated successfully!', 'success')
                    return redirect(url_for('doctor_detail', doctor_id=doctor_id))
                    
                except Exception as e:
                    db.rollback()
                    flash(f'Error updating doctor: {str(e)}', 'danger')
            
            # GET request
            cursor.execute("""
                SELECT d.*, dept.dept_name
                FROM doctors d
                LEFT JOIN departments dept ON d.department_id = dept.dept_id
                WHERE d.doctor_id = %s
            """, (doctor_id,))
            doctor = cursor.fetchone()
            
            cursor.execute("SELECT dept_id, dept_name FROM departments ORDER BY dept_name")
            departments = cursor.fetchall()
            
            db.close()
            
            if not doctor:
                flash('Doctor not found!', 'danger')
                return redirect(url_for('doctors'))
            
            return render_template('doctors/edit_doctor.html', doctor=doctor, departments=departments)
        
        @self.app.route('/doctor/<int:doctor_id>/delete', methods=['POST'])
        def delete_doctor(doctor_id):
            if 'user_id' not in session or session.get('role') != 'admin':
                flash('Access denied!', 'danger')
                return redirect(url_for('doctors'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE doctor_id = %s", (doctor_id,))
                result = cursor.fetchone()
                if result['count'] > 0:
                    flash('Cannot delete doctor with existing appointments!', 'danger')
                    return redirect(url_for('doctors'))
                
                cursor.execute("DELETE FROM doctors WHERE doctor_id = %s", (doctor_id,))
                db.commit()
                flash('Doctor deleted successfully!', 'success')
                
            except Exception as e:
                db.rollback()
                flash(f'Error deleting doctor: {str(e)}', 'danger')
            finally:
                db.close()
            
            return redirect(url_for('doctors'))
        
        @self.app.route('/doctor_dashboard')
        def doctor_dashboard():
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            doctor_id = session.get('doctor_id')
            
            if not doctor_id:
                return redirect(url_for('doctors'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'Scheduled' THEN 1 END) as scheduled,
                    COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) as cancelled
                FROM appointments
                WHERE doctor_id = %s AND appointment_date = CURDATE()
            """, (doctor_id,))
            today_stats = cursor.fetchone()
            
            if not today_stats:
                today_stats = {'scheduled': 0, 'completed': 0, 'cancelled': 0}
            
            cursor.execute("""
                SELECT DISTINCT p.patient_id, p.first_name, p.last_name, p.mr_number,
                       MAX(a.appointment_date) as last_visit
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.doctor_id = %s
                GROUP BY p.patient_id
                ORDER BY last_visit DESC
                LIMIT 10
            """, (doctor_id,))
            recent_patients = cursor.fetchall()
            
            db.close()
            
            return render_template('doctors/doctor_dashboard.html',
                                 today_stats=today_stats,
                                 recent_patients=recent_patients)
        
        @self.app.route('/api/doctors/available')
        def api_available_doctors():
            date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            db = self.get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT d.doctor_id, d.first_name, d.last_name, d.specialization, d.consultation_fee
                FROM doctors d
                WHERE d.is_available = 1
                AND NOT EXISTS (
                    SELECT 1 FROM appointments a 
                    WHERE a.doctor_id = d.doctor_id 
                    AND a.appointment_date = %s 
                    AND a.status NOT IN ('Cancelled', 'Completed')
                )
                LIMIT 20
            """, (date,))
            
            doctors = cursor.fetchall()
            db.close()
            
            return jsonify({'doctors': doctors})
    
    def list_doctors(self):
        pass
    
    def view_doctor(self, doctor_id):
        pass
    
    def create_doctor(self):
        pass
    
    def update_doctor(self, doctor_id):
        pass