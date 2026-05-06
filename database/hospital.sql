-- =============================================
-- Hospital Management System Database Schema
-- =============================================

-- Create Database
CREATE DATABASE IF NOT EXISTS hospital_management_db;
USE hospital_management_db;

-- =============================================
-- 1. Users Table (Authentication)
-- =============================================
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'doctor', 'receptionist', 'pharmacist', 'lab_technician', 'patient') DEFAULT 'patient',
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- =============================================
-- 2. Patients Table (Fixed - Removed GENERATED column)
-- =============================================
CREATE TABLE patients (
    patient_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    mr_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'),
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT NOT NULL,
    city VARCHAR(50),
    state VARCHAR(50),
    pincode VARCHAR(10),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relation VARCHAR(50),
    marital_status ENUM('Single', 'Married', 'Divorced', 'Widowed'),
    occupation VARCHAR(100),
    insurance_provider VARCHAR(100),
    insurance_number VARCHAR(50),
    profile_image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_mr_number (mr_number),
    INDEX idx_phone (phone),
    INDEX idx_name (first_name, last_name),
    INDEX idx_dob (date_of_birth)
);

-- =============================================
-- 3. Doctors Table
-- =============================================
CREATE TABLE doctors (
    doctor_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    doctor_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    department_id INT,
    sub_specialization VARCHAR(100),
    qualification VARCHAR(200) NOT NULL,
    experience_years INT DEFAULT 0,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    consultation_fee DECIMAL(10,2) NOT NULL,
    follow_up_fee DECIMAL(10,2),
    available_days VARCHAR(100),
    available_time_start TIME,
    available_time_end TIME,
    slot_duration INT DEFAULT 15,
    chamber_number VARCHAR(20),
    bio TEXT,
    profile_image VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3,2) DEFAULT 0,
    total_patients INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_specialization (specialization),
    INDEX idx_doctor_code (doctor_code)
);

-- =============================================
-- 4. Departments Table
-- =============================================
CREATE TABLE departments (
    dept_id INT PRIMARY KEY AUTO_INCREMENT,
    dept_code VARCHAR(20) UNIQUE NOT NULL,
    dept_name VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(100),
    phone VARCHAR(20),
    extension VARCHAR(10),
    head_doctor_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (head_doctor_id) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    INDEX idx_dept_name (dept_name)
);

-- Add foreign key for department_id in doctors table
ALTER TABLE doctors ADD FOREIGN KEY (department_id) REFERENCES departments(dept_id) ON DELETE SET NULL;

-- =============================================
-- 5. Appointments Table
-- =============================================
CREATE TABLE appointments (
    appointment_id INT PRIMARY KEY AUTO_INCREMENT,
    appointment_number VARCHAR(20) UNIQUE NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    end_time TIME,
    appointment_type ENUM('Consultation', 'Follow-up', 'Emergency', 'Surgery', 'Checkup') DEFAULT 'Consultation',
    status ENUM('Scheduled', 'Confirmed', 'In-Progress', 'Completed', 'Cancelled', 'No-Show', 'Rescheduled') DEFAULT 'Scheduled',
    payment_status ENUM('Pending', 'Paid', 'Partial', 'Insurance') DEFAULT 'Pending',
    symptoms TEXT,
    notes TEXT,
    prescription TEXT,
    is_emergency BOOLEAN DEFAULT FALSE,
    waiting_number INT,
    cancellation_reason TEXT,
    reschedule_reason TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    INDEX idx_appointment_date (appointment_date),
    INDEX idx_status (status),
    INDEX idx_patient (patient_id),
    INDEX idx_doctor (doctor_id),
    UNIQUE KEY unique_appointment_slot (doctor_id, appointment_date, appointment_time)
);

-- =============================================
-- 6. Billing Table
-- =============================================
CREATE TABLE billing (
    bill_id INT PRIMARY KEY AUTO_INCREMENT,
    bill_number VARCHAR(20) UNIQUE NOT NULL,
    patient_id INT NOT NULL,
    appointment_id INT,
    bill_date DATE NOT NULL,
    due_date DATE,
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    discount_reason VARCHAR(255),
    total_amount DECIMAL(10,2) NOT NULL,
    amount_paid DECIMAL(10,2) DEFAULT 0,
    balance_amount DECIMAL(10,2) DEFAULT 0,
    payment_status ENUM('Paid', 'Pending', 'Partial', 'Refunded', 'Written Off') DEFAULT 'Pending',
    payment_method ENUM('Cash', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Insurance', 'Cheque') DEFAULT 'Cash',
    payment_date DATE,
    transaction_id VARCHAR(100),
    insurance_claim_id VARCHAR(100),
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    INDEX idx_bill_number (bill_number),
    INDEX idx_patient (patient_id),
    INDEX idx_status (payment_status)
);

-- =============================================
-- 7. Billing Items Table
-- =============================================
CREATE TABLE billing_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    bill_id INT NOT NULL,
    item_type ENUM('Consultation', 'Medicine', 'Lab Test', 'Room', 'Surgery', 'Other') NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    item_code VARCHAR(50),
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (bill_id) REFERENCES billing(bill_id) ON DELETE CASCADE,
    INDEX idx_bill (bill_id)
);

-- =============================================
-- 8. Pharmacy / Medicines Table
-- =============================================
CREATE TABLE medicines (
    medicine_id INT PRIMARY KEY AUTO_INCREMENT,
    medicine_code VARCHAR(50) UNIQUE NOT NULL,
    medicine_name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    category VARCHAR(100),
    manufacturer VARCHAR(200),
    composition TEXT,
    strength VARCHAR(50),
    dosage_form ENUM('Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream', 'Ointment', 'Drops', 'Inhaler') NOT NULL,
    unit VARCHAR(20) DEFAULT 'piece',
    purchase_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    current_stock INT NOT NULL DEFAULT 0,
    minimum_stock INT DEFAULT 10,
    maximum_stock INT DEFAULT 500,
    reorder_level INT DEFAULT 20,
    expiry_date DATE,
    batch_number VARCHAR(50),
    requires_prescription BOOLEAN DEFAULT TRUE,
    storage_conditions VARCHAR(200),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_medicine_name (medicine_name),
    INDEX idx_category (category),
    INDEX idx_expiry (expiry_date),
    INDEX idx_stock (current_stock)
);

-- =============================================
-- 9. Prescriptions Table
-- =============================================
CREATE TABLE prescriptions (
    prescription_id INT PRIMARY KEY AUTO_INCREMENT,
    prescription_number VARCHAR(20) UNIQUE NOT NULL,
    appointment_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    prescription_date DATE NOT NULL,
    notes TEXT,
    valid_until DATE,
    is_dispensed BOOLEAN DEFAULT FALSE,
    dispensed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    INDEX idx_prescription_number (prescription_number),
    INDEX idx_patient (patient_id)
);

-- =============================================
-- 10. Prescription Items Table
-- =============================================
CREATE TABLE prescription_items (
    presc_item_id INT PRIMARY KEY AUTO_INCREMENT,
    prescription_id INT NOT NULL,
    medicine_id INT NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    duration VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    instructions TEXT,
    morning BOOLEAN DEFAULT FALSE,
    afternoon BOOLEAN DEFAULT FALSE,
    evening BOOLEAN DEFAULT FALSE,
    night BOOLEAN DEFAULT FALSE,
    before_meal BOOLEAN DEFAULT FALSE,
    after_meal BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id),
    INDEX idx_prescription (prescription_id)
);

-- =============================================
-- 11. Lab Tests Master Table
-- =============================================
CREATE TABLE lab_tests (
    test_id INT PRIMARY KEY AUTO_INCREMENT,
    test_code VARCHAR(50) UNIQUE NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    specimen_type VARCHAR(100),
    normal_range VARCHAR(200),
    unit VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    preparation_instructions TEXT,
    turnaround_time_hours INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_test_name (test_name),
    INDEX idx_category (category)
);

-- =============================================
-- 12. Lab Orders Table
-- =============================================
CREATE TABLE lab_orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_id INT,
    order_date DATE NOT NULL,
    priority ENUM('Routine', 'Urgent', 'Emergency') DEFAULT 'Routine',
    status ENUM('Pending', 'In-Progress', 'Completed', 'Cancelled', 'Reported') DEFAULT 'Pending',
    clinical_notes TEXT,
    reported_by INT,
    report_date DATE,
    report_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
    INDEX idx_order_number (order_number),
    INDEX idx_patient (patient_id),
    INDEX idx_status (status)
);

-- =============================================
-- 13. Lab Order Items Table
-- =============================================
CREATE TABLE lab_order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    test_id INT NOT NULL,
    result_text TEXT,
    result_value VARCHAR(100),
    result_unit VARCHAR(50),
    normal_range VARCHAR(200),
    remarks TEXT,
    is_abnormal BOOLEAN DEFAULT FALSE,
    status ENUM('Pending', 'In-Progress', 'Completed') DEFAULT 'Pending',
    completed_at DATETIME,
    FOREIGN KEY (order_id) REFERENCES lab_orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES lab_tests(test_id),
    INDEX idx_order (order_id)
);

-- =============================================
-- 14. Rooms / Wards Table
-- =============================================
CREATE TABLE rooms (
    room_id INT PRIMARY KEY AUTO_INCREMENT,
    room_number VARCHAR(10) UNIQUE NOT NULL,
    room_type ENUM('General Ward', 'Semi-Private', 'Private', 'Deluxe', 'ICU', 'ICCU', 'Emergency') NOT NULL,
    floor INT,
    capacity INT DEFAULT 1,
    current_occupancy INT DEFAULT 0,
    price_per_day DECIMAL(10,2) NOT NULL,
    amenities TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_room_number (room_number),
    INDEX idx_availability (is_available)
);

-- =============================================
-- 15. Admissions Table
-- =============================================
CREATE TABLE admissions (
    admission_id INT PRIMARY KEY AUTO_INCREMENT,
    admission_number VARCHAR(20) UNIQUE NOT NULL,
    patient_id INT NOT NULL,
    room_id INT,
    doctor_id INT NOT NULL,
    admission_date DATETIME NOT NULL,
    discharge_date DATETIME,
    admission_type ENUM('Emergency', 'Elective', 'Transfer') DEFAULT 'Elective',
    diagnosis TEXT,
    treatment_plan TEXT,
    status ENUM('Admitted', 'Discharged', 'Transferred', 'Expired') DEFAULT 'Admitted',
    discharge_summary TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    INDEX idx_admission_number (admission_number),
    INDEX idx_patient (patient_id),
    INDEX idx_status (status)
);

-- =============================================
-- 16. Medical Records Table
-- =============================================
CREATE TABLE medical_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    doctor_id INT,
    record_date DATE NOT NULL,
    record_type ENUM('Visit', 'Diagnosis', 'Procedure', 'Surgery', 'Vaccination', 'Allergy', 'Chronic Condition') NOT NULL,
    title VARCHAR(200),
    description TEXT,
    diagnosis TEXT,
    treatment TEXT,
    prescription_id INT,
    attachment VARCHAR(255),
    is_confidential BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id),
    INDEX idx_patient (patient_id),
    INDEX idx_record_date (record_date)
);

-- =============================================
-- 17. Staff Table
-- =============================================
CREATE TABLE staff (
    staff_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    staff_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    qualification VARCHAR(200),
    experience_years INT,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    joining_date DATE,
    salary DECIMAL(10,2),
    shift_timing VARCHAR(50),
    address TEXT,
    profile_image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_staff_code (staff_code)
);

-- =============================================
-- 18. Inventory / Stock Management
-- =============================================
CREATE TABLE inventory (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    unit VARCHAR(20),
    quantity INT NOT NULL DEFAULT 0,
    reorder_level INT DEFAULT 10,
    unit_price DECIMAL(10,2),
    supplier VARCHAR(200),
    batch_number VARCHAR(50),
    expiry_date DATE,
    location VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_item_name (item_name),
    INDEX idx_expiry (expiry_date)
);

-- =============================================
-- 19. Ambulance Table
-- =============================================
CREATE TABLE ambulances (
    ambulance_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_number VARCHAR(20) UNIQUE NOT NULL,
    driver_name VARCHAR(100),
    driver_phone VARCHAR(20),
    ambulance_type ENUM('Basic', 'Advanced', 'ICU') DEFAULT 'Basic',
    equipment TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    last_maintenance DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_vehicle (vehicle_number),
    INDEX idx_availability (is_available)
);

-- =============================================
-- 20. Insurance Claims Table
-- =============================================
CREATE TABLE insurance_claims (
    claim_id INT PRIMARY KEY AUTO_INCREMENT,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    patient_id INT NOT NULL,
    insurance_provider VARCHAR(100),
    policy_number VARCHAR(100),
    claim_amount DECIMAL(10,2),
    approved_amount DECIMAL(10,2),
    status ENUM('Pending', 'Approved', 'Rejected', 'Processed') DEFAULT 'Pending',
    claim_date DATE,
    approval_date DATE,
    remarks TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    INDEX idx_claim_number (claim_number),
    INDEX idx_patient (patient_id)
);

-- =============================================
-- Insert Sample Data
-- =============================================

-- Insert Departments
INSERT INTO departments (dept_code, dept_name, description, location, phone) VALUES
('CARD', 'Cardiology', 'Heart care and cardiac surgery', '3rd Floor, Tower A', '1234567890'),
('NEURO', 'Neurology', 'Brain and nervous system disorders', '4th Floor, Tower A', '1234567891'),
('PED', 'Pediatrics', 'Child healthcare', '2nd Floor, Tower B', '1234567892'),
('ORTHO', 'Orthopedics', 'Bone and joint care', '1st Floor, Tower B', '1234567893'),
('GYN', 'Gynecology', 'Women\'s health', '2nd Floor, Tower A', '1234567894'),
('DERMA', 'Dermatology', 'Skin care', '1st Floor, Tower C', '1234567895'),
('OPHTH', 'Ophthalmology', 'Eye care', '3rd Floor, Tower C', '1234567896'),
('ENT', 'ENT', 'Ear, Nose, Throat', '2nd Floor, Tower C', '1234567897');

-- Insert Users (using simple password hashing for demo)
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@hospital.com', 'scrypt:32768:8:1$admin123', 'admin'),
('dr.smith', 'smith@hospital.com', 'scrypt:32768:8:1$doctor123', 'doctor'),
('dr.johnson', 'johnson@hospital.com', 'scrypt:32768:8:1$doctor123', 'doctor'),
('reception', 'reception@hospital.com', 'scrypt:32768:8:1$recep123', 'receptionist'),
('pharmacy', 'pharmacy@hospital.com', 'scrypt:32768:8:1$pharmacy123', 'pharmacist'),
('labtech', 'lab@hospital.com', 'scrypt:32768:8:1$lab123', 'lab_technician');

-- Insert Doctors (first, then update department head)
INSERT INTO doctors (user_id, doctor_code, first_name, last_name, specialization, qualification, experience_years, phone, email, consultation_fee) VALUES
(2, 'DOC001', 'Sarah', 'Smith', 'Cardiology', 'MD, DM Cardiology', 12, '9876543210', 'smith@hospital.com', 1200.00),
(3, 'DOC002', 'James', 'Johnson', 'Neurology', 'MD, DM Neurology', 10, '9876543211', 'johnson@hospital.com', 1100.00);

-- Update department heads after doctors are inserted
UPDATE departments SET head_doctor_id = 1 WHERE dept_code = 'CARD';
UPDATE departments SET head_doctor_id = 2 WHERE dept_code = 'NEURO';

-- Update doctors with department_id
UPDATE doctors SET department_id = 1 WHERE doctor_id = 1;
UPDATE doctors SET department_id = 2 WHERE doctor_id = 2;

-- Insert Patients
INSERT INTO patients (user_id, mr_number, first_name, last_name, date_of_birth, gender, blood_group, phone, email, address) VALUES
(NULL, 'MR10001', 'John', 'Doe', '1990-05-15', 'Male', 'O+', '9988776655', 'john@gmail.com', '123 Main St, City'),
(NULL, 'MR10002', 'Jane', 'Doe', '1992-08-20', 'Female', 'A+', '9988776644', 'jane@gmail.com', '123 Main St, City');

-- Insert Medicines
INSERT INTO medicines (medicine_code, medicine_name, generic_name, category, manufacturer, dosage_form, purchase_price, selling_price, current_stock, minimum_stock, expiry_date) VALUES
('MED001', 'Paracetamol 500mg', 'Acetaminophen', 'Analgesic', 'Cipla', 'Tablet', 2.50, 5.00, 1000, 50, '2025-12-31'),
('MED002', 'Amoxicillin 500mg', 'Amoxicillin', 'Antibiotic', 'GSK', 'Capsule', 15.00, 25.00, 500, 30, '2025-10-31'),
('MED003', 'Cetrizine 10mg', 'Cetrizine', 'Antihistamine', 'Sun Pharma', 'Tablet', 3.00, 8.00, 800, 40, '2025-11-30');

-- Insert Lab Tests
INSERT INTO lab_tests (test_code, test_name, category, specimen_type, normal_range, price) VALUES
('LAB001', 'Complete Blood Count', 'Hematology', 'Blood', '4.5-11.0 K/μL', 500.00),
('LAB002', 'Blood Glucose', 'Biochemistry', 'Blood', '70-100 mg/dL', 200.00),
('LAB003', 'Lipid Profile', 'Biochemistry', 'Blood', 'Total Chol: <200', 800.00);

-- Insert Rooms
INSERT INTO rooms (room_number, room_type, floor, capacity, price_per_day) VALUES
('101', 'General Ward', 1, 6, 500.00),
('102', 'General Ward', 1, 4, 600.00),
('201', 'Private', 2, 1, 2500.00),
('202', 'Private', 2, 1, 3000.00),
('301', 'ICU', 3, 1, 8000.00);

-- Insert Sample Appointments
INSERT INTO appointments (appointment_number, patient_id, doctor_id, appointment_date, appointment_time, status) VALUES
('APT20241201001', 1, 1, CURDATE(), '10:00:00', 'Scheduled'),
('APT20241201002', 2, 2, CURDATE(), '11:30:00', 'Scheduled');

-- Insert Sample Bills
INSERT INTO billing (bill_number, patient_id, bill_date, due_date, subtotal, tax_amount, total_amount, payment_status) VALUES
('INV20241201001', 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 500.00, 90.00, 590.00, 'Pending');

-- Create a view for patient age calculation (alternative to generated column)
CREATE VIEW patient_details AS
SELECT 
    p.*,
    TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) as age,
    CONCAT(p.first_name, ' ', p.last_name) as full_name
FROM patients p;

-- Create a view for appointment summary
CREATE VIEW appointment_summary AS
SELECT 
    a.*,
    CONCAT(p.first_name, ' ', p.last_name) as patient_name,
    CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
    d.specialization
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
JOIN doctors d ON a.doctor_id = d.doctor_id;

-- Create a view for billing summary
CREATE VIEW billing_summary AS
SELECT 
    b.*,
    CONCAT(p.first_name, ' ', p.last_name) as patient_name,
    p.mr_number
FROM billing b
JOIN patients p ON b.patient_id = p.patient_id;

-- Stored Procedure: Get patient appointment history
DELIMITER //
CREATE PROCEDURE GetPatientHistory(IN patientId INT)
BEGIN
    SELECT 
        a.appointment_date,
        a.appointment_time,
        CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
        a.status,
        a.symptoms,
        a.notes
    FROM appointments a
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE a.patient_id = patientId
    ORDER BY a.appointment_date DESC;
END //
DELIMITER ;

-- Stored Procedure: Update medicine stock
DELIMITER //
CREATE PROCEDURE UpdateMedicineStock(
    IN medicineId INT,
    IN quantityChange INT,
    IN operationType VARCHAR(10)
)
BEGIN
    IF operationType = 'ADD' THEN
        UPDATE medicines 
        SET current_stock = current_stock + quantityChange
        WHERE medicine_id = medicineId;
    ELSEIF operationType = 'REMOVE' THEN
        UPDATE medicines 
        SET current_stock = current_stock - quantityChange
        WHERE medicine_id = medicineId AND current_stock >= quantityChange;
    END IF;
END //
DELIMITER ;

-- Trigger: Update room occupancy when admission occurs
DELIMITER //
CREATE TRIGGER update_room_occupancy
AFTER INSERT ON admissions
FOR EACH ROW
BEGIN
    UPDATE rooms 
    SET current_occupancy = current_occupancy + 1,
        is_available = CASE WHEN current_occupancy + 1 >= capacity THEN FALSE ELSE TRUE END
    WHERE room_id = NEW.room_id;
END //
DELIMITER ;

-- Trigger: Update billing balance when payment is recorded
DELIMITER //
CREATE TRIGGER update_billing_balance
AFTER UPDATE ON billing
FOR EACH ROW
BEGIN
    IF NEW.amount_paid >= NEW.total_amount THEN
        UPDATE billing 
        SET payment_status = 'Paid', balance_amount = 0
        WHERE bill_id = NEW.bill_id;
    ELSEIF NEW.amount_paid > 0 THEN
        UPDATE billing 
        SET payment_status = 'Partial', 
            balance_amount = total_amount - amount_paid
        WHERE bill_id = NEW.bill_id;
    END IF;
END //
DELIMITER ;

-- Display success message
SELECT 'Database created successfully with all tables, views, procedures, and triggers!' as Status;