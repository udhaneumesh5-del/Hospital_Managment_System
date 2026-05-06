-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 27, 2026 at 11:29 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `hospital_management_db`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `GetPatientHistory` (IN `patientId` INT)   BEGIN
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
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `UpdateMedicineStock` (IN `medicineId` INT, IN `quantityChange` INT, IN `operationType` VARCHAR(10))   BEGIN
    IF operationType = 'ADD' THEN
        UPDATE medicines 
        SET current_stock = current_stock + quantityChange
        WHERE medicine_id = medicineId;
    ELSEIF operationType = 'REMOVE' THEN
        UPDATE medicines 
        SET current_stock = current_stock - quantityChange
        WHERE medicine_id = medicineId AND current_stock >= quantityChange;
    END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `admissions`
--

CREATE TABLE `admissions` (
  `admission_id` int(11) NOT NULL,
  `admission_number` varchar(20) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `room_id` int(11) DEFAULT NULL,
  `doctor_id` int(11) NOT NULL,
  `admission_date` datetime NOT NULL,
  `discharge_date` datetime DEFAULT NULL,
  `admission_type` enum('Emergency','Elective','Transfer') DEFAULT 'Elective',
  `diagnosis` text DEFAULT NULL,
  `treatment_plan` text DEFAULT NULL,
  `status` enum('Admitted','Discharged','Transferred','Expired') DEFAULT 'Admitted',
  `discharge_summary` text DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Triggers `admissions`
--
DELIMITER $$
CREATE TRIGGER `update_room_occupancy` AFTER INSERT ON `admissions` FOR EACH ROW BEGIN
    UPDATE rooms 
    SET current_occupancy = current_occupancy + 1,
        is_available = CASE WHEN current_occupancy + 1 >= capacity THEN FALSE ELSE TRUE END
    WHERE room_id = NEW.room_id;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `ambulances`
--

CREATE TABLE `ambulances` (
  `ambulance_id` int(11) NOT NULL,
  `vehicle_number` varchar(20) NOT NULL,
  `driver_name` varchar(100) DEFAULT NULL,
  `driver_phone` varchar(20) DEFAULT NULL,
  `ambulance_type` enum('Basic','Advanced','ICU') DEFAULT 'Basic',
  `equipment` text DEFAULT NULL,
  `is_available` tinyint(1) DEFAULT 1,
  `last_maintenance` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `appointment_id` int(11) NOT NULL,
  `appointment_number` varchar(20) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `appointment_date` date NOT NULL,
  `appointment_time` time NOT NULL,
  `end_time` time DEFAULT NULL,
  `appointment_type` enum('Consultation','Follow-up','Emergency','Surgery','Checkup') DEFAULT 'Consultation',
  `status` enum('Scheduled','Confirmed','In-Progress','Completed','Cancelled','No-Show','Rescheduled') DEFAULT 'Scheduled',
  `payment_status` enum('Pending','Paid','Partial','Insurance') DEFAULT 'Pending',
  `symptoms` text DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `prescription` text DEFAULT NULL,
  `is_emergency` tinyint(1) DEFAULT 0,
  `waiting_number` int(11) DEFAULT NULL,
  `cancellation_reason` text DEFAULT NULL,
  `reschedule_reason` text DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `appointments`
--

INSERT INTO `appointments` (`appointment_id`, `appointment_number`, `patient_id`, `doctor_id`, `appointment_date`, `appointment_time`, `end_time`, `appointment_type`, `status`, `payment_status`, `symptoms`, `notes`, `prescription`, `is_emergency`, `waiting_number`, `cancellation_reason`, `reschedule_reason`, `created_by`, `created_at`, `updated_at`) VALUES
(1, 'APT20241201001', 1, 1, '2026-04-20', '10:00:00', NULL, 'Consultation', 'Completed', 'Pending', NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, '2026-04-20 16:59:34', '2026-04-27 20:59:47'),
(2, 'APT20241201002', 2, 2, '2026-04-20', '11:30:00', NULL, 'Consultation', 'Completed', 'Pending', NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, '2026-04-20 16:59:34', '2026-04-27 20:59:55'),
(3, '', 2, 2, '2026-04-27', '02:41:44', NULL, '', 'Completed', 'Pending', 'Prescription Visit', NULL, NULL, 0, NULL, NULL, NULL, NULL, '2026-04-27 21:11:44', '2026-04-27 21:11:44');

-- --------------------------------------------------------

--
-- Stand-in structure for view `appointment_summary`
-- (See below for the actual view)
--
CREATE TABLE `appointment_summary` (
`appointment_id` int(11)
,`appointment_number` varchar(20)
,`patient_id` int(11)
,`doctor_id` int(11)
,`appointment_date` date
,`appointment_time` time
,`end_time` time
,`appointment_type` enum('Consultation','Follow-up','Emergency','Surgery','Checkup')
,`status` enum('Scheduled','Confirmed','In-Progress','Completed','Cancelled','No-Show','Rescheduled')
,`payment_status` enum('Pending','Paid','Partial','Insurance')
,`symptoms` text
,`notes` text
,`prescription` text
,`is_emergency` tinyint(1)
,`waiting_number` int(11)
,`cancellation_reason` text
,`reschedule_reason` text
,`created_by` int(11)
,`created_at` timestamp
,`updated_at` timestamp
,`patient_name` varchar(101)
,`doctor_name` varchar(105)
,`specialization` varchar(100)
);

-- --------------------------------------------------------

--
-- Table structure for table `billing`
--

CREATE TABLE `billing` (
  `bill_id` int(11) NOT NULL,
  `bill_number` varchar(20) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `appointment_id` int(11) DEFAULT NULL,
  `bill_date` date NOT NULL,
  `due_date` date DEFAULT NULL,
  `subtotal` decimal(10,2) NOT NULL DEFAULT 0.00,
  `tax_amount` decimal(10,2) DEFAULT 0.00,
  `discount_amount` decimal(10,2) DEFAULT 0.00,
  `discount_reason` varchar(255) DEFAULT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `amount_paid` decimal(10,2) DEFAULT 0.00,
  `balance_amount` decimal(10,2) DEFAULT 0.00,
  `payment_status` enum('Paid','Pending','Partial','Refunded','Written Off') DEFAULT 'Pending',
  `payment_method` enum('Cash','Credit Card','Debit Card','UPI','Net Banking','Insurance','Cheque') DEFAULT 'Cash',
  `payment_date` date DEFAULT NULL,
  `transaction_id` varchar(100) DEFAULT NULL,
  `insurance_claim_id` varchar(100) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `billing`
--

INSERT INTO `billing` (`bill_id`, `bill_number`, `patient_id`, `appointment_id`, `bill_date`, `due_date`, `subtotal`, `tax_amount`, `discount_amount`, `discount_reason`, `total_amount`, `amount_paid`, `balance_amount`, `payment_status`, `payment_method`, `payment_date`, `transaction_id`, `insurance_claim_id`, `notes`, `created_by`, `created_at`, `updated_at`) VALUES
(1, 'INV20241201001', 1, NULL, '2026-04-20', '2026-05-20', 500.00, 90.00, 0.00, NULL, 590.00, 0.00, 0.00, 'Pending', 'Cash', NULL, NULL, NULL, NULL, NULL, '2026-04-20 16:59:34', '2026-04-20 16:59:34');

--
-- Triggers `billing`
--
DELIMITER $$
CREATE TRIGGER `update_billing_balance` AFTER UPDATE ON `billing` FOR EACH ROW BEGIN
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
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `billing_items`
--

CREATE TABLE `billing_items` (
  `item_id` int(11) NOT NULL,
  `bill_id` int(11) NOT NULL,
  `item_type` enum('Consultation','Medicine','Lab Test','Room','Surgery','Other') NOT NULL,
  `item_name` varchar(200) NOT NULL,
  `item_code` varchar(50) DEFAULT NULL,
  `quantity` int(11) DEFAULT 1,
  `unit_price` decimal(10,2) NOT NULL,
  `discount_percent` decimal(5,2) DEFAULT 0.00,
  `discount_amount` decimal(10,2) DEFAULT 0.00,
  `total_price` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Stand-in structure for view `billing_summary`
-- (See below for the actual view)
--
CREATE TABLE `billing_summary` (
`bill_id` int(11)
,`bill_number` varchar(20)
,`patient_id` int(11)
,`appointment_id` int(11)
,`bill_date` date
,`due_date` date
,`subtotal` decimal(10,2)
,`tax_amount` decimal(10,2)
,`discount_amount` decimal(10,2)
,`discount_reason` varchar(255)
,`total_amount` decimal(10,2)
,`amount_paid` decimal(10,2)
,`balance_amount` decimal(10,2)
,`payment_status` enum('Paid','Pending','Partial','Refunded','Written Off')
,`payment_method` enum('Cash','Credit Card','Debit Card','UPI','Net Banking','Insurance','Cheque')
,`payment_date` date
,`transaction_id` varchar(100)
,`insurance_claim_id` varchar(100)
,`notes` text
,`created_by` int(11)
,`created_at` timestamp
,`updated_at` timestamp
,`patient_name` varchar(101)
,`mr_number` varchar(20)
);

-- --------------------------------------------------------

--
-- Table structure for table `departments`
--

CREATE TABLE `departments` (
  `dept_id` int(11) NOT NULL,
  `dept_code` varchar(20) NOT NULL,
  `dept_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `extension` varchar(10) DEFAULT NULL,
  `head_doctor_id` int(11) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `departments`
--

INSERT INTO `departments` (`dept_id`, `dept_code`, `dept_name`, `description`, `location`, `phone`, `extension`, `head_doctor_id`, `is_active`, `created_at`) VALUES
(1, 'CARD', 'Cardiology', 'Heart care and cardiac surgery', '3rd Floor, Tower A', '1234567890', NULL, 1, 1, '2026-04-20 16:59:34'),
(2, 'NEURO', 'Neurology', 'Brain and nervous system disorders', '4th Floor, Tower A', '1234567891', NULL, 2, 1, '2026-04-20 16:59:34'),
(3, 'PED', 'Pediatrics', 'Child healthcare', '2nd Floor, Tower B', '1234567892', NULL, NULL, 1, '2026-04-20 16:59:34'),
(4, 'ORTHO', 'Orthopedics', 'Bone and joint care', '1st Floor, Tower B', '1234567893', NULL, NULL, 1, '2026-04-20 16:59:34'),
(5, 'GYN', 'Gynecology', 'Women\'s health', '2nd Floor, Tower A', '1234567894', NULL, NULL, 1, '2026-04-20 16:59:34'),
(6, 'DERMA', 'Dermatology', 'Skin care', '1st Floor, Tower C', '1234567895', NULL, NULL, 1, '2026-04-20 16:59:34'),
(7, 'OPHTH', 'Ophthalmology', 'Eye care', '3rd Floor, Tower C', '1234567896', NULL, NULL, 1, '2026-04-20 16:59:34'),
(8, 'ENT', 'ENT', 'Ear, Nose, Throat', '2nd Floor, Tower C', '1234567897', NULL, NULL, 1, '2026-04-20 16:59:34'),
(9, '', 'Cardiology', NULL, NULL, NULL, NULL, NULL, 1, '2026-04-26 10:21:40');

-- --------------------------------------------------------

--
-- Table structure for table `doctors`
--

CREATE TABLE `doctors` (
  `doctor_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `doctor_code` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `specialization` varchar(100) NOT NULL,
  `department_id` int(11) DEFAULT NULL,
  `sub_specialization` varchar(100) DEFAULT NULL,
  `qualification` varchar(200) NOT NULL,
  `experience_years` int(11) DEFAULT 0,
  `phone` varchar(20) NOT NULL,
  `email` varchar(100) NOT NULL,
  `consultation_fee` decimal(10,2) NOT NULL,
  `follow_up_fee` decimal(10,2) DEFAULT NULL,
  `available_days` varchar(100) DEFAULT NULL,
  `available_time_start` time DEFAULT NULL,
  `available_time_end` time DEFAULT NULL,
  `slot_duration` int(11) DEFAULT 15,
  `chamber_number` varchar(20) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `profile_image` varchar(255) DEFAULT NULL,
  `is_available` tinyint(1) DEFAULT 1,
  `rating` decimal(3,2) DEFAULT 0.00,
  `total_patients` int(11) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `doctors`
--

INSERT INTO `doctors` (`doctor_id`, `user_id`, `doctor_code`, `first_name`, `last_name`, `specialization`, `department_id`, `sub_specialization`, `qualification`, `experience_years`, `phone`, `email`, `consultation_fee`, `follow_up_fee`, `available_days`, `available_time_start`, `available_time_end`, `slot_duration`, `chamber_number`, `bio`, `profile_image`, `is_available`, `rating`, `total_patients`, `created_at`, `updated_at`) VALUES
(1, NULL, 'DOC001', 'Sarah', 'Smith', 'Cardiology', 1, NULL, 'MD, DM Cardiology', 12, '9876543210', 'smith@hospital.com', 1200.00, NULL, NULL, NULL, NULL, 15, NULL, NULL, NULL, 1, 0.00, 0, '2026-04-20 16:59:34', '2026-04-20 16:59:34'),
(2, NULL, 'DOC002', 'James', 'Johnson', 'Neurology', 2, NULL, 'MD, DM Neurology', 10, '9876543211', 'johnson@hospital.com', 1100.00, NULL, NULL, NULL, NULL, 15, NULL, NULL, NULL, 1, 0.00, 0, '2026-04-20 16:59:34', '2026-04-20 16:59:34'),
(3, NULL, 'DOC20260428012221', 'tushar', 'jamdhade', 'md', 9, NULL, 'mbbs', 12, '8258555885', '', 100.00, NULL, 'mon', '10:10:00', '22:10:00', 15, NULL, 'okk', NULL, 1, 0.00, 0, '2026-04-27 19:52:21', '2026-04-27 19:52:21');

-- --------------------------------------------------------

--
-- Table structure for table `insurance_claims`
--

CREATE TABLE `insurance_claims` (
  `claim_id` int(11) NOT NULL,
  `claim_number` varchar(50) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `insurance_provider` varchar(100) DEFAULT NULL,
  `policy_number` varchar(100) DEFAULT NULL,
  `claim_amount` decimal(10,2) DEFAULT NULL,
  `approved_amount` decimal(10,2) DEFAULT NULL,
  `status` enum('Pending','Approved','Rejected','Processed') DEFAULT 'Pending',
  `claim_date` date DEFAULT NULL,
  `approval_date` date DEFAULT NULL,
  `remarks` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `inventory`
--

CREATE TABLE `inventory` (
  `item_id` int(11) NOT NULL,
  `item_code` varchar(50) NOT NULL,
  `item_name` varchar(200) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `sub_category` varchar(100) DEFAULT NULL,
  `unit` varchar(20) DEFAULT NULL,
  `quantity` int(11) NOT NULL DEFAULT 0,
  `reorder_level` int(11) DEFAULT 10,
  `unit_price` decimal(10,2) DEFAULT NULL,
  `supplier` varchar(200) DEFAULT NULL,
  `batch_number` varchar(50) DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lab_orders`
--

CREATE TABLE `lab_orders` (
  `order_id` int(11) NOT NULL,
  `order_number` varchar(20) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `appointment_id` int(11) DEFAULT NULL,
  `order_date` date NOT NULL,
  `priority` enum('Routine','Urgent','Emergency') DEFAULT 'Routine',
  `status` enum('Pending','In-Progress','Completed','Cancelled','Reported') DEFAULT 'Pending',
  `clinical_notes` text DEFAULT NULL,
  `reported_by` int(11) DEFAULT NULL,
  `report_date` date DEFAULT NULL,
  `report_file` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lab_order_items`
--

CREATE TABLE `lab_order_items` (
  `order_item_id` int(11) NOT NULL,
  `order_id` int(11) NOT NULL,
  `test_id` int(11) NOT NULL,
  `result_text` text DEFAULT NULL,
  `result_value` varchar(100) DEFAULT NULL,
  `result_unit` varchar(50) DEFAULT NULL,
  `normal_range` varchar(200) DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  `is_abnormal` tinyint(1) DEFAULT 0,
  `status` enum('Pending','In-Progress','Completed') DEFAULT 'Pending',
  `completed_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lab_requests`
--

CREATE TABLE `lab_requests` (
  `request_id` int(11) NOT NULL,
  `request_number` varchar(50) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `test_id` int(11) NOT NULL,
  `appointment_id` int(11) DEFAULT NULL,
  `request_date` date NOT NULL,
  `priority` enum('Routine','Urgent','Emergency') DEFAULT 'Routine',
  `clinical_notes` text DEFAULT NULL,
  `status` enum('Pending','In Progress','Completed','Cancelled') DEFAULT 'Pending',
  `completed_date` date DEFAULT NULL,
  `completed_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lab_tests`
--

CREATE TABLE `lab_tests` (
  `test_id` int(11) NOT NULL,
  `test_code` varchar(50) NOT NULL,
  `test_name` varchar(200) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `sub_category` varchar(100) DEFAULT NULL,
  `specimen_type` varchar(100) DEFAULT NULL,
  `normal_range` varchar(200) DEFAULT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `price` decimal(10,2) NOT NULL,
  `preparation_instructions` text DEFAULT NULL,
  `turnaround_time_hours` int(11) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lab_tests`
--

INSERT INTO `lab_tests` (`test_id`, `test_code`, `test_name`, `category`, `sub_category`, `specimen_type`, `normal_range`, `unit`, `price`, `preparation_instructions`, `turnaround_time_hours`, `is_active`, `created_at`) VALUES
(1, 'LAB001', 'Complete Blood Count', 'Hematology', NULL, 'Blood', '4.5-11.0 K/μL', NULL, 500.00, NULL, NULL, 1, '2026-04-20 16:59:34'),
(2, 'LAB002', 'Blood Glucose', 'Biochemistry', NULL, 'Blood', '70-100 mg/dL', NULL, 200.00, NULL, NULL, 1, '2026-04-20 16:59:34'),
(3, 'LAB003', 'Lipid Profile', 'Biochemistry', NULL, 'Blood', 'Total Chol: <200', NULL, 800.00, NULL, NULL, 1, '2026-04-20 16:59:34');

-- --------------------------------------------------------

--
-- Table structure for table `medical_records`
--

CREATE TABLE `medical_records` (
  `record_id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) DEFAULT NULL,
  `record_date` date NOT NULL,
  `record_type` enum('Visit','Diagnosis','Procedure','Surgery','Vaccination','Allergy','Chronic Condition') NOT NULL,
  `title` varchar(200) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `diagnosis` text DEFAULT NULL,
  `treatment` text DEFAULT NULL,
  `prescription_id` int(11) DEFAULT NULL,
  `attachment` varchar(255) DEFAULT NULL,
  `is_confidential` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `medicines`
--

CREATE TABLE `medicines` (
  `medicine_id` int(11) NOT NULL,
  `medicine_code` varchar(50) NOT NULL,
  `medicine_name` varchar(200) NOT NULL,
  `generic_name` varchar(200) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `manufacturer` varchar(200) DEFAULT NULL,
  `composition` text DEFAULT NULL,
  `strength` varchar(50) DEFAULT NULL,
  `dosage_form` enum('Tablet','Capsule','Syrup','Injection','Cream','Ointment','Drops','Inhaler') NOT NULL,
  `unit` varchar(20) DEFAULT 'piece',
  `purchase_price` decimal(10,2) NOT NULL,
  `selling_price` decimal(10,2) NOT NULL,
  `tax_rate` decimal(5,2) DEFAULT 0.00,
  `current_stock` int(11) NOT NULL DEFAULT 0,
  `minimum_stock` int(11) DEFAULT 10,
  `maximum_stock` int(11) DEFAULT 500,
  `reorder_level` int(11) DEFAULT 20,
  `expiry_date` date DEFAULT NULL,
  `batch_number` varchar(50) DEFAULT NULL,
  `requires_prescription` tinyint(1) DEFAULT 1,
  `storage_conditions` varchar(200) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `medicines`
--

INSERT INTO `medicines` (`medicine_id`, `medicine_code`, `medicine_name`, `generic_name`, `category`, `manufacturer`, `composition`, `strength`, `dosage_form`, `unit`, `purchase_price`, `selling_price`, `tax_rate`, `current_stock`, `minimum_stock`, `maximum_stock`, `reorder_level`, `expiry_date`, `batch_number`, `requires_prescription`, `storage_conditions`, `description`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'MED001', 'Paracetamol 500mg', 'Acetaminophen', 'Analgesic', 'Cipla', NULL, NULL, 'Tablet', 'piece', 2.50, 5.00, 0.00, 995, 50, 500, 20, '2025-12-31', NULL, 1, NULL, NULL, 1, '2026-04-20 16:59:34', '2026-04-27 21:13:32'),
(2, 'MED002', 'Amoxicillin 500mg', 'Amoxicillin', 'Antibiotic', 'GSK', NULL, NULL, 'Capsule', 'piece', 15.00, 25.00, 0.00, 500, 30, 500, 20, '2025-10-31', NULL, 1, NULL, NULL, 1, '2026-04-20 16:59:34', '2026-04-20 16:59:34'),
(3, 'MED003', 'Cetrizine 10mg', 'Cetrizine', 'Antihistamine', 'Sun Pharma', NULL, NULL, 'Tablet', 'piece', 3.00, 8.00, 0.00, 800, 40, 500, 20, '2025-11-30', NULL, 1, NULL, NULL, 1, '2026-04-20 16:59:34', '2026-04-20 16:59:34'),
(4, 'MED20260427220404', 'Para', 'PARA', 'Tablet', '1', NULL, NULL, '', 'piece', 0.00, 109.99, 0.00, 3, 10, 500, 20, '2026-04-30', '1', 1, NULL, 'Medicine de', 1, '2026-04-27 16:34:04', '2026-04-27 16:36:45');

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `patient_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `mr_number` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `date_of_birth` date NOT NULL,
  `gender` enum('Male','Female','Other') NOT NULL,
  `blood_group` enum('A+','A-','B+','B-','AB+','AB-','O+','O-') DEFAULT NULL,
  `phone` varchar(20) NOT NULL,
  `alternate_phone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `address` text NOT NULL,
  `city` varchar(50) DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `pincode` varchar(10) DEFAULT NULL,
  `emergency_contact_name` varchar(100) DEFAULT NULL,
  `emergency_contact_phone` varchar(20) DEFAULT NULL,
  `emergency_contact_relation` varchar(50) DEFAULT NULL,
  `marital_status` enum('Single','Married','Divorced','Widowed') DEFAULT NULL,
  `occupation` varchar(100) DEFAULT NULL,
  `insurance_provider` varchar(100) DEFAULT NULL,
  `insurance_number` varchar(50) DEFAULT NULL,
  `profile_image` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `status` varchar(20) DEFAULT 'Active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patients`
--

INSERT INTO `patients` (`patient_id`, `user_id`, `mr_number`, `first_name`, `last_name`, `date_of_birth`, `gender`, `blood_group`, `phone`, `alternate_phone`, `email`, `address`, `city`, `state`, `pincode`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `marital_status`, `occupation`, `insurance_provider`, `insurance_number`, `profile_image`, `is_active`, `created_at`, `updated_at`, `status`) VALUES
(1, NULL, 'MR10001', 'John', 'Doe', '1990-05-15', 'Male', 'O+', '9988776655', NULL, 'john@gmail.com', '123 Main St, City', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, '2026-04-20 16:59:34', '2026-04-20 16:59:34', 'Active'),
(2, NULL, 'MR10002', 'Jane', 'Doe', '1992-08-20', 'Female', 'A+', '9988776644', NULL, 'jane@gmail.com', '123 Main St, City', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, '2026-04-20 16:59:34', '2026-04-20 16:59:34', 'Active'),
(3, NULL, 'MR20260428020156', 'tushar', 'jamdhade', '2026-04-28', 'Male', 'A+', '8585858585', NULL, '', 'Dhamori Newasa Aahilyanagar', 'Newasa Aahilyanagar', 'Maharashtra', NULL, '7875515454541541', '', NULL, NULL, NULL, NULL, NULL, NULL, 1, '2026-04-27 20:31:56', '2026-04-27 20:31:56', 'Active');

-- --------------------------------------------------------

--
-- Stand-in structure for view `patient_details`
-- (See below for the actual view)
--
CREATE TABLE `patient_details` (
`patient_id` int(11)
,`user_id` int(11)
,`mr_number` varchar(20)
,`first_name` varchar(50)
,`last_name` varchar(50)
,`date_of_birth` date
,`gender` enum('Male','Female','Other')
,`blood_group` enum('A+','A-','B+','B-','AB+','AB-','O+','O-')
,`phone` varchar(20)
,`alternate_phone` varchar(20)
,`email` varchar(100)
,`address` text
,`city` varchar(50)
,`state` varchar(50)
,`pincode` varchar(10)
,`emergency_contact_name` varchar(100)
,`emergency_contact_phone` varchar(20)
,`emergency_contact_relation` varchar(50)
,`marital_status` enum('Single','Married','Divorced','Widowed')
,`occupation` varchar(100)
,`insurance_provider` varchar(100)
,`insurance_number` varchar(50)
,`profile_image` varchar(255)
,`is_active` tinyint(1)
,`created_at` timestamp
,`updated_at` timestamp
,`age` bigint(21)
,`full_name` varchar(101)
);

-- --------------------------------------------------------

--
-- Table structure for table `prescriptions`
--

CREATE TABLE `prescriptions` (
  `prescription_id` int(11) NOT NULL,
  `prescription_number` varchar(20) NOT NULL,
  `appointment_id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `prescription_date` date NOT NULL,
  `notes` text DEFAULT NULL,
  `valid_until` date DEFAULT NULL,
  `is_dispensed` tinyint(1) DEFAULT 0,
  `dispensed_date` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` varchar(20) DEFAULT 'Pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `prescriptions`
--

INSERT INTO `prescriptions` (`prescription_id`, `prescription_number`, `appointment_id`, `patient_id`, `doctor_id`, `prescription_date`, `notes`, `valid_until`, `is_dispensed`, `dispensed_date`, `created_at`, `status`) VALUES
(2, 'RX20260428024144', 3, 2, 2, '2026-04-27', 'okk', NULL, 0, NULL, '2026-04-27 21:11:44', 'Dispensed');

-- --------------------------------------------------------

--
-- Table structure for table `prescription_items`
--

CREATE TABLE `prescription_items` (
  `presc_item_id` int(11) NOT NULL,
  `prescription_id` int(11) NOT NULL,
  `medicine_id` int(11) NOT NULL,
  `dosage` varchar(100) NOT NULL,
  `frequency` varchar(100) NOT NULL,
  `duration` varchar(50) NOT NULL,
  `quantity` int(11) NOT NULL,
  `instructions` text DEFAULT NULL,
  `morning` tinyint(1) DEFAULT 0,
  `afternoon` tinyint(1) DEFAULT 0,
  `evening` tinyint(1) DEFAULT 0,
  `night` tinyint(1) DEFAULT 0,
  `before_meal` tinyint(1) DEFAULT 0,
  `after_meal` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `prescription_items`
--

INSERT INTO `prescription_items` (`presc_item_id`, `prescription_id`, `medicine_id`, `dosage`, `frequency`, `duration`, `quantity`, `instructions`, `morning`, `afternoon`, `evening`, `night`, `before_meal`, `after_meal`) VALUES
(1, 2, 1, '5', '5', '5', 5, '5', 0, 0, 0, 0, 0, 0);

-- --------------------------------------------------------

--
-- Table structure for table `rooms`
--

CREATE TABLE `rooms` (
  `room_id` int(11) NOT NULL,
  `room_number` varchar(10) NOT NULL,
  `room_type` enum('General Ward','Semi-Private','Private','Deluxe','ICU','ICCU','Emergency') NOT NULL,
  `floor` int(11) DEFAULT NULL,
  `capacity` int(11) DEFAULT 1,
  `current_occupancy` int(11) DEFAULT 0,
  `price_per_day` decimal(10,2) NOT NULL,
  `amenities` text DEFAULT NULL,
  `is_available` tinyint(1) DEFAULT 1,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `rooms`
--

INSERT INTO `rooms` (`room_id`, `room_number`, `room_type`, `floor`, `capacity`, `current_occupancy`, `price_per_day`, `amenities`, `is_available`, `is_active`, `created_at`) VALUES
(1, '101', 'General Ward', 1, 6, 0, 500.00, NULL, 1, 1, '2026-04-20 16:59:34'),
(2, '102', 'General Ward', 1, 4, 0, 600.00, NULL, 1, 1, '2026-04-20 16:59:34'),
(3, '201', 'Private', 2, 1, 0, 2500.00, NULL, 1, 1, '2026-04-20 16:59:34'),
(4, '202', 'Private', 2, 1, 0, 3000.00, NULL, 1, 1, '2026-04-20 16:59:34'),
(5, '301', 'ICU', 3, 1, 0, 8000.00, NULL, 1, 1, '2026-04-20 16:59:34');

-- --------------------------------------------------------

--
-- Table structure for table `staff`
--

CREATE TABLE `staff` (
  `staff_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `staff_code` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `designation` varchar(100) NOT NULL,
  `department` varchar(100) DEFAULT NULL,
  `qualification` varchar(200) DEFAULT NULL,
  `experience_years` int(11) DEFAULT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `joining_date` date DEFAULT NULL,
  `salary` decimal(10,2) DEFAULT NULL,
  `shift_timing` varchar(50) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `profile_image` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `stock_transactions`
--

CREATE TABLE `stock_transactions` (
  `transaction_id` int(11) NOT NULL,
  `medicine_id` int(11) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `transaction_type` varchar(50) DEFAULT NULL,
  `transaction_date` datetime DEFAULT current_timestamp(),
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stock_transactions`
--

INSERT INTO `stock_transactions` (`transaction_id`, `medicine_id`, `quantity`, `transaction_type`, `transaction_date`, `notes`) VALUES
(1, 1, -5, 'dispense', '2026-04-28 02:43:32', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','doctor','receptionist','pharmacist','lab_technician','patient') DEFAULT 'patient',
  `is_active` tinyint(1) DEFAULT 1,
  `last_login` datetime DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `email`, `password_hash`, `role`, `is_active`, `last_login`, `created_at`, `updated_at`) VALUES
(7, 'admin', 'admin@hospital.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', 1, '2026-04-28 01:59:47', '2026-04-20 17:17:15', '2026-04-27 20:29:47'),
(8, 'dr.smith', 'smith@hospital.com', 'f348d5628621f3d8f59c8cabda0f8eb0aa7e0514a90be7571020b1336f26c113', 'doctor', 1, '2026-04-28 01:49:02', '2026-04-20 17:17:15', '2026-04-27 20:19:02'),
(9, 'dr.johnson', 'johnson@hospital.com', 'f348d5628621f3d8f59c8cabda0f8eb0aa7e0514a90be7571020b1336f26c113', 'doctor', 1, NULL, '2026-04-20 17:17:15', '2026-04-20 17:17:15'),
(10, 'reception', 'reception@hospital.com', '5d37ed314cf2b5c8462b52b12cd512e2ac4a180e75598da4f12bfb0dea6d0a67', 'receptionist', 1, '2026-04-28 02:10:17', '2026-04-20 17:17:15', '2026-04-27 20:40:17'),
(11, 'pharmacy', 'pharmacy@hospital.com', 'ed5273f7ab1e24f89704b06074e12565a17da3d0457bd9a5271b43816f985d57', 'pharmacist', 1, '2026-04-28 02:11:11', '2026-04-20 17:17:15', '2026-04-27 20:41:11'),
(12, 'labtech', 'lab@hospital.com', '3705b578e8fcb1b82a94ad917881ec248bbd4111645e91aed3c19af12d82116f', 'lab_technician', 1, '2026-04-28 02:11:53', '2026-04-20 17:17:15', '2026-04-27 20:41:53');

-- --------------------------------------------------------

--
-- Structure for view `appointment_summary`
--
DROP TABLE IF EXISTS `appointment_summary`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `appointment_summary`  AS SELECT `a`.`appointment_id` AS `appointment_id`, `a`.`appointment_number` AS `appointment_number`, `a`.`patient_id` AS `patient_id`, `a`.`doctor_id` AS `doctor_id`, `a`.`appointment_date` AS `appointment_date`, `a`.`appointment_time` AS `appointment_time`, `a`.`end_time` AS `end_time`, `a`.`appointment_type` AS `appointment_type`, `a`.`status` AS `status`, `a`.`payment_status` AS `payment_status`, `a`.`symptoms` AS `symptoms`, `a`.`notes` AS `notes`, `a`.`prescription` AS `prescription`, `a`.`is_emergency` AS `is_emergency`, `a`.`waiting_number` AS `waiting_number`, `a`.`cancellation_reason` AS `cancellation_reason`, `a`.`reschedule_reason` AS `reschedule_reason`, `a`.`created_by` AS `created_by`, `a`.`created_at` AS `created_at`, `a`.`updated_at` AS `updated_at`, concat(`p`.`first_name`,' ',`p`.`last_name`) AS `patient_name`, concat('Dr. ',`d`.`first_name`,' ',`d`.`last_name`) AS `doctor_name`, `d`.`specialization` AS `specialization` FROM ((`appointments` `a` join `patients` `p` on(`a`.`patient_id` = `p`.`patient_id`)) join `doctors` `d` on(`a`.`doctor_id` = `d`.`doctor_id`)) ;

-- --------------------------------------------------------

--
-- Structure for view `billing_summary`
--
DROP TABLE IF EXISTS `billing_summary`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `billing_summary`  AS SELECT `b`.`bill_id` AS `bill_id`, `b`.`bill_number` AS `bill_number`, `b`.`patient_id` AS `patient_id`, `b`.`appointment_id` AS `appointment_id`, `b`.`bill_date` AS `bill_date`, `b`.`due_date` AS `due_date`, `b`.`subtotal` AS `subtotal`, `b`.`tax_amount` AS `tax_amount`, `b`.`discount_amount` AS `discount_amount`, `b`.`discount_reason` AS `discount_reason`, `b`.`total_amount` AS `total_amount`, `b`.`amount_paid` AS `amount_paid`, `b`.`balance_amount` AS `balance_amount`, `b`.`payment_status` AS `payment_status`, `b`.`payment_method` AS `payment_method`, `b`.`payment_date` AS `payment_date`, `b`.`transaction_id` AS `transaction_id`, `b`.`insurance_claim_id` AS `insurance_claim_id`, `b`.`notes` AS `notes`, `b`.`created_by` AS `created_by`, `b`.`created_at` AS `created_at`, `b`.`updated_at` AS `updated_at`, concat(`p`.`first_name`,' ',`p`.`last_name`) AS `patient_name`, `p`.`mr_number` AS `mr_number` FROM (`billing` `b` join `patients` `p` on(`b`.`patient_id` = `p`.`patient_id`)) ;

-- --------------------------------------------------------

--
-- Structure for view `patient_details`
--
DROP TABLE IF EXISTS `patient_details`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `patient_details`  AS SELECT `p`.`patient_id` AS `patient_id`, `p`.`user_id` AS `user_id`, `p`.`mr_number` AS `mr_number`, `p`.`first_name` AS `first_name`, `p`.`last_name` AS `last_name`, `p`.`date_of_birth` AS `date_of_birth`, `p`.`gender` AS `gender`, `p`.`blood_group` AS `blood_group`, `p`.`phone` AS `phone`, `p`.`alternate_phone` AS `alternate_phone`, `p`.`email` AS `email`, `p`.`address` AS `address`, `p`.`city` AS `city`, `p`.`state` AS `state`, `p`.`pincode` AS `pincode`, `p`.`emergency_contact_name` AS `emergency_contact_name`, `p`.`emergency_contact_phone` AS `emergency_contact_phone`, `p`.`emergency_contact_relation` AS `emergency_contact_relation`, `p`.`marital_status` AS `marital_status`, `p`.`occupation` AS `occupation`, `p`.`insurance_provider` AS `insurance_provider`, `p`.`insurance_number` AS `insurance_number`, `p`.`profile_image` AS `profile_image`, `p`.`is_active` AS `is_active`, `p`.`created_at` AS `created_at`, `p`.`updated_at` AS `updated_at`, timestampdiff(YEAR,`p`.`date_of_birth`,curdate()) AS `age`, concat(`p`.`first_name`,' ',`p`.`last_name`) AS `full_name` FROM `patients` AS `p` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admissions`
--
ALTER TABLE `admissions`
  ADD PRIMARY KEY (`admission_id`),
  ADD UNIQUE KEY `admission_number` (`admission_number`),
  ADD KEY `room_id` (`room_id`),
  ADD KEY `doctor_id` (`doctor_id`),
  ADD KEY `idx_admission_number` (`admission_number`),
  ADD KEY `idx_patient` (`patient_id`),
  ADD KEY `idx_status` (`status`);

--
-- Indexes for table `ambulances`
--
ALTER TABLE `ambulances`
  ADD PRIMARY KEY (`ambulance_id`),
  ADD UNIQUE KEY `vehicle_number` (`vehicle_number`),
  ADD KEY `idx_vehicle` (`vehicle_number`),
  ADD KEY `idx_availability` (`is_available`);

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`appointment_id`),
  ADD UNIQUE KEY `appointment_number` (`appointment_number`),
  ADD UNIQUE KEY `unique_appointment_slot` (`doctor_id`,`appointment_date`,`appointment_time`),
  ADD KEY `idx_appointment_date` (`appointment_date`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_patient` (`patient_id`),
  ADD KEY `idx_doctor` (`doctor_id`);

--
-- Indexes for table `billing`
--
ALTER TABLE `billing`
  ADD PRIMARY KEY (`bill_id`),
  ADD UNIQUE KEY `bill_number` (`bill_number`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `idx_bill_number` (`bill_number`),
  ADD KEY `idx_patient` (`patient_id`),
  ADD KEY `idx_status` (`payment_status`);

--
-- Indexes for table `billing_items`
--
ALTER TABLE `billing_items`
  ADD PRIMARY KEY (`item_id`),
  ADD KEY `idx_bill` (`bill_id`);

--
-- Indexes for table `departments`
--
ALTER TABLE `departments`
  ADD PRIMARY KEY (`dept_id`),
  ADD UNIQUE KEY `dept_code` (`dept_code`),
  ADD KEY `head_doctor_id` (`head_doctor_id`),
  ADD KEY `idx_dept_name` (`dept_name`);

--
-- Indexes for table `doctors`
--
ALTER TABLE `doctors`
  ADD PRIMARY KEY (`doctor_id`),
  ADD UNIQUE KEY `doctor_code` (`doctor_code`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_specialization` (`specialization`),
  ADD KEY `idx_doctor_code` (`doctor_code`),
  ADD KEY `department_id` (`department_id`);

--
-- Indexes for table `insurance_claims`
--
ALTER TABLE `insurance_claims`
  ADD PRIMARY KEY (`claim_id`),
  ADD UNIQUE KEY `claim_number` (`claim_number`),
  ADD KEY `idx_claim_number` (`claim_number`),
  ADD KEY `idx_patient` (`patient_id`);

--
-- Indexes for table `inventory`
--
ALTER TABLE `inventory`
  ADD PRIMARY KEY (`item_id`),
  ADD UNIQUE KEY `item_code` (`item_code`),
  ADD KEY `idx_item_name` (`item_name`),
  ADD KEY `idx_expiry` (`expiry_date`);

--
-- Indexes for table `lab_orders`
--
ALTER TABLE `lab_orders`
  ADD PRIMARY KEY (`order_id`),
  ADD UNIQUE KEY `order_number` (`order_number`),
  ADD KEY `doctor_id` (`doctor_id`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `idx_order_number` (`order_number`),
  ADD KEY `idx_patient` (`patient_id`),
  ADD KEY `idx_status` (`status`);

--
-- Indexes for table `lab_order_items`
--
ALTER TABLE `lab_order_items`
  ADD PRIMARY KEY (`order_item_id`),
  ADD KEY `test_id` (`test_id`),
  ADD KEY `idx_order` (`order_id`);

--
-- Indexes for table `lab_requests`
--
ALTER TABLE `lab_requests`
  ADD PRIMARY KEY (`request_id`),
  ADD UNIQUE KEY `request_number` (`request_number`),
  ADD KEY `test_id` (`test_id`),
  ADD KEY `idx_patient` (`patient_id`),
  ADD KEY `idx_doctor` (`doctor_id`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_request_date` (`request_date`);

--
-- Indexes for table `lab_tests`
--
ALTER TABLE `lab_tests`
  ADD PRIMARY KEY (`test_id`),
  ADD UNIQUE KEY `test_code` (`test_code`),
  ADD KEY `idx_test_name` (`test_name`),
  ADD KEY `idx_category` (`category`);

--
-- Indexes for table `medical_records`
--
ALTER TABLE `medical_records`
  ADD PRIMARY KEY (`record_id`),
  ADD KEY `doctor_id` (`doctor_id`),
  ADD KEY `prescription_id` (`prescription_id`),
  ADD KEY `idx_patient` (`patient_id`),
  ADD KEY `idx_record_date` (`record_date`);

--
-- Indexes for table `medicines`
--
ALTER TABLE `medicines`
  ADD PRIMARY KEY (`medicine_id`),
  ADD UNIQUE KEY `medicine_code` (`medicine_code`),
  ADD KEY `idx_medicine_name` (`medicine_name`),
  ADD KEY `idx_category` (`category`),
  ADD KEY `idx_expiry` (`expiry_date`),
  ADD KEY `idx_stock` (`current_stock`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`patient_id`),
  ADD UNIQUE KEY `mr_number` (`mr_number`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_mr_number` (`mr_number`),
  ADD KEY `idx_phone` (`phone`),
  ADD KEY `idx_name` (`first_name`,`last_name`),
  ADD KEY `idx_dob` (`date_of_birth`);

--
-- Indexes for table `prescriptions`
--
ALTER TABLE `prescriptions`
  ADD PRIMARY KEY (`prescription_id`),
  ADD UNIQUE KEY `prescription_number` (`prescription_number`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `doctor_id` (`doctor_id`),
  ADD KEY `idx_prescription_number` (`prescription_number`),
  ADD KEY `idx_patient` (`patient_id`);

--
-- Indexes for table `prescription_items`
--
ALTER TABLE `prescription_items`
  ADD PRIMARY KEY (`presc_item_id`),
  ADD KEY `medicine_id` (`medicine_id`),
  ADD KEY `idx_prescription` (`prescription_id`);

--
-- Indexes for table `rooms`
--
ALTER TABLE `rooms`
  ADD PRIMARY KEY (`room_id`),
  ADD UNIQUE KEY `room_number` (`room_number`),
  ADD KEY `idx_room_number` (`room_number`),
  ADD KEY `idx_availability` (`is_available`);

--
-- Indexes for table `staff`
--
ALTER TABLE `staff`
  ADD PRIMARY KEY (`staff_id`),
  ADD UNIQUE KEY `staff_code` (`staff_code`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_staff_code` (`staff_code`);

--
-- Indexes for table `stock_transactions`
--
ALTER TABLE `stock_transactions`
  ADD PRIMARY KEY (`transaction_id`),
  ADD KEY `medicine_id` (`medicine_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_username` (`username`),
  ADD KEY `idx_email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admissions`
--
ALTER TABLE `admissions`
  MODIFY `admission_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `ambulances`
--
ALTER TABLE `ambulances`
  MODIFY `ambulance_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `appointment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `billing`
--
ALTER TABLE `billing`
  MODIFY `bill_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `billing_items`
--
ALTER TABLE `billing_items`
  MODIFY `item_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `departments`
--
ALTER TABLE `departments`
  MODIFY `dept_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `doctors`
--
ALTER TABLE `doctors`
  MODIFY `doctor_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `insurance_claims`
--
ALTER TABLE `insurance_claims`
  MODIFY `claim_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `inventory`
--
ALTER TABLE `inventory`
  MODIFY `item_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lab_orders`
--
ALTER TABLE `lab_orders`
  MODIFY `order_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lab_order_items`
--
ALTER TABLE `lab_order_items`
  MODIFY `order_item_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lab_requests`
--
ALTER TABLE `lab_requests`
  MODIFY `request_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lab_tests`
--
ALTER TABLE `lab_tests`
  MODIFY `test_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `medical_records`
--
ALTER TABLE `medical_records`
  MODIFY `record_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `medicines`
--
ALTER TABLE `medicines`
  MODIFY `medicine_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `patient_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `prescriptions`
--
ALTER TABLE `prescriptions`
  MODIFY `prescription_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `prescription_items`
--
ALTER TABLE `prescription_items`
  MODIFY `presc_item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `rooms`
--
ALTER TABLE `rooms`
  MODIFY `room_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `staff`
--
ALTER TABLE `staff`
  MODIFY `staff_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `stock_transactions`
--
ALTER TABLE `stock_transactions`
  MODIFY `transaction_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `admissions`
--
ALTER TABLE `admissions`
  ADD CONSTRAINT `admissions_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `admissions_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`),
  ADD CONSTRAINT `admissions_ibfk_3` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`);

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`) ON DELETE CASCADE;

--
-- Constraints for table `billing`
--
ALTER TABLE `billing`
  ADD CONSTRAINT `billing_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `billing_ibfk_2` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`) ON DELETE SET NULL;

--
-- Constraints for table `billing_items`
--
ALTER TABLE `billing_items`
  ADD CONSTRAINT `billing_items_ibfk_1` FOREIGN KEY (`bill_id`) REFERENCES `billing` (`bill_id`) ON DELETE CASCADE;

--
-- Constraints for table `departments`
--
ALTER TABLE `departments`
  ADD CONSTRAINT `departments_ibfk_1` FOREIGN KEY (`head_doctor_id`) REFERENCES `doctors` (`doctor_id`) ON DELETE SET NULL;

--
-- Constraints for table `doctors`
--
ALTER TABLE `doctors`
  ADD CONSTRAINT `doctors_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  ADD CONSTRAINT `doctors_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`dept_id`) ON DELETE SET NULL;

--
-- Constraints for table `insurance_claims`
--
ALTER TABLE `insurance_claims`
  ADD CONSTRAINT `insurance_claims_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`);

--
-- Constraints for table `lab_orders`
--
ALTER TABLE `lab_orders`
  ADD CONSTRAINT `lab_orders_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `lab_orders_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`),
  ADD CONSTRAINT `lab_orders_ibfk_3` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`);

--
-- Constraints for table `lab_order_items`
--
ALTER TABLE `lab_order_items`
  ADD CONSTRAINT `lab_order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `lab_orders` (`order_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `lab_order_items_ibfk_2` FOREIGN KEY (`test_id`) REFERENCES `lab_tests` (`test_id`);

--
-- Constraints for table `lab_requests`
--
ALTER TABLE `lab_requests`
  ADD CONSTRAINT `lab_requests_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `lab_requests_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `lab_requests_ibfk_3` FOREIGN KEY (`test_id`) REFERENCES `lab_tests` (`test_id`) ON DELETE CASCADE;

--
-- Constraints for table `medical_records`
--
ALTER TABLE `medical_records`
  ADD CONSTRAINT `medical_records_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `medical_records_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`),
  ADD CONSTRAINT `medical_records_ibfk_3` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`prescription_id`);

--
-- Constraints for table `patients`
--
ALTER TABLE `patients`
  ADD CONSTRAINT `patients_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `prescriptions`
--
ALTER TABLE `prescriptions`
  ADD CONSTRAINT `prescriptions_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `prescriptions_ibfk_2` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `prescriptions_ibfk_3` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`);

--
-- Constraints for table `prescription_items`
--
ALTER TABLE `prescription_items`
  ADD CONSTRAINT `prescription_items_ibfk_1` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`prescription_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `prescription_items_ibfk_2` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`);

--
-- Constraints for table `staff`
--
ALTER TABLE `staff`
  ADD CONSTRAINT `staff_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `stock_transactions`
--
ALTER TABLE `stock_transactions`
  ADD CONSTRAINT `stock_transactions_ibfk_1` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
