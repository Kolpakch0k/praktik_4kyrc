-- Apply once to databases created with the previous init.sql.
-- Existing appointment data is preserved.
USE medical_appointments;

ALTER TABLE appointments
    DROP INDEX uq_doctor_active_slot,
    ADD COLUMN active_slot_guard TINYINT GENERATED ALWAYS AS (
        CASE WHEN status = 'активна' THEN 1 ELSE NULL END
    ) STORED AFTER status,
    ADD UNIQUE KEY uq_doctor_active_slot (
        doctor_id, appointment_date, appointment_time, active_slot_guard
    );
