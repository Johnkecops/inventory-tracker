-- Drug Tracking System - database schema
--
-- RECONSTRUCTED from the queries streamlit_app.py issues, not recovered from an
-- authoritative dump. Every object here exists because the application reads or
-- calls it; column types and constraint choices are inferred from usage and the
-- Streamlit widgets that feed them. Diff this against a live DrugTrackingSystem
-- instance before treating it as canonical.
--
-- Objects the application requires:
--   tables      Patients, Drugs, Purchases
--   view        vw_purchase_history        (streamlit_app.py:56)
--   procedures  AddDrug, RecordPurchase    (streamlit_app.py:142, :211)
--   trigger     signals surfaced as pymysql.MySQLError args[1] (streamlit_app.py:215-217)

CREATE DATABASE IF NOT EXISTS DrugTrackingSystem
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE DrugTrackingSystem;

-- ---------------------------------------------------------------- tables -----

-- name/age/symptoms are the three form inputs at streamlit_app.py:77-80.
-- created_at must exist: the patient list orders by it (streamlit_app.py:107).
CREATE TABLE IF NOT EXISTS Patients (
    patient_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,          -- st.text_input max_chars=100
    age         INT UNSIGNED,                   -- st.number_input min_value=0
    symptoms    TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patients_name (name)
) ENGINE=InnoDB;

-- expiration_date is nullable: the availability filter at streamlit_app.py:180
-- explicitly admits NULL as "no expiry".
CREATE TABLE IF NOT EXISTS Drugs (
    drug_id          INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    price            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock_level      INT NOT NULL DEFAULT 0,
    expiration_date  DATE NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_drugs_stock_nonneg CHECK (stock_level >= 0),
    CONSTRAINT chk_drugs_price_nonneg CHECK (price >= 0),
    INDEX idx_drugs_name (name)
) ENGINE=InnoDB;

-- One row per dispensed unit. RecordPurchase takes exactly three arguments
-- (patient_id, drug_id, symptoms) at streamlit_app.py:211, so quantity is
-- fixed at one unit per purchase.
CREATE TABLE IF NOT EXISTS Purchases (
    purchase_id    INT AUTO_INCREMENT PRIMARY KEY,
    patient_id     INT NOT NULL,
    drug_id        INT NOT NULL,
    symptoms       TEXT,
    unit_price     DECIMAL(10,2) NOT NULL DEFAULT 0.00,  -- price at time of sale
    purchase_date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_purchases_patient FOREIGN KEY (patient_id)
        REFERENCES Patients (patient_id) ON DELETE RESTRICT,
    CONSTRAINT fk_purchases_drug FOREIGN KEY (drug_id)
        REFERENCES Drugs (drug_id) ON DELETE RESTRICT,
    INDEX idx_purchases_date (purchase_date)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------ view -----

-- The dashboard selects * from this view and formats a purchase_date column
-- (streamlit_app.py:56-62). Remaining columns are chosen to make that table
-- readable; adjust to match the live view.
CREATE OR REPLACE VIEW vw_purchase_history AS
SELECT
    pu.purchase_id,
    pa.name          AS patient_name,
    d.name           AS drug_name,
    pu.unit_price    AS price,
    pu.symptoms,
    pu.purchase_date
FROM Purchases pu
JOIN Patients pa ON pa.patient_id = pu.patient_id
JOIN Drugs    d  ON d.drug_id     = pu.drug_id;

-- ------------------------------------------------------------ procedures -----

DELIMITER //

-- Called with (name, price, stock_level, expiration_date) at streamlit_app.py:142.
CREATE PROCEDURE AddDrug (
    IN  p_name             VARCHAR(100),
    IN  p_price            DECIMAL(10,2),
    IN  p_stock_level      INT,
    IN  p_expiration_date  DATE
)
BEGIN
    IF p_name IS NULL OR p_name = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Drug name is required.';
    END IF;
    IF p_stock_level < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock level cannot be negative.';
    END IF;

    INSERT INTO Drugs (name, price, stock_level, expiration_date)
    VALUES (p_name, p_price, p_stock_level, p_expiration_date);
END //

-- Called with (patient_id, drug_id, symptoms) at streamlit_app.py:211. The app
-- comment says this proc handles stock reduction and the availability checks,
-- and surfaces failures as SIGNAL messages the app reads from args[1].
CREATE PROCEDURE RecordPurchase (
    IN  p_patient_id  INT,
    IN  p_drug_id     INT,
    IN  p_symptoms    TEXT
)
BEGIN
    DECLARE v_stock  INT;
    DECLARE v_expiry DATE;
    DECLARE v_price  DECIMAL(10,2);

    START TRANSACTION;

    SELECT stock_level, expiration_date, price
      INTO v_stock, v_expiry, v_price
      FROM Drugs
     WHERE drug_id = p_drug_id
       FOR UPDATE;

    IF v_stock IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Unknown drug.';
    END IF;
    IF v_stock <= 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Drug is out of stock.';
    END IF;
    IF v_expiry IS NOT NULL AND v_expiry < CURDATE() THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Drug is expired and cannot be dispensed.';
    END IF;

    INSERT INTO Purchases (patient_id, drug_id, symptoms, unit_price)
    VALUES (p_patient_id, p_drug_id, p_symptoms, v_price);

    UPDATE Drugs
       SET stock_level = stock_level - 1
     WHERE drug_id = p_drug_id;

    COMMIT;
END //

DELIMITER ;
