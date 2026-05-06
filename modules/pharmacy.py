from flask import request, render_template, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta

class PharmacyModule:
    def __init__(self, app, db_connection):
        self.app = app
        self.get_db = db_connection
        self.register_routes()
    
    def register_routes(self):
        
        @self.app.route('/pharmacy_dashboard')
        def pharmacy_dashboard():
            """Pharmacy main dashboard with statistics"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Stock statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_medicines,
                    COALESCE(SUM(current_stock), 0) as total_stock,
                    COALESCE(SUM(current_stock * selling_price), 0) as total_value,
                    COUNT(CASE WHEN current_stock <= reorder_level THEN 1 END) as low_stock_count,
                    COUNT(CASE WHEN current_stock <= 0 THEN 1 END) as out_of_stock
                FROM medicines
            """)
            stats = cursor.fetchone()
            if not stats:
                stats = {'total_medicines': 0, 'total_stock': 0, 'total_value': 0, 'low_stock_count': 0, 'out_of_stock': 0}
            
            # Low stock items for alert
            cursor.execute("""
                SELECT medicine_id, medicine_name, current_stock as quantity, 
                       reorder_level as min_stock, unit
                FROM medicines
                WHERE current_stock <= reorder_level AND current_stock > 0
                ORDER BY current_stock ASC
                LIMIT 10
            """)
            low_stock_items = cursor.fetchall()
            
            # Expiring medicines (next 30 days)
            cursor.execute("""
                SELECT medicine_id, medicine_name, expiry_date, current_stock, unit
                FROM medicines
                WHERE expiry_date IS NOT NULL 
                AND expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                ORDER BY expiry_date ASC
                LIMIT 10
            """)
            expiring_items = cursor.fetchall()
            
            # Recent prescriptions
            cursor.execute("""
                SELECT p.prescription_id, p.prescription_number, p.prescription_date,
                       CONCAT(pat.first_name, ' ', pat.last_name) as patient_name,
                       CONCAT(d.first_name, ' ', d.last_name) as doctor_name
                FROM prescriptions p
                JOIN patients pat ON p.patient_id = pat.patient_id
                JOIN doctors d ON p.doctor_id = d.doctor_id
                ORDER BY p.prescription_date DESC
                LIMIT 10
            """)
            recent_prescriptions = cursor.fetchall()
            
            db.close()
            
            return render_template('pharmacy/pharmacy_dashboard.html',
                                 total_medicines=stats['total_medicines'],
                                 total_stock=stats['total_stock'],
                                 total_value=stats['total_value'],
                                 low_stock=stats['low_stock_count'],
                                 out_of_stock=stats['out_of_stock'],
                                 low_stock_items=low_stock_items,
                                 expiring_items=expiring_items,
                                 recent_prescriptions=recent_prescriptions)
        
        @self.app.route('/pharmacy')
        def pharmacy():
            """Pharmacy inventory management page"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            # Get filter parameters
            search_query = request.args.get('search', '')
            current_category = request.args.get('category', '')
            stock_status = request.args.get('stock_status', '')
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            # Get today's date for expiry check
            today_date = datetime.now().strftime('%Y-%m-%d')
            
            db = self.get_db()
            cursor = db.cursor()
            
            # Build query
            query = """
                SELECT medicine_id, medicine_code, medicine_name, generic_name, 
                       category, selling_price as price, current_stock as quantity,
                       minimum_stock as min_stock, reorder_level, expiry_date,
                       unit, manufacturer
                FROM medicines
                WHERE 1=1
            """
            params = []
            
            if search_query:
                query += " AND (medicine_name LIKE %s OR generic_name LIKE %s OR medicine_code LIKE %s)"
                params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
            
            if current_category:
                query += " AND category = %s"
                params.append(current_category)
            
            if stock_status == 'low':
                query += " AND current_stock <= reorder_level AND current_stock > 0"
            elif stock_status == 'out':
                query += " AND current_stock <= 0"
            elif stock_status == 'sufficient':
                query += " AND current_stock > reorder_level"
            
            query += " ORDER BY medicine_name LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])
            
            cursor.execute(query, params)
            medicines = cursor.fetchall()
            
            # Get total count for pagination
            count_query = "SELECT COUNT(*) as total FROM medicines WHERE 1=1"
            count_params = []
            if search_query:
                count_query += " AND (medicine_name LIKE %s OR generic_name LIKE %s)"
                count_params.extend([f'%{search_query}%', f'%{search_query}%'])
            if current_category:
                count_query += " AND category = %s"
                count_params.append(current_category)
            if stock_status == 'low':
                count_query += " AND current_stock <= reorder_level AND current_stock > 0"
            elif stock_status == 'out':
                count_query += " AND current_stock <= 0"
            elif stock_status == 'sufficient':
                count_query += " AND current_stock > reorder_level"
            
            cursor.execute(count_query, count_params)
            result = cursor.fetchone()
            total_count = result['total'] if result else 0
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
            
            # Get categories for filter
            cursor.execute("SELECT DISTINCT category FROM medicines WHERE category IS NOT NULL AND category != ''")
            categories = cursor.fetchall()
            
            # Get summary statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_medicines,
                    COALESCE(SUM(current_stock), 0) as total_stock,
                    COALESCE(SUM(current_stock * selling_price), 0) as total_value,
                    COUNT(CASE WHEN current_stock <= reorder_level THEN 1 END) as low_stock_count
                FROM medicines
            """)
            summary = cursor.fetchone()
            if not summary:
                summary = {'total_medicines': 0, 'total_stock': 0, 'total_value': 0, 'low_stock_count': 0}
            
            db.close()
            
            return render_template('pharmacy/pharmacy.html',
                                 medicines=medicines,
                                 categories=categories,
                                 summary=summary,
                                 total_pages=total_pages,
                                 page=page,
                                 search_query=search_query,
                                 current_category=current_category,
                                 stock_status=stock_status,
                                 today_date=today_date)
        
        @self.app.route('/medicine/new', methods=['GET', 'POST'])
        def new_medicine():
            """Add new medicine"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            if request.method == 'POST':
                try:
                    medicine_code = f"MED{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    db = self.get_db()
                    cursor = db.cursor()
                    
                    cursor.execute("""
                        INSERT INTO medicines (
                            medicine_code, medicine_name, generic_name, category, 
                            manufacturer, composition, strength, dosage_form, unit,
                            purchase_price, selling_price, tax_rate, current_stock,
                            minimum_stock, reorder_level, expiry_date, batch_number,
                            requires_prescription, storage_conditions, description
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        medicine_code,
                        request.form.get('medicine_name'),
                        request.form.get('generic_name'),
                        request.form.get('category'),
                        request.form.get('manufacturer'),
                        request.form.get('composition'),
                        request.form.get('strength'),
                        request.form.get('dosage_form'),
                        request.form.get('unit', 'piece'),
                        float(request.form.get('purchase_price', 0)),
                        float(request.form.get('selling_price', 0)),
                        float(request.form.get('tax_rate', 0)),
                        int(request.form.get('current_stock', 0)),
                        int(request.form.get('minimum_stock', 10)),
                        int(request.form.get('reorder_level', 20)),
                        request.form.get('expiry_date'),
                        request.form.get('batch_number'),
                        1 if request.form.get('requires_prescription') else 0,
                        request.form.get('storage_conditions'),
                        request.form.get('description')
                    ))
                    
                    db.commit()
                    medicine_id = cursor.lastrowid
                    db.close()
                    
                    flash('Medicine added successfully!', 'success')
                    return redirect(url_for('medicine_detail', medicine_id=medicine_id))
                    
                except Exception as e:
                    flash(f'Error adding medicine: {str(e)}', 'error')
                    return redirect(url_for('new_medicine'))
            
            return render_template('pharmacy/new_medicine.html')
        
        @self.app.route('/medicine/<int:medicine_id>')
        def medicine_detail(medicine_id):
            """View medicine details"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("SELECT * FROM medicines WHERE medicine_id = %s", (medicine_id,))
            medicine = cursor.fetchone()
            
            # Get stock history
            cursor.execute("""
                SELECT * FROM stock_transactions 
                WHERE medicine_id = %s 
                ORDER BY transaction_date DESC 
                LIMIT 20
            """, (medicine_id,))
            stock_history = cursor.fetchall()
            
            db.close()
            
            if not medicine:
                flash('Medicine not found!', 'error')
                return redirect(url_for('pharmacy'))
            
            return render_template('pharmacy/medicine_detail.html',
                                 medicine=medicine,
                                 stock_history=stock_history)
        
        @self.app.route('/medicine/<int:medicine_id>/edit', methods=['GET', 'POST'])
        def edit_medicine(medicine_id):
            """Edit medicine details"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            if request.method == 'POST':
                try:
                    cursor.execute("""
                        UPDATE medicines SET
                            medicine_name = %s, generic_name = %s, category = %s,
                            manufacturer = %s, composition = %s, strength = %s,
                            dosage_form = %s, unit = %s, purchase_price = %s,
                            selling_price = %s, tax_rate = %s, minimum_stock = %s,
                            reorder_level = %s, expiry_date = %s, batch_number = %s,
                            requires_prescription = %s, storage_conditions = %s,
                            description = %s
                        WHERE medicine_id = %s
                    """, (
                        request.form.get('medicine_name'),
                        request.form.get('generic_name'),
                        request.form.get('category'),
                        request.form.get('manufacturer'),
                        request.form.get('composition'),
                        request.form.get('strength'),
                        request.form.get('dosage_form'),
                        request.form.get('unit'),
                        float(request.form.get('purchase_price', 0)),
                        float(request.form.get('selling_price', 0)),
                        float(request.form.get('tax_rate', 0)),
                        int(request.form.get('minimum_stock', 10)),
                        int(request.form.get('reorder_level', 20)),
                        request.form.get('expiry_date'),
                        request.form.get('batch_number'),
                        1 if request.form.get('requires_prescription') else 0,
                        request.form.get('storage_conditions'),
                        request.form.get('description'),
                        medicine_id
                    ))
                    
                    db.commit()
                    flash('Medicine updated successfully!', 'success')
                    return redirect(url_for('medicine_detail', medicine_id=medicine_id))
                    
                except Exception as e:
                    flash(f'Error updating medicine: {str(e)}', 'error')
            
            cursor.execute("SELECT * FROM medicines WHERE medicine_id = %s", (medicine_id,))
            medicine = cursor.fetchone()
            db.close()
            
            if not medicine:
                flash('Medicine not found!', 'error')
                return redirect(url_for('pharmacy'))
            
            return render_template('pharmacy/edit_medicine.html', medicine=medicine)
        
        @self.app.route('/medicine/<int:medicine_id>/delete', methods=['POST'])
        def delete_medicine(medicine_id):
            """Delete medicine (Admin only)"""
            if 'user_id' not in session or session.get('role') != 'admin':
                flash('Access denied!', 'error')
                return redirect(url_for('pharmacy'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                cursor.execute("DELETE FROM medicines WHERE medicine_id = %s", (medicine_id,))
                db.commit()
                flash('Medicine deleted successfully!', 'success')
            except Exception as e:
                flash(f'Error deleting medicine: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('pharmacy'))
        
        @self.app.route('/update_stock/<int:medicine_id>', methods=['POST'])
        def update_stock(medicine_id):
            """Update medicine stock from inventory page"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            quantity = int(request.form.get('quantity', 0))
            operation = request.form.get('operation', 'add')
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                # Get current stock
                cursor.execute("SELECT current_stock, medicine_name FROM medicines WHERE medicine_id = %s", (medicine_id,))
                current = cursor.fetchone()
                
                if not current:
                    flash('Medicine not found!', 'error')
                    return redirect(url_for('pharmacy'))
                
                if operation == 'add':
                    new_quantity = current['current_stock'] + quantity
                    cursor.execute("""
                        UPDATE medicines SET current_stock = %s WHERE medicine_id = %s
                    """, (new_quantity, medicine_id))
                    
                    # Record transaction
                    cursor.execute("""
                        INSERT INTO stock_transactions (medicine_id, quantity, transaction_type)
                        VALUES (%s, %s, 'purchase')
                    """, (medicine_id, quantity))
                    
                    flash(f'Added {quantity} units to {current["medicine_name"]}!', 'success')
                    
                else:  # remove
                    if quantity > current['current_stock']:
                        flash(f'Insufficient stock! Only {current["current_stock"]} units available.', 'error')
                        return redirect(url_for('pharmacy'))
                    
                    new_quantity = current['current_stock'] - quantity
                    cursor.execute("""
                        UPDATE medicines SET current_stock = %s WHERE medicine_id = %s
                    """, (new_quantity, medicine_id))
                    
                    # Record transaction
                    cursor.execute("""
                        INSERT INTO stock_transactions (medicine_id, quantity, transaction_type)
                        VALUES (%s, %s, 'removed')
                    """, (medicine_id, -quantity))
                    
                    flash(f'Removed {quantity} units from {current["medicine_name"]}!', 'success')
                
                db.commit()
                
            except Exception as e:
                db.rollback()
                flash(f'Error updating stock: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('pharmacy'))
        
        @self.app.route('/medicine/<int:medicine_id>/stock', methods=['POST'])
        def update_medicine_stock(medicine_id):
            """Update medicine stock from detail page"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            quantity = int(request.form.get('quantity', 0))
            transaction_type = request.form.get('transaction_type', 'add')
            db = self.get_db()
            cursor = db.cursor()

            try:
                # Get current stock
                cursor.execute("SELECT current_stock FROM medicines WHERE medicine_id = %s", (medicine_id,))
                current = cursor.fetchone()

                if not current:
                    flash('Medicine not found!', 'error')
                    return redirect(url_for('pharmacy'))

                if transaction_type == 'add':
                    new_quantity = current['current_stock'] + quantity
                else:
                    new_quantity = current['current_stock'] - quantity
                    if new_quantity < 0:
                        flash('Insufficient stock!', 'error')
                        return redirect(url_for('medicine_detail', medicine_id=medicine_id))

                # Update stock
                cursor.execute("""
                    UPDATE medicines SET current_stock = %s WHERE medicine_id = %s
                """, (new_quantity, medicine_id))

                # Record transaction
                cursor.execute("""
                    INSERT INTO stock_transactions (medicine_id, quantity, transaction_type)
                    VALUES (%s, %s, %s)
                """, (medicine_id, quantity if transaction_type == 'add' else -quantity,
                      transaction_type))
                
                db.commit()
                flash('Stock updated successfully!', 'success')
                
            except Exception as e:
                db.rollback()
                flash(f'Error updating stock: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('medicine_detail', medicine_id=medicine_id))
        
        @self.app.route('/prescriptions')
        def prescriptions():
            """View all prescriptions"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            # Get filter parameters
            search_query = request.args.get('search', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            db = self.get_db()
            cursor = db.cursor()
            
            # FIXED: Removed diagnosis, status, price columns
            query = """
                SELECT p.prescription_id, p.prescription_number, p.prescription_date,
                       CONCAT(pat.first_name, ' ', pat.last_name) as patient_name,
                       pat.mr_number,
                       CONCAT(d.first_name, ' ', d.last_name) as doctor_name,
                       (SELECT COUNT(*) FROM prescription_items WHERE prescription_id = p.prescription_id) as medicines_count
                FROM prescriptions p
                JOIN patients pat ON p.patient_id = pat.patient_id
                JOIN doctors d ON p.doctor_id = d.doctor_id
                WHERE 1=1
            """
            params = []
            
            if search_query:
                query += " AND (CONCAT(pat.first_name, ' ', pat.last_name) LIKE %s OR p.prescription_number LIKE %s)"
                params.extend([f'%{search_query}%', f'%{search_query}%'])
            
            if start_date:
                query += " AND p.prescription_date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND p.prescription_date <= %s"
                params.append(end_date)
            
            query += " ORDER BY p.prescription_date DESC LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])
            
            cursor.execute(query, params)
            prescriptions = cursor.fetchall()
            
            # Get total count for pagination
            count_query = "SELECT COUNT(*) as total FROM prescriptions p WHERE 1=1"
            count_params = []
            
            if search_query:
                count_query += " AND (CONCAT(pat.first_name, ' ', pat.last_name) LIKE %s OR p.prescription_number LIKE %s)"
                count_params.extend([f'%{search_query}%', f'%{search_query}%'])
            
            cursor.execute(count_query, count_params)
            result = cursor.fetchone()
            total_count = result['total'] if result else 0
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
            
            db.close()
            
            return render_template('doctors/prescriptions.html',
                         prescriptions=prescriptions,
                         total_pages=total_pages,
                         page=page,
                         search_query=search_query,
                         start_date=start_date,
                         end_date=end_date)
        
        @self.app.route('/prescription/new', methods=['GET', 'POST'])
        def new_prescription():
            """Create new prescription"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            if request.method == 'POST':
                try:
                    db = self.get_db()
                    cursor = db.cursor()
                    
                    # Generate prescription number
                    prescription_number = f"RX{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # Get appointment_id or auto-create one for walk-in prescriptions
                    appointment_id = request.form.get('appointment_id')
                    patient_id = request.form.get('patient_id')
                    doctor_id = request.form.get('doctor_id')
                    prescription_date = request.form.get('prescription_date')

                    if not appointment_id or appointment_id == '':
                        # Auto-create a walk-in appointment
                        cursor.execute("""
                            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time,
                                                     appointment_type, status, symptoms)
                            VALUES (%s, %s, %s, CURTIME(), 'Walk-in', 'Completed', 'Prescription Visit')
                        """, (patient_id, doctor_id, prescription_date))
                        appointment_id = cursor.lastrowid

                    cursor.execute("""
                        INSERT INTO prescriptions (prescription_number, patient_id, doctor_id, appointment_id, prescription_date, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        prescription_number,
                        patient_id,
                        doctor_id,
                        appointment_id,
                        prescription_date,
                        request.form.get('notes')
                    ))
                    
                    prescription_id = cursor.lastrowid
                    
                    # Add prescription items
                    medicine_ids = request.form.getlist('medicine_id[]')
                    quantities = request.form.getlist('quantity[]')
                    dosages = request.form.getlist('dosage[]')
                    frequencies = request.form.getlist('frequency[]')
                    durations = request.form.getlist('duration[]')
                    instructions_list = request.form.getlist('instructions[]')
                    
                    # FIXED: Removed price column
                    for i in range(len(medicine_ids)):
                        if medicine_ids[i] and quantities[i]:
                            cursor.execute("""
                                INSERT INTO prescription_items (prescription_id, medicine_id, quantity, 
                                                              dosage, frequency, duration, instructions)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                prescription_id, medicine_ids[i], int(quantities[i]),
                                dosages[i] if i < len(dosages) else '',
                                frequencies[i] if i < len(frequencies) else '',
                                durations[i] if i < len(durations) else '',
                                instructions_list[i] if i < len(instructions_list) else ''
                            ))
                    
                    db.commit()
                    db.close()
                    
                    flash('Prescription created successfully!', 'success')
                    return redirect(url_for('view_prescription', prescription_id=prescription_id))
                    
                except Exception as e:
                    db.rollback()
                    flash(f'Error creating prescription: {str(e)}', 'error')
                    return redirect(url_for('new_prescription'))
            
            # GET request - show form
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("SELECT patient_id, first_name, last_name, mr_number FROM patients WHERE is_active = 1")
            patients = cursor.fetchall()
            
            cursor.execute("SELECT doctor_id, first_name, last_name, specialization FROM doctors WHERE is_available = 1")
            doctors = cursor.fetchall()
            
            cursor.execute("SELECT medicine_id, medicine_name, current_stock FROM medicines WHERE current_stock > 0")
            medicines = cursor.fetchall()

            # Get recent appointments for linking
            cursor.execute("""
                SELECT a.appointment_id, a.appointment_date,
                       p.first_name as patient_first, p.last_name as patient_last
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.status IN ('Scheduled', 'Completed')
                AND a.appointment_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                ORDER BY a.appointment_date DESC
                LIMIT 50
            """)
            appointments = cursor.fetchall()

            db.close()

            return render_template('doctors/new_prescription.html',
                                 patients=patients,
                                 doctors=doctors,
                                 medicines=medicines,
                                 appointments=appointments)
        
        @self.app.route('/prescription/<int:prescription_id>')
        def view_prescription(prescription_id):
            """View prescription details"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            # FIXED: Removed diagnosis column
            cursor.execute("""
                SELECT p.prescription_id, p.prescription_number, p.prescription_date, p.notes,
                       CONCAT(pat.first_name, ' ', pat.last_name) as patient_name,
                       pat.mr_number, pat.phone, pat.email,
                       CONCAT(d.first_name, ' ', d.last_name) as doctor_name,
                       d.specialization
                FROM prescriptions p
                JOIN patients pat ON p.patient_id = pat.patient_id
                JOIN doctors d ON p.doctor_id = d.doctor_id
                WHERE p.prescription_id = %s
            """, (prescription_id,))
            prescription = cursor.fetchone()
            
            if not prescription:
                flash('Prescription not found!', 'error')
                return redirect(url_for('prescriptions'))
            
            # FIXED: Removed selling_price column
            cursor.execute("""
                SELECT pi.*, m.medicine_name, m.unit
                FROM prescription_items pi
                JOIN medicines m ON pi.medicine_id = m.medicine_id
                WHERE pi.prescription_id = %s
            """, (prescription_id,))
            items = cursor.fetchall()
            
            db.close()
            
            return render_template('pharmacy/view_prescription.html',
                                 prescription=prescription,
                                 items=items)
        
        @self.app.route('/prescription/<int:prescription_id>/dispense', methods=['POST'])
        def dispense_prescription(prescription_id):
            """Dispense prescription"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                # Get prescription items
                cursor.execute("""
                    SELECT pi.*, m.current_stock, m.medicine_name
                    FROM prescription_items pi
                    JOIN medicines m ON pi.medicine_id = m.medicine_id
                    WHERE pi.prescription_id = %s
                """, (prescription_id,))
                items = cursor.fetchall()
                
                # Check stock availability
                for item in items:
                    if item['quantity'] > item['current_stock']:
                        flash(f'Insufficient stock for {item["medicine_name"]}! Only {item["current_stock"]} available.', 'error')
                        return redirect(url_for('view_prescription', prescription_id=prescription_id))
                
                # Update stock
                for item in items:
                    cursor.execute("""
                        UPDATE medicines SET current_stock = current_stock - %s
                        WHERE medicine_id = %s
                    """, (item['quantity'], item['medicine_id']))
                    
                    # Record transaction
                    cursor.execute("""
                        INSERT INTO stock_transactions (medicine_id, quantity, transaction_type)
                        VALUES (%s, %s, 'dispense')
                    """, (item['medicine_id'], -item['quantity']))

                # Update prescription status to Dispensed
                cursor.execute("""
                    UPDATE prescriptions SET status = 'Dispensed' WHERE prescription_id = %s
                """, (prescription_id,))

                db.commit()
                flash('Prescription dispensed successfully!', 'success')
                
            except Exception as e:
                db.rollback()
                flash(f'Error dispensing prescription: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('view_prescription', prescription_id=prescription_id))
        
        @self.app.route('/prescription/<int:prescription_id>/delete', methods=['POST'])
        def delete_prescription(prescription_id):
            """Delete prescription"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            try:
                # First delete prescription items
                cursor.execute("DELETE FROM prescription_items WHERE prescription_id = %s", (prescription_id,))
                # Then delete prescription
                cursor.execute("DELETE FROM prescriptions WHERE prescription_id = %s", (prescription_id,))
                db.commit()
                flash('Prescription deleted successfully!', 'success')
            except Exception as e:
                db.rollback()
                flash(f'Error deleting prescription: {str(e)}', 'error')
            finally:
                db.close()
            
            return redirect(url_for('prescriptions'))
        
        @self.app.route('/prescription/<int:prescription_id>/print')
        def print_prescription(prescription_id):
            """Print prescription"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT p.*, 
                       CONCAT(pat.first_name, ' ', pat.last_name) as patient_name,
                       pat.mr_number, pat.phone, pat.email, pat.address,
                       CONCAT(d.first_name, ' ', d.last_name) as doctor_name,
                       d.specialization
                FROM prescriptions p
                JOIN patients pat ON p.patient_id = pat.patient_id
                JOIN doctors d ON p.doctor_id = d.doctor_id
                WHERE p.prescription_id = %s
            """, (prescription_id,))
            prescription = cursor.fetchone()
            
            cursor.execute("""
                SELECT pi.*, m.medicine_name, m.unit
                FROM prescription_items pi
                JOIN medicines m ON pi.medicine_id = m.medicine_id
                WHERE pi.prescription_id = %s
            """, (prescription_id,))
            items = cursor.fetchall()
            
            db.close()
            
            return render_template('pharmacy/print_prescription.html',
                                 prescription=prescription,
                                 items=items)
        
        # API endpoints for AJAX calls
        @self.app.route('/api/medicines/search')
        def api_search_medicines():
            """API endpoint to search medicines"""
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            
            query = request.args.get('q', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT medicine_id, medicine_name, selling_price, current_stock, unit
                FROM medicines
                WHERE (medicine_name LIKE %s OR generic_name LIKE %s)
                AND current_stock > 0
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))
            
            medicines = cursor.fetchall()
            db.close()
            
            return jsonify({'medicines': medicines})
        
        @self.app.route('/api/medicine/<int:medicine_id>/stock')
        def api_check_stock(medicine_id):
            """API endpoint to check medicine stock"""
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT medicine_name, current_stock, selling_price
                FROM medicines
                WHERE medicine_id = %s
            """, (medicine_id,))
            
            medicine = cursor.fetchone()
            db.close()
            
            return jsonify({'medicine': medicine})
    
    # Wrapper methods for app.py
    def list_medicines(self):
        pass
    
    def view_medicine(self, medicine_id):
        pass
    
    def create_medicine(self):
        pass
    
    def create_prescription(self, appointment_id):
        pass