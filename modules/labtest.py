from flask import request, render_template, redirect, url_for, flash, session, jsonify
from datetime import datetime

class LabTestModule:
    def __init__(self, app, db_connection):
        self.app = app
        self.get_db = db_connection
        self.register_routes()
    
    def register_routes(self):
        
        @self.app.route('/labtest')
        def labtest():
            """Main lab tests listing page"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            # Get filter parameters
            search_query = request.args.get('search', '')
            category = request.args.get('category', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            query = """
                SELECT lt.*, 
                       (SELECT COUNT(*) FROM lab_order_items WHERE test_id = lt.test_id) as total_orders
                FROM lab_tests lt
                WHERE lt.is_active = 1
            """
            params = []
            
            if search_query:
                query += " AND (lt.test_name LIKE %s OR lt.test_code LIKE %s)"
                params.extend([f'%{search_query}%', f'%{search_query}%'])
            
            if category:
                query += " AND lt.category = %s"
                params.append(category)
            
            query += " ORDER BY lt.test_name"
            
            cursor.execute(query, params)
            tests = cursor.fetchall()
            
            db.close()
            
            return render_template('labtech/labtests.html',
                                 tests=tests,
                                 search_query=search_query,
                                 category=category)
        
        @self.app.route('/labtest/new', methods=['GET', 'POST'])
        def new_labtest():
            """Add new lab test"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            if request.method == 'POST':
                try:
                    test_code = f"LAB{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    db = self.get_db()
                    cursor = db.cursor()
                    
                    cursor.execute("""
                        INSERT INTO lab_tests (test_code, test_name, category, sub_category, 
                                              specimen_type, normal_range, unit, price, 
                                              preparation_instructions, turnaround_time_hours,
                                              description, instructions, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        test_code,
                        request.form.get('test_name'),
                        request.form.get('category'),
                        request.form.get('sub_category'),
                        request.form.get('specimen_type'),
                        request.form.get('normal_range'),
                        request.form.get('unit'),
                        float(request.form.get('price', 0)),
                        request.form.get('preparation_instructions'),
                        request.form.get('turnaround_time_hours'),
                        request.form.get('description'),
                        request.form.get('instructions'),
                        1
                    ))
                    
                    db.commit()
                    test_id = cursor.lastrowid
                    db.close()
                    
                    flash(f'Lab test added successfully! Code: {test_code}', 'success')
                    return redirect(url_for('labtest_detail', test_id=test_id))
                    
                except Exception as e:
                    flash(f'Error adding lab test: {str(e)}', 'error')
                    return redirect(url_for('new_labtest'))
            
            return render_template('labtech/new_labtest.html')
        
        @self.app.route('/labtest/<int:test_id>')
        def labtest_detail(test_id):
            """View lab test details"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT * FROM lab_tests WHERE test_id = %s
            """, (test_id,))
            test = cursor.fetchone()
            
            db.close()
            
            if not test:
                flash('Lab test not found!', 'error')
                return redirect(url_for('labtest'))
            
            return render_template('labtech/labtest_detail.html', test=test)
        
        @self.app.route('/labtest/<int:test_id>/edit', methods=['GET', 'POST'])
        def edit_labtest(test_id):
            """Edit lab test"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            if request.method == 'POST':
                try:
                    cursor.execute("""
                        UPDATE lab_tests SET
                            test_name = %s, category = %s, sub_category = %s,
                            specimen_type = %s, normal_range = %s, unit = %s,
                            price = %s, preparation_instructions = %s,
                            turnaround_time_hours = %s, description = %s,
                            instructions = %s, is_active = %s
                        WHERE test_id = %s
                    """, (
                        request.form.get('test_name'),
                        request.form.get('category'),
                        request.form.get('sub_category'),
                        request.form.get('specimen_type'),
                        request.form.get('normal_range'),
                        request.form.get('unit'),
                        float(request.form.get('price', 0)),
                        request.form.get('preparation_instructions'),
                        request.form.get('turnaround_time_hours'),
                        request.form.get('description'),
                        request.form.get('instructions'),
                        1 if request.form.get('is_active') else 0,
                        test_id
                    ))
                    
                    db.commit()
                    flash('Lab test updated successfully!', 'success')
                    return redirect(url_for('labtest_detail', test_id=test_id))
                    
                except Exception as e:
                    flash(f'Error updating lab test: {str(e)}', 'error')
            
            cursor.execute("SELECT * FROM lab_tests WHERE test_id = %s", (test_id,))
            test = cursor.fetchone()
            db.close()
            
            if not test:
                flash('Lab test not found!', 'error')
                return redirect(url_for('labtest'))
            
            return render_template('labtech/edit_labtest.html', test=test)
        
        @self.app.route('/labtest/<int:test_id>/delete', methods=['POST'])
        def delete_labtest(test_id):
            """Delete lab test (Admin only)"""
            if 'user_id' not in session or session.get('role') != 'admin':
                flash('Access denied!', 'error')
                return redirect(url_for('labtest'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                # Soft delete - just deactivate
                cursor.execute("UPDATE lab_tests SET is_active = 0 WHERE test_id = %s", (test_id,))
                db.commit()
                flash('Lab test deleted successfully!', 'success')
            except Exception as e:
                db.rollback()
                flash(f'Error deleting lab test: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('labtest'))
        
        @self.app.route('/lab_requests')
        def lab_requests():
            """View lab test requests"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            status_filter = request.args.get('status', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            query = """
                SELECT lr.*, 
                       p.first_name as patient_first, p.last_name as patient_last, p.mr_number,
                       d.first_name as doctor_first, d.last_name as doctor_last,
                       lt.test_name, lt.test_code
                FROM lab_requests lr
                JOIN patients p ON lr.patient_id = p.patient_id
                JOIN doctors d ON lr.doctor_id = d.doctor_id
                JOIN lab_tests lt ON lr.test_id = lt.test_id
                WHERE 1=1
            """
            params = []
            
            if status_filter:
                query += " AND lr.status = %s"
                params.append(status_filter)
            
            query += " ORDER BY lr.request_date DESC LIMIT 100"
            
            cursor.execute(query, params)
            requests = cursor.fetchall()
            
            db.close()
            
            return render_template('labtech/lab_requests.html',
                                 requests=requests,
                                 status_filter=status_filter)
        
        @self.app.route('/lab_request/new', methods=['GET', 'POST'])
        def new_lab_request():
            """Create new lab test request"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            if request.method == 'POST':
                try:
                    request_number = f"REQ{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    cursor.execute("""
                        INSERT INTO lab_requests (request_number, patient_id, doctor_id, test_id,
                                                  appointment_id, priority, clinical_notes, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
                    """, (
                        request_number,
                        request.form.get('patient_id'),
                        request.form.get('doctor_id'),
                        request.form.get('test_id'),
                        request.form.get('appointment_id'),
                        request.form.get('priority', 'Routine'),
                        request.form.get('clinical_notes')
                    ))
                    
                    db.commit()
                    request_id = cursor.lastrowid
                    db.close()
                    
                    flash(f'Lab request created successfully! Number: {request_number}', 'success')
                    return redirect(url_for('view_lab_request', request_id=request_id))
                    
                except Exception as e:
                    db.rollback()
                    flash(f'Error creating lab request: {str(e)}', 'error')
                    return redirect(url_for('new_lab_request'))
            
            # GET request - show form
            cursor.execute("SELECT patient_id, first_name, last_name, mr_number FROM patients WHERE is_active = 1")
            patients = cursor.fetchall()
            
            cursor.execute("SELECT doctor_id, first_name, last_name, specialization FROM doctors WHERE is_available = 1")
            doctors = cursor.fetchall()
            
            cursor.execute("SELECT test_id, test_name, category, price FROM lab_tests WHERE is_active = 1")
            tests = cursor.fetchall()
            
            db.close()
            
            return render_template('labtech/new_lab_request.html',
                                 patients=patients,
                                 doctors=doctors,
                                 tests=tests)
        
        @self.app.route('/lab_request/<int:request_id>')
        def view_lab_request(request_id):
            """View lab request details"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT lr.*, 
                       p.first_name as patient_first, p.last_name as patient_last, 
                       p.mr_number, p.phone, p.email, p.date_of_birth,
                       d.first_name as doctor_first, d.last_name as doctor_last,
                       lt.test_name, lt.test_code, lt.category, lt.normal_range, lt.unit
                FROM lab_requests lr
                JOIN patients p ON lr.patient_id = p.patient_id
                JOIN doctors d ON lr.doctor_id = d.doctor_id
                JOIN lab_tests lt ON lr.test_id = lt.test_id
                WHERE lr.request_id = %s
            """, (request_id,))
            request = cursor.fetchone()
            
            # Get test results if completed
            if request and request['status'] == 'Completed':
                cursor.execute("""
                    SELECT * FROM lab_results WHERE request_id = %s
                """, (request_id,))
                result = cursor.fetchone()
            else:
                result = None
            
            db.close()
            
            if not request:
                flash('Lab request not found!', 'error')
                return redirect(url_for('lab_requests'))
            
            return render_template('labtech/view_lab_request.html',
                                 request=request,
                                 result=result)
        
        @self.app.route('/lab_request/<int:request_id>/process', methods=['GET', 'POST'])
        def process_lab_request(request_id):
            """Process lab test and enter results"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            if request.method == 'POST':
                try:
                    # Update lab request status
                    cursor.execute("""
                        UPDATE lab_requests 
                        SET status = 'Completed', 
                            completed_date = CURDATE(),
                            completed_by = %s
                        WHERE request_id = %s
                    """, (session.get('user_id'), request_id))
                    
                    # Insert test results
                    cursor.execute("""
                        INSERT INTO lab_results (request_id, result_value, result_text, 
                                                normal_range_flag, remarks, tested_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        request_id,
                        request.form.get('result_value'),
                        request.form.get('result_text'),
                        'Abnormal' if request.form.get('is_abnormal') else 'Normal',
                        request.form.get('remarks'),
                        session.get('user_id')
                    ))
                    
                    db.commit()
                    flash('Test results saved successfully!', 'success')
                    return redirect(url_for('view_lab_request', request_id=request_id))
                    
                except Exception as e:
                    db.rollback()
                    flash(f'Error saving results: {str(e)}', 'error')
                    return redirect(url_for('process_lab_request', request_id=request_id))
            
            # GET request - show processing form
            cursor.execute("""
                SELECT lr.*, 
                       p.first_name as patient_first, p.last_name as patient_last, p.mr_number,
                       lt.test_name, lt.normal_range, lt.unit, lt.preparation_instructions
                FROM lab_requests lr
                JOIN patients p ON lr.patient_id = p.patient_id
                JOIN lab_tests lt ON lr.test_id = lt.test_id
                WHERE lr.request_id = %s
            """, (request_id,))
            request = cursor.fetchone()
            db.close()
            
            if not request:
                flash('Lab request not found!', 'error')
                return redirect(url_for('lab_requests'))
            
            return render_template('labtech/process_lab_request.html', request=request)
        
        @self.app.route('/lab_request/<int:request_id>/cancel', methods=['POST'])
        def cancel_lab_request(request_id):
            """Cancel lab request"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                UPDATE lab_requests SET status = 'Cancelled' WHERE request_id = %s
            """, (request_id,))
            db.commit()
            db.close()
            
            flash('Lab request cancelled!', 'success')
            return redirect(url_for('lab_requests'))
        
        @self.app.route('/lab_request/<int:request_id>/print')
        def print_lab_report(request_id):
            """Print lab report"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT lr.*, 
                       p.first_name as patient_first, p.last_name as patient_last, 
                       p.mr_number, p.phone, p.email, p.date_of_birth, p.gender,
                       d.first_name as doctor_first, d.last_name as doctor_last,
                       lt.test_name, lt.test_code, lt.category, lt.normal_range, lt.unit,
                       lr_res.result_value, lr_res.result_text, lr_res.normal_range_flag, lr_res.remarks
                FROM lab_requests lr
                JOIN patients p ON lr.patient_id = p.patient_id
                JOIN doctors d ON lr.doctor_id = d.doctor_id
                JOIN lab_tests lt ON lr.test_id = lt.test_id
                LEFT JOIN lab_results lr_res ON lr.request_id = lr_res.request_id
                WHERE lr.request_id = %s
            """, (request_id,))
            report = cursor.fetchone()
            db.close()
            
            if not report:
                flash('Report not found!', 'error')
                return redirect(url_for('lab_requests'))
            
            return render_template('labtech/print_lab_report.html', report=report)
        
        @self.app.route('/lab_dashboard')
        def lab_dashboard():
            """Lab technician dashboard"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Statistics
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending_requests,
                    COUNT(CASE WHEN status = 'In Progress' THEN 1 END) as in_progress,
                    COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed_today
                FROM lab_requests
                WHERE request_date = CURDATE()
            """)
            today_stats = cursor.fetchone()
            
            # Pending requests
            cursor.execute("""
                SELECT lr.*, p.first_name, p.last_name, p.mr_number, lt.test_name
                FROM lab_requests lr
                JOIN patients p ON lr.patient_id = p.patient_id
                JOIN lab_tests lt ON lr.test_id = lt.test_id
                WHERE lr.status = 'Pending'
                ORDER BY lr.request_date
                LIMIT 20
            """)
            pending_requests = cursor.fetchall()
            
            # Recent completed
            cursor.execute("""
                SELECT lr.*, p.first_name, p.last_name, lt.test_name
                FROM lab_requests lr
                JOIN patients p ON lr.patient_id = p.patient_id
                JOIN lab_tests lt ON lr.test_id = lt.test_id
                WHERE lr.status = 'Completed'
                ORDER BY lr.completed_date DESC
                LIMIT 10
            """)
            recent_completed = cursor.fetchall()
            
            db.close()
            
            return render_template('labtech/lab_dashboard.html',
                                 today_stats=today_stats,
                                 pending_requests=pending_requests,
                                 recent_completed=recent_completed)
        
        # API Endpoints
        @self.app.route('/api/lab_tests/search')
        def api_search_lab_tests():
            """API endpoint for searching lab tests"""
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            
            query = request.args.get('q', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT test_id, test_name, category, price
                FROM lab_tests
                WHERE test_name LIKE %s AND is_active = 1
                LIMIT 10
            """, (f'%{query}%',))
            
            tests = cursor.fetchall()
            db.close()
            
            return jsonify({'tests': tests})
        
        @self.app.route('/api/lab_request/<int:request_id>/status')
        def api_update_request_status(request_id):
            """API to update request status"""
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            
            status = request.args.get('status', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                UPDATE lab_requests SET status = %s WHERE request_id = %s
            """, (status, request_id))
            db.commit()
            db.close()
            
            return jsonify({'success': True})
    
    # Wrapper methods for app.py
    def list_tests(self):
        pass
    
    def view_test(self, test_id):
        pass
    
    def create_test(self):
        pass
    
    def request_test(self, appointment_id):
        pass