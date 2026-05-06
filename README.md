# 🏥 City General Hospital - Advanced Hospital Management System

A comprehensive, enterprise-grade Hospital Management System built with Flask, MySQL, and modern web technologies.

## 📋 Project Overview

This is a complete Hospital Management System for a 400-mark academic project. It includes 17 database tables, 7 functional modules, and a responsive web interface.

## ✨ Features

### Core Modules
- **Patient Management** - Register, view, edit, and delete patient records with medical history
- **Doctor Management** - Manage doctor profiles, schedules, and consultations
- **Appointment Scheduling** - Book, reschedule, and track appointments with availability checking
- **Billing System** - Generate invoices, track payments, and print bills (PDF)
- **Pharmacy Management** - Medicine inventory with stock alerts and prescription dispensing
- **Lab Test Management** - Test catalog, order management, and result entry
- **User Authentication** - Role-based access control (Admin, Doctor, Receptionist, Pharmacist, Lab Tech)

### Advanced Features
- 📊 Interactive Dashboard with Charts (Chart.js)
- 📱 Responsive Design (Mobile-friendly)
- 🖨️ PDF Bill Generation (ReportLab)
- 🔍 Search and Pagination
- 📧 Email Validation and Phone Format Validation
- 💰 Tax Calculation (18% GST)
- 📈 Revenue Analytics
- 🏥 Room and Admission Management
- 💊 Prescription Management

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python Flask |
| Database | MySQL |
| Frontend | HTML5, CSS3, JavaScript |
| Charts | Chart.js |
| PDF Generation | ReportLab |
| Authentication | Session-based |

## 📁 Database Schema (17 Tables)

1. users - Authentication & roles
2. patients - Patient information
3. doctors - Doctor profiles
4. departments - Hospital departments
5. appointments - Appointment scheduling
6. billing - Financial records
7. billing_items - Line items for bills
8. medicines - Medicine catalog
9. prescriptions - Prescription records
10. prescription_items - Prescription details
11. lab_tests - Test catalog
12. lab_orders - Test orders
13. lab_order_items - Test results
14. rooms - Hospital rooms
15. admissions - Patient admissions
16. medical_records - Patient history
17. staff - Staff information

## 🚀 Installation Guide

### Prerequisites
- Python 3.8+
- MySQL Server 5.7+
- pip package manager

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/Hospital_Management_System.git
cd Hospital_Management_System
# Hospital_Managment_System

