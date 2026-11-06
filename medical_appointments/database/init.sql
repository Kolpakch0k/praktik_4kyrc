CREATE DATABASE IF NOT EXISTS medical_appointments
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE medical_appointments;

CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    last_name VARCHAR(80) NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    middle_name VARCHAR(80) NOT NULL,
    birth_date DATE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255) NOT NULL,
    INDEX idx_patient_name (last_name, first_name),
    INDEX idx_patient_phone (phone)
);

CREATE TABLE IF NOT EXISTS specializations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500) NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    last_name VARCHAR(80) NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    middle_name VARCHAR(80) NOT NULL,
    specialization_id INT NOT NULL,
    office VARCHAR(20) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    INDEX idx_doctor_specialization (specialization_id),
    CONSTRAINT fk_doctor_specialization
        FOREIGN KEY (specialization_id)
        REFERENCES specializations(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('активна', 'отменена', 'состоялась') NOT NULL DEFAULT 'активна',
    active_slot_guard TINYINT GENERATED ALWAYS AS (
        CASE WHEN status = 'активна' THEN 1 ELSE NULL END
    ) STORED,
    comment VARCHAR(500) NOT NULL DEFAULT '',
    INDEX idx_appointment_schedule (
        doctor_id, appointment_date, appointment_time, status
    ),
    INDEX idx_appointment_patient (patient_id),
    UNIQUE KEY uq_doctor_active_slot (
        doctor_id, appointment_date, appointment_time, active_slot_guard
    ),
    CONSTRAINT fk_appointment_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_appointment_doctor
        FOREIGN KEY (doctor_id)
        REFERENCES doctors(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
