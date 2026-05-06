from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime

class AppointmentModule:
    def __init__(self, app, get_db):
        self.app = app
        self.get_db = get_db
        self.register_routes()
    
    def register_routes(self):
        """Register all appointment routes"""
        
        @self.app.route('/appointments')
        def appointments():
            """List all appointments"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Get filter parameters
            status_filter = request.args.get('status', '')
            date_filter = request.args.get('date', '')
            
            # Build query
            query = """
                SELECT a.*, 
                       p.first_name as patient_first, p.last_name as patient_last, 
                       p.mr_number, p.phone, p.email,
                       d.first_name as doctor_first, d.last_name as doctor_last, 
                       d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE 1=1
            """
            params = []
            
            if status_filter:
                query += " AND a.status = %s"
                params.append(status_filter)
            
            if date_filter:
                query += " AND a.appointment_date = %s"
                params.append(date_filter)
            
            query += " ORDER BY a.appointment_date DESC, a.appointment_time ASC"
            
            cursor.execute(query, params)
            appointments = cursor.fetchall()
            
            # Get distinct statuses for filter
            cursor.execute("SELECT DISTINCT status FROM appointments")
            statuses = cursor.fetchall()
            
            db.close()
            
            return render_template('reception/appointments.html',
                                 appointments=appointments,
                                 statuses=statuses,
                                 current_status=status_filter,
                                 current_date=date_filter)
        
        @self.app.route('/appointment/<int:appointment_id>')
        def appointment_detail(appointment_id):
            """Show single appointment details"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT a.*,
                       p.first_name as patient_first, p.last_name as patient_last,
                       p.mr_number, p.phone, p.email,
                       d.first_name as doctor_first, d.last_name as doctor_last,
                       d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.appointment_id = %s
            """, (appointment_id,))
            
            appointment = cursor.fetchone()
            db.close()
            
            if appointment is None:
                flash('Appointment not found!', 'error')
                return redirect(url_for('appointments'))
            
            return render_template('reception/appointment_detail.html', appointment=appointment)
        
        @self.app.route('/appointment/new', methods=['GET', 'POST'])
        def new_appointment():
            """Create new appointment (from dashboard)"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            if request.method == 'POST':
                try:
                    patient_id = request.form.get('patient_id')
                    doctor_id = request.form.get('doctor_id')
                    appointment_date = request.form.get('appointment_date')
                    appointment_time = request.form.get('appointment_time')
                    appointment_type = request.form.get('appointment_type')
                    symptoms = request.form.get('symptoms', '')
                    
                    # Validation
                    if not all([patient_id, doctor_id, appointment_date, appointment_time, appointment_type]):
                        flash('Please fill all required fields!', 'error')
                        return redirect(url_for('new_appointment'))
                    
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
                    return redirect(url_for('new_appointment'))
                finally:
                    db.close()
            
            # GET request - show form
            cursor.execute("SELECT patient_id, first_name, last_name, mr_number FROM patients WHERE is_active = 1 ORDER BY first_name")
            patients = cursor.fetchall()
            
            cursor.execute("SELECT doctor_id, first_name, last_name, specialization FROM doctors WHERE is_available = 1 ORDER BY first_name")
            doctors = cursor.fetchall()
            
            db.close()
            
            return render_template('reception/new_appointment.html', patients=patients, doctors=doctors)
        
        @self.app.route('/add_appointment', methods=['POST'])
        def add_appointment():
            """Add appointment from homepage form"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                # Get form data
                patient_name = request.form.get('patient_name')
                patient_phone = request.form.get('patient_phone')
                patient_email = request.form.get('patient_email')
                doctor_id = request.form.get('doctor_id')
                appointment_date = request.form.get('appointment_date')
                appointment_time = request.form.get('appointment_time')
                symptoms = request.form.get('symptoms')
                
                # First, check if patient exists, if not create new patient
                cursor.execute("SELECT patient_id FROM patients WHERE phone = %s", (patient_phone,))
                existing_patient = cursor.fetchone()
                
                if existing_patient:
                    patient_id = existing_patient['patient_id']
                else:
                    # Generate MR number
                    cursor.execute("SELECT COALESCE(MAX(patient_id), 0) + 1 FROM patients")
                    result = cursor.fetchone()
                    new_id = result['COALESCE(MAX(patient_id), 0) + 1'] if result else 1
                    mr_number = f"MR{new_id:06d}"
                    
                    cursor.execute("""
                        INSERT INTO patients (first_name, last_name, phone, email, mr_number, is_active)
                        VALUES (%s, %s, %s, %s, %s, 1)
                    """, (patient_name, '', patient_phone, patient_email, mr_number))
                    
                    patient_id = cursor.lastrowid
                
                # Generate appointment number
                cursor.execute("SELECT COALESCE(MAX(appointment_id), 0) + 1 FROM appointments")
                result = cursor.fetchone()
                new_id = result['COALESCE(MAX(appointment_id), 0) + 1'] if result else 1
                appointment_number = f"APT{new_id:06d}"
                
                # Create appointment
                cursor.execute("""
                    INSERT INTO appointments 
                    (appointment_number, patient_id, doctor_id, appointment_date, 
                     appointment_time, symptoms, status, payment_status, appointment_type)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Scheduled', 'Pending', 'General')
                """, (appointment_number, patient_id, doctor_id, appointment_date, 
                      appointment_time, symptoms))
                
                db.commit()
                appointment_id = cursor.lastrowid
                flash('Appointment booked successfully! We will contact you soon.', 'success')
                return redirect(url_for('appointment_detail', appointment_id=appointment_id))
                
            except Exception as e:
                db.rollback()
                flash(f'Error booking appointment: {str(e)}', 'error')
                return redirect(url_for('index'))
            finally:
                db.close()
        
        @self.app.route('/appointment/<int:appointment_id>/edit', methods=['GET', 'POST'])
        def edit_appointment(appointment_id):
            """Edit appointment"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            if request.method == 'POST':
                try:
                    appointment_date = request.form.get('appointment_date')
                    appointment_time = request.form.get('appointment_time')
                    appointment_type = request.form.get('appointment_type')
                    symptoms = request.form.get('symptoms', '')
                    
                    cursor.execute("""
                        UPDATE appointments 
                        SET appointment_date = %s, appointment_time = %s, 
                            appointment_type = %s, symptoms = %s
                        WHERE appointment_id = %s
                    """, (appointment_date, appointment_time, appointment_type, symptoms, appointment_id))
                    
                    db.commit()
                    flash('Appointment updated successfully!', 'success')
                    return redirect(url_for('appointment_detail', appointment_id=appointment_id))
                    
                except Exception as e:
                    db.rollback()
                    flash(f'Error updating appointment: {str(e)}', 'error')
                finally:
                    db.close()
            
            # GET request - show form
            cursor.execute("""
                SELECT a.*, p.first_name as patient_first, p.last_name as patient_last,
                       d.first_name as doctor_first, d.last_name as doctor_last
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.appointment_id = %s
            """, (appointment_id,))
            
            appointment = cursor.fetchone()
            
            cursor.execute("SELECT doctor_id, first_name, last_name, specialization FROM doctors WHERE is_available = 1")
            doctors = cursor.fetchall()
            
            db.close()
            
            if appointment is None:
                flash('Appointment not found!', 'error')
                return redirect(url_for('appointments'))
            
            return render_template('reception/edit_appointment.html', appointment=appointment, doctors=doctors)
        
        @self.app.route('/appointment/<int:appointment_id>/status/<string:status>')
        def update_appointment_status(appointment_id, status):
            """Update appointment status"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            valid_statuses = ['Scheduled', 'Completed', 'Cancelled', 'No Show']
            if status not in valid_statuses:
                flash('Invalid status!', 'error')
                return redirect(url_for('appointment_detail', appointment_id=appointment_id))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                cursor.execute("""
                    UPDATE appointments 
                    SET status = %s 
                    WHERE appointment_id = %s
                """, (status, appointment_id))
                
                db.commit()
                flash(f'Appointment marked as {status}!', 'success')
                
            except Exception as e:
                db.rollback()
                flash(f'Error updating status: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('appointment_detail', appointment_id=appointment_id))
        
        @self.app.route('/appointment/<int:appointment_id>/delete', methods=['POST'])
        def delete_appointment(appointment_id):
            """Delete appointment"""
            if 'user_id' not in session or session.get('role') != 'admin':
                flash('Access denied!', 'error')
                return redirect(url_for('appointments'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))
                db.commit()
                flash('Appointment deleted successfully!', 'success')
                
            except Exception as e:
                db.rollback()
                flash(f'Error deleting appointment: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('appointments'))
        
        @self.app.route('/calendar')
        def calendar():
            """Appointment calendar view"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            return render_template('calendar.html')
        
        @self.app.route('/api/appointments')
        def api_appointments():
            """API endpoint for calendar appointments"""
            if 'user_id' not in session:
                return {'error': 'Unauthorized'}, 401
            
            start_date = request.args.get('start', '')
            end_date = request.args.get('end', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            query = """
                SELECT a.appointment_id as id, a.appointment_date as date, a.appointment_time as time,
                       a.status, a.appointment_number,
                       p.first_name as patient_first, p.last_name as patient_last,
                       d.first_name as doctor_first, d.last_name as doctor_last
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.appointment_date BETWEEN %s AND %s
                ORDER BY a.appointment_date, a.appointment_time
            """
            
            cursor.execute(query, (start_date, end_date))
            appointments = cursor.fetchall()
            db.close()
            
            # Format for calendar
            events = []
            for apt in appointments:
                events.append({
                    'id': apt['id'],
                    'title': f"{apt['patient_first']} {apt['patient_last']} - Dr. {apt['doctor_last']}",
                    'start': f"{apt['date']}T{apt['time']}",
                    'status': apt['status'],
                    'appointment_number': apt['appointment_number']
                })
            
            return {'events': events}
    
    # These methods are called from app.py
    def appointments_list(self):
        """Wrapper for appointments route"""
        pass
    
    def view_appointment(self, appointment_id):
        """Wrapper for appointment_detail route"""
        pass
    
    def create_appointment(self):
        """Wrapper for new_appointment route"""
        pass
    
    def edit_appointment(self, appointment_id):
        """Wrapper for edit_appointment route"""
        pass
    
    def update_status(self, appointment_id, status):
        """Wrapper for update_appointment_status route"""
        pass
    
    def delete_appointment(self, appointment_id):
        """Wrapper for delete_appointment route"""
        pass