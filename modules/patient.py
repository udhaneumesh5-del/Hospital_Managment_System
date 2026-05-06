from flask import request, render_template, redirect, url_for, flash, session, jsonify
from datetime import datetime

class PatientModule:
    def __init__(self, app, db_connection):
        self.app = app
        self.get_db = db_connection
        self.register_routes()
    
    def register_routes(self):
        @self.app.route('/patients')
        def patients():
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            page = request.args.get('page', 1, type=int)
            per_page = 10
            offset = (page - 1) * per_page
            search = request.args.get('search', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Get total count
            if search:
                cursor.execute("""
                    SELECT COUNT(*) as total FROM patients 
                    WHERE first_name LIKE %s OR last_name LIKE %s OR mr_number LIKE %s OR phone LIKE %s
                """, (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'))
            else:
                cursor.execute("SELECT COUNT(*) as total FROM patients")
            
            total = cursor.fetchone()['total']
            total_pages = (total + per_page - 1) // per_page
            
            # Get patients with pagination
            if search:
                cursor.execute("""
                    SELECT p.*, 
                           (SELECT COUNT(*) FROM appointments WHERE patient_id = p.patient_id) as total_visits,
                           (SELECT COUNT(*) FROM billing WHERE patient_id = p.patient_id AND payment_status = 'Pending') as pending_bills
                    FROM patients p
                    WHERE p.first_name LIKE %s OR p.last_name LIKE %s OR p.mr_number LIKE %s OR p.phone LIKE %s
                    ORDER BY p.patient_id DESC
                    LIMIT %s OFFSET %s
                """, (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', per_page, offset))
            else:
                cursor.execute("""
                    SELECT p.*, 
                           (SELECT COUNT(*) FROM appointments WHERE patient_id = p.patient_id) as total_visits,
                           (SELECT COUNT(*) FROM billing WHERE patient_id = p.patient_id AND payment_status = 'Pending') as pending_bills
                    FROM patients p
                    ORDER BY p.patient_id DESC
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
            
            patients = cursor.fetchall()
            db.close()
            
            return render_template('reception/patients.html',
                                 patients=patients,
                                 page=page,
                                 total_pages=total_pages,
                                 search=search)
        
        @self.app.route('/patient/<int:patient_id>')
        def patient_detail(patient_id):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Get patient details
            cursor.execute("""
                SELECT p.*, 
                       (SELECT COUNT(*) FROM appointments WHERE patient_id = p.patient_id) as total_appointments,
                       (SELECT COUNT(*) FROM medical_records WHERE patient_id = p.patient_id) as total_records
                FROM patients p
                WHERE p.patient_id = %s
            """, (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash('Patient not found!', 'danger')
                return redirect(url_for('patients'))
            
            # Get recent appointments
            cursor.execute("""
                SELECT a.*, d.first_name as doctor_first, d.last_name as doctor_last, d.specialization
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.patient_id = %s
                ORDER BY a.appointment_date DESC
                LIMIT 10
            """, (patient_id,))
            appointments = cursor.fetchall()
            
            # Get recent bills
            cursor.execute("""
                SELECT b.* FROM billing b
                WHERE b.patient_id = %s
                ORDER BY b.bill_date DESC
                LIMIT 10
            """, (patient_id,))
            bills = cursor.fetchall()
            
            # Get medical records
            cursor.execute("""
                SELECT mr.*, d.first_name as doctor_first, d.last_name as doctor_last
                FROM medical_records mr
                LEFT JOIN doctors d ON mr.doctor_id = d.doctor_id
                WHERE mr.patient_id = %s
                ORDER BY mr.record_date DESC
                LIMIT 10
            """, (patient_id,))
            medical_records = cursor.fetchall()
            
            db.close()
            
            return render_template('reception/patient_detail.html',
                                 patient=patient,
                                 appointments=appointments,
                                 bills=bills,
                                 medical_records=medical_records)
        
        @self.app.route('/add_patient', methods=['POST'])
        def add_patient():
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            # Generate MR Number
            mr_number = f"MR{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                INSERT INTO patients (mr_number, first_name, last_name, date_of_birth, gender, blood_group, 
                                    phone, alternate_phone, email, address, city, state, pincode,
                                    emergency_contact_name, emergency_contact_phone, emergency_contact_relation,
                                    marital_status, occupation, insurance_provider, insurance_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                mr_number,
                request.form['first_name'],
                request.form['last_name'],
                request.form['date_of_birth'],
                request.form['gender'],
                request.form.get('blood_group'),
                request.form['phone'],
                request.form.get('alternate_phone'),
                request.form.get('email'),
                request.form['address'],
                request.form.get('city'),
                request.form.get('state'),
                request.form.get('pincode'),
                request.form.get('emergency_contact_name'),
                request.form.get('emergency_contact_phone'),
                request.form.get('emergency_contact_relation'),
                request.form.get('marital_status'),
                request.form.get('occupation'),
                request.form.get('insurance_provider'),
                request.form.get('insurance_number')
            ))
            
            db.commit()
            patient_id = cursor.lastrowid
            db.close()
            
            flash(f'Patient added successfully! MR Number: {mr_number}', 'success')
            return redirect(url_for('patient_detail', patient_id=patient_id))
        
        @self.app.route('/edit_patient/<int:patient_id>', methods=['POST'])
        def edit_patient(patient_id):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                UPDATE patients SET 
                    first_name = %s, last_name = %s, date_of_birth = %s, gender = %s,
                    blood_group = %s, phone = %s, alternate_phone = %s, email = %s,
                    address = %s, city = %s, state = %s, pincode = %s,
                    emergency_contact_name = %s, emergency_contact_phone = %s, emergency_contact_relation = %s,
                    marital_status = %s, occupation = %s, insurance_provider = %s, insurance_number = %s
                WHERE patient_id = %s
            """, (
                request.form['first_name'],
                request.form['last_name'],
                request.form['date_of_birth'],
                request.form['gender'],
                request.form.get('blood_group'),
                request.form['phone'],
                request.form.get('alternate_phone'),
                request.form.get('email'),
                request.form['address'],
                request.form.get('city'),
                request.form.get('state'),
                request.form.get('pincode'),
                request.form.get('emergency_contact_name'),
                request.form.get('emergency_contact_phone'),
                request.form.get('emergency_contact_relation'),
                request.form.get('marital_status'),
                request.form.get('occupation'),
                request.form.get('insurance_provider'),
                request.form.get('insurance_number'),
                patient_id
            ))
            
            db.commit()
            db.close()
            
            flash('Patient information updated successfully!', 'success')
            return redirect(url_for('patient_detail', patient_id=patient_id))
        
        @self.app.route('/delete_patient/<int:patient_id>')
        def delete_patient(patient_id):
            if 'user_id' not in session or session.get('role') != 'admin':
                flash('You do not have permission to delete patients!', 'danger')
                return redirect(url_for('patients'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Check if patient has appointments
            cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE patient_id = %s", (patient_id,))
            count = cursor.fetchone()['count']
            
            if count > 0:
                flash('Cannot delete patient with existing appointments!', 'danger')
            else:
                cursor.execute("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
                db.commit()
                flash('Patient deleted successfully!', 'success')
            
            db.close()
            return redirect(url_for('patients'))
        
        @self.app.route('/api/patients/search')
        def api_search_patients():
            query = request.args.get('q', '')
            if len(query) < 2:
                return jsonify([])
            
            db = self.get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT patient_id, mr_number, first_name, last_name, phone
                FROM patients
                WHERE first_name LIKE %s OR last_name LIKE %s OR mr_number LIKE %s OR phone LIKE %s
                LIMIT 10
            """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            
            patients = cursor.fetchall()
            db.close()

            return jsonify(patients)

        @self.app.route('/api/patient/<int:patient_id>')
        def api_get_patient(patient_id):
            """Get single patient data for editing"""
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            db = self.get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT patient_id, mr_number, first_name, last_name, date_of_birth,
                       gender, blood_group, phone, alternate_phone, email, address,
                       city, state, pincode, emergency_contact_name, emergency_contact_phone,
                       emergency_contact_relation, marital_status, occupation,
                       insurance_provider, insurance_number
                FROM patients
                WHERE patient_id = %s
            """, (patient_id,))

            patient = cursor.fetchone()
            db.close()

            if not patient:
                return jsonify({'error': 'Patient not found'}), 404

            # Convert date to string format for JSON
            patient_dict = dict(patient)
            if patient_dict.get('date_of_birth'):
                patient_dict['date_of_birth'] = str(patient_dict['date_of_birth'])

            return jsonify(patient_dict)