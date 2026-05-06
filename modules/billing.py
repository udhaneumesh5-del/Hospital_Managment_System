from flask import request, render_template, redirect, url_for, flash, session, jsonify, make_response
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

class BillingModule:
    def __init__(self, app, db_connection):
        self.app = app
        self.get_db = db_connection
        self.register_routes()
    
    def register_routes(self):
        @self.app.route('/billing')
        def billing():
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            status_filter = request.args.get('status', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            
            db = self.get_db()
            cursor = db.cursor()
            
            query = """
                SELECT b.*, p.first_name, p.last_name, p.mr_number
                FROM billing b
                JOIN patients p ON b.patient_id = p.patient_id
                WHERE 1=1
            """
            params = []
            
            if status_filter:
                query += " AND b.payment_status = %s"
                params.append(status_filter)
            
            if date_from:
                query += " AND b.bill_date >= %s"
                params.append(date_from)
            
            if date_to:
                query += " AND b.bill_date <= %s"
                params.append(date_to)
            
            query += " ORDER BY b.bill_date DESC LIMIT 100"
            
            cursor.execute(query, params)
            bills = cursor.fetchall()
            
            # Get summary
            cursor.execute("""
                SELECT 
                    SUM(total_amount) as total_revenue,
                    SUM(amount_paid) as total_collected,
                    SUM(balance_amount) as total_outstanding
                FROM billing
                WHERE payment_status != 'Paid'
            """)
            summary = cursor.fetchone()
            
            db.close()
            
            return render_template('reception/billing.html', bills=bills, summary=summary,
                                 status_filter=status_filter, date_from=date_from, date_to=date_to)
        
        @self.app.route('/generate_bill', methods=['POST'])
        def generate_bill():
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            bill_number = f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"
            subtotal = float(request.form['subtotal'])
            tax_amount = subtotal * 0.18  # 18% GST
            discount_amount = float(request.form.get('discount', 0))
            total_amount = subtotal + tax_amount - discount_amount
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                INSERT INTO billing (bill_number, patient_id, appointment_id, bill_date, due_date,
                                    subtotal, tax_amount, discount_amount, discount_reason, total_amount,
                                    payment_method, created_by)
                VALUES (%s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY),
                        %s, %s, %s, %s, %s, %s, %s)
            """, (
                bill_number,
                request.form['patient_id'],
                request.form.get('appointment_id'),
                subtotal,
                tax_amount,
                discount_amount,
                request.form.get('discount_reason'),
                total_amount,
                request.form['payment_method'],
                session['user_id']
            ))
            
            bill_id = cursor.lastrowid
            
            # Add billing items
            items = request.form.getlist('item_name[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('unit_price[]')
            item_types = request.form.getlist('item_type[]')
            
            for i in range(len(items)):
                total_price = float(quantities[i]) * float(prices[i])
                cursor.execute("""
                    INSERT INTO billing_items (bill_id, item_type, item_name, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (bill_id, item_types[i], items[i], quantities[i], prices[i], total_price))
            
            db.commit()
            db.close()
            
            flash(f'Bill generated successfully! Bill Number: {bill_number}', 'success')
            return redirect(url_for('view_bill', bill_id=bill_id))
        
        @self.app.route('/bill/<int:bill_id>')
        def view_bill(bill_id):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT b.*, p.first_name, p.last_name, p.mr_number, p.address, p.phone
                FROM billing b
                JOIN patients p ON b.patient_id = p.patient_id
                WHERE b.bill_id = %s
            """, (bill_id,))
            bill = cursor.fetchone()
            
            if not bill:
                flash('Bill not found!', 'danger')
                return redirect(url_for('billing'))
            
            cursor.execute("""
                SELECT * FROM billing_items WHERE bill_id = %s
            """, (bill_id,))
            items = cursor.fetchall()
            
            db.close()
            
            return render_template('reception/view_bill.html', bill=bill, items=items)
        
        @self.app.route('/make_payment/<int:bill_id>', methods=['POST'])
        def make_payment(bill_id):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            amount_paid = float(request.form['amount'])
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("SELECT total_amount, amount_paid FROM billing WHERE bill_id = %s", (bill_id,))
            bill = cursor.fetchone()
            
            new_amount_paid = bill['amount_paid'] + amount_paid
            new_balance = bill['total_amount'] - new_amount_paid
            
            if new_balance <= 0:
                status = 'Paid'
            elif new_amount_paid > 0:
                status = 'Partial'
            else:
                status = 'Pending'
            
            cursor.execute("""
                UPDATE billing 
                SET amount_paid = %s, balance_amount = %s, payment_status = %s,
                    payment_date = %s, transaction_id = %s
                WHERE bill_id = %s
            """, (new_amount_paid, max(0, new_balance), status, datetime.now(), 
                 request.form.get('transaction_id'), bill_id))
            
            db.commit()
            db.close()
            
            flash('Payment recorded successfully!', 'success')
            return redirect(url_for('view_bill', bill_id=bill_id))
        
        @self.app.route('/print_bill/<int:bill_id>')
        def print_bill(bill_id):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT b.*, p.first_name, p.last_name, p.mr_number, p.address, p.phone, p.email
                FROM billing b
                JOIN patients p ON b.patient_id = p.patient_id
                WHERE b.bill_id = %s
            """, (bill_id,))
            bill = cursor.fetchone()
            
            cursor.execute("SELECT * FROM billing_items WHERE bill_id = %s", (bill_id,))
            items = cursor.fetchall()
            
            db.close()
            
            # Generate PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=30)
            
            content = []
            
            # Hospital Header
            content.append(Paragraph("CITY GENERAL HOSPITAL", title_style))
            content.append(Paragraph("123 Healthcare Avenue, Medical District, City - 400001", styles['Normal']))
            content.append(Paragraph("Phone: +91 1234567890 | Email: contact@cityhospital.com", styles['Normal']))
            content.append(Spacer(1, 20))
            
            # Bill Title
            content.append(Paragraph(f"TAX INVOICE", styles['Heading1']))
            content.append(Paragraph(f"Bill No: {bill['bill_number']}", styles['Normal']))
            content.append(Paragraph(f"Date: {bill['bill_date']}", styles['Normal']))
            content.append(Spacer(1, 20))
            
            # Patient Details
            patient_data = [
                ["Patient Name:", f"{bill['first_name']} {bill['last_name']}"],
                ["MR Number:", bill['mr_number']],
                ["Address:", bill['address']],
                ["Phone:", bill['phone']]
            ]
            patient_table = Table(patient_data, colWidths=[100, 350])
            patient_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            content.append(patient_table)
            content.append(Spacer(1, 20))
            
            # Items Table
            item_data = [['#', 'Description', 'Quantity', 'Unit Price', 'Total']]
            for i, item in enumerate(items, 1):
                item_data.append([
                    str(i), 
                    item['item_name'], 
                    str(item['quantity']), 
                    f"₹{item['unit_price']:.2f}", 
                    f"₹{item['total_price']:.2f}"
                ])
            
            item_table = Table(item_data, colWidths=[40, 250, 60, 80, 80])
            item_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            content.append(item_table)
            content.append(Spacer(1, 20))
            
            # Totals
            total_data = [
                ["Subtotal:", "", "", "", f"₹{bill['subtotal']:.2f}"],
                ["Tax (18% GST):", "", "", "", f"₹{bill['tax_amount']:.2f}"],
                ["Discount:", "", "", "", f"₹{bill['discount_amount']:.2f}"],
                ["Total Amount:", "", "", "", f"₹{bill['total_amount']:.2f}"],
                ["Amount Paid:", "", "", "", f"₹{bill['amount_paid']:.2f}"],
                ["Balance Due:", "", "", "", f"₹{bill['balance_amount']:.2f}"],
            ]
            total_table = Table(total_data, colWidths=[100, 100, 100, 100, 100])
            total_table.setStyle(TableStyle([
                ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (4, -1), (4, -1), colors.red),
            ]))
            content.append(total_table)
            content.append(Spacer(1, 30))
            
            # Footer
            content.append(Paragraph("Thank you for choosing City General Hospital!", styles['Normal']))
            content.append(Paragraph("This is a computer generated invoice.", styles['Normal']))
            
            doc.build(content)
            buffer.seek(0)
            
            return make_response(buffer.getvalue(), 200, {
                'Content-Type': 'application/pdf',
                'Content-Disposition': f'inline; filename=bill_{bill["bill_number"]}.pdf'
            })