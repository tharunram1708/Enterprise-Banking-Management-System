CREATE DATABASE IF NOT EXISTS enterprise_bank;
USE enterprise_bank;

-- Phase 1: Authentication and security tables
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'customer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret VARCHAR(120),
    failed_login_count INT NOT NULL DEFAULT 0,
    locked_until DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_users_email (email)
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    refresh_token_id VARCHAR(64) NOT NULL UNIQUE,
    ip_address VARCHAR(64),
    user_agent VARCHAR(255),
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS verification_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    email VARCHAR(255) NOT NULL,
    purpose VARCHAR(40) NOT NULL,
    code_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME,
    attempts INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX ix_verification_codes_email (email)
);

CREATE TABLE IF NOT EXISTS login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(64),
    user_agent VARCHAR(255),
    success BOOLEAN NOT NULL,
    reason VARCHAR(120),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX ix_login_history_email (email)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    actor_user_id INT,
    action VARCHAR(80) NOT NULL,
    resource_type VARCHAR(80) NOT NULL,
    resource_id VARCHAR(80),
    ip_address VARCHAR(64),
    details JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
);

-- Phase 2: Customer management
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    date_of_birth DATE NOT NULL,
    pan_number VARCHAR(20) UNIQUE,
    aadhaar_last_four VARCHAR(4),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    kyc_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_by_user_id INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    INDEX ix_customers_email (email)
);

CREATE TABLE IF NOT EXISTS addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    address_type VARCHAR(30) NOT NULL DEFAULT 'home',
    line1 VARCHAR(255) NOT NULL,
    line2 VARCHAR(255),
    city VARCHAR(80) NOT NULL,
    state VARCHAR(80) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(80) NOT NULL DEFAULT 'India',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS nominees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    relationship VARCHAR(60) NOT NULL,
    phone VARCHAR(20),
    share_percent DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    document_type VARCHAR(60) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Phase 3: Account management
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_number VARCHAR(24) NOT NULL UNIQUE,
    account_type VARCHAR(40) NOT NULL DEFAULT 'savings',
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    balance DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    interest_rate DECIMAL(5,2),
    maturity_date DATE,
    joint_holder_customer_id INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (joint_holder_customer_id) REFERENCES customers(id),
    INDEX ix_accounts_account_number (account_number)
);

-- Phase 4: Transactions
CREATE TABLE IF NOT EXISTS beneficiaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    name VARCHAR(120) NOT NULL,
    bank_name VARCHAR(120) NOT NULL,
    account_number VARCHAR(24) NOT NULL,
    ifsc_code VARCHAR(20) NOT NULL,
    nickname VARCHAR(80),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_no VARCHAR(40) NOT NULL UNIQUE,
    from_account_id INT,
    to_account_id INT,
    transaction_type VARCHAR(40) NOT NULL,
    channel VARCHAR(40) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'success',
    description VARCHAR(255),
    scheduled_for DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_account_id) REFERENCES accounts(id),
    FOREIGN KEY (to_account_id) REFERENCES accounts(id),
    INDEX ix_transactions_reference_no (reference_no)
);

-- Phase 5: Loan management
CREATE TABLE IF NOT EXISTS loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    loan_type VARCHAR(40) NOT NULL DEFAULT 'personal',
    amount DECIMAL(14,2) NOT NULL,
    annual_interest_rate DECIMAL(5,2) NOT NULL,
    tenure_months INT NOT NULL,
    emi_amount DECIMAL(14,2) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'applied',
    approved_by_user_id INT,
    closed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (approved_by_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS loan_repayment_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    installment_no INT NOT NULL,
    due_date DATE NOT NULL,
    principal_amount DECIMAL(14,2) NOT NULL,
    interest_amount DECIMAL(14,2) NOT NULL,
    total_amount DECIMAL(14,2) NOT NULL,
    paid_on DATE,
    FOREIGN KEY (loan_id) REFERENCES loans(id)
);

-- Phase 6: Card management
CREATE TABLE IF NOT EXISTS cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    customer_id INT NOT NULL,
    card_type VARCHAR(30) NOT NULL DEFAULT 'debit',
    last_four VARCHAR(4) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    pin_hash VARCHAR(255),
    daily_limit DECIMAL(14,2) NOT NULL DEFAULT 25000.00,
    monthly_limit DECIMAL(14,2) NOT NULL DEFAULT 250000.00,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Phase 7 and 8: Branch and employee management
CREATE TABLE IF NOT EXISTS branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    ifsc_code VARCHAR(20) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    city VARCHAR(80) NOT NULL,
    state VARCHAR(80) NOT NULL,
    manager_user_id INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    branch_id INT NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    designation VARCHAR(80) NOT NULL,
    salary DECIMAL(14,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    work_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS payroll (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    month VARCHAR(7) NOT NULL,
    gross_pay DECIMAL(14,2) NOT NULL,
    deductions DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    net_pay DECIMAL(14,2) NOT NULL,
    paid_on DATE,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Phase 9: Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    customer_id INT,
    channel VARCHAR(30) NOT NULL,
    subject VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    read_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Useful project queries

-- Register a user. Use the API in real projects so bcrypt hashing is handled safely.
INSERT INTO users (email, full_name, phone, hashed_password, role, is_verified)
VALUES ('admin@bank.com', 'Bank Admin', '9000000000', 'replace-with-bcrypt-hash', 'admin', TRUE);

-- Customer CRUD
INSERT INTO customers (
    first_name, last_name, email, phone, date_of_birth, pan_number, aadhaar_last_four, created_by_user_id
) VALUES (
    'Rahul', 'Sharma', 'rahul@example.com', '9876543210', '1998-05-10', 'ABCDE1234F', '1234', 1
);

SELECT * FROM customers ORDER BY id DESC;

SELECT *
FROM customers
WHERE first_name LIKE '%rahul%'
   OR last_name LIKE '%rahul%'
   OR email LIKE '%rahul%'
   OR phone LIKE '%rahul%';

UPDATE customers
SET status = 'verified', kyc_status = 'verified'
WHERE id = 1;

-- Address, nominee, and document records
INSERT INTO addresses (customer_id, address_type, line1, city, state, postal_code, country)
VALUES (1, 'home', 'MG Road', 'Bengaluru', 'Karnataka', '560001', 'India');

INSERT INTO nominees (customer_id, full_name, relationship, phone, share_percent)
VALUES (1, 'Priya Sharma', 'Sister', '9876500000', 100.00);

INSERT INTO customer_documents (customer_id, document_type, file_name, file_path, verified)
VALUES (1, 'pan_card', 'pan.pdf', 'uploads/customer_documents/1/pan.pdf', FALSE);

-- Account creation
INSERT INTO accounts (customer_id, account_number, account_type, balance)
VALUES (1, '10000000000001', 'savings', 5000.00);

INSERT INTO accounts (customer_id, account_number, account_type, balance)
VALUES (1, '10000000000002', 'current', 10000.00);

SELECT a.id, a.account_number, a.account_type, a.status, a.balance, c.first_name, c.last_name
FROM accounts a
JOIN customers c ON c.id = a.customer_id
WHERE c.id = 1;

UPDATE accounts
SET status = 'frozen'
WHERE id = 1;

-- Deposit
START TRANSACTION;
UPDATE accounts
SET balance = balance + 2000.00
WHERE id = 1 AND status = 'active';

INSERT INTO transactions (reference_no, to_account_id, transaction_type, channel, amount, status, description)
VALUES ('TXN-DEPOSIT-001', 1, 'deposit', 'branch', 2000.00, 'success', 'Cash deposit');
COMMIT;

-- Withdrawal
START TRANSACTION;
UPDATE accounts
SET balance = balance - 1000.00
WHERE id = 1 AND status = 'active' AND balance >= 1000.00;

INSERT INTO transactions (reference_no, from_account_id, transaction_type, channel, amount, status, description)
VALUES ('TXN-WITHDRAW-001', 1, 'withdrawal', 'branch', 1000.00, 'success', 'Cash withdrawal');
COMMIT;

-- Fund transfer
START TRANSACTION;
UPDATE accounts
SET balance = balance - 500.00
WHERE id = 1 AND status = 'active' AND balance >= 500.00;

UPDATE accounts
SET balance = balance + 500.00
WHERE id = 2 AND status = 'active';

INSERT INTO transactions (
    reference_no, from_account_id, to_account_id, transaction_type, channel, amount, status, description
) VALUES (
    'TXN-TRANSFER-001', 1, 2, 'fund_transfer', 'online', 500.00, 'success', 'Account transfer'
);
COMMIT;

-- Transaction history
SELECT *
FROM transactions
WHERE from_account_id = 1 OR to_account_id = 1
ORDER BY created_at DESC;

-- Beneficiary
INSERT INTO beneficiaries (customer_id, name, bank_name, account_number, ifsc_code, nickname)
VALUES (1, 'Amit Kumar', 'Demo Bank', '555566667777', 'DEMO0001234', 'Amit');

-- Loan application and approval
INSERT INTO loans (
    customer_id, loan_type, amount, annual_interest_rate, tenure_months, emi_amount, status
) VALUES (
    1, 'personal', 200000.00, 11.50, 24, 9369.00, 'applied'
);

UPDATE loans
SET status = 'approved', approved_by_user_id = 1
WHERE id = 1;

SELECT * FROM loans WHERE customer_id = 1;

-- Card management
INSERT INTO cards (account_id, customer_id, card_type, last_four, daily_limit, monthly_limit)
VALUES (1, 1, 'debit', '4321', 25000.00, 250000.00);

UPDATE cards
SET status = 'blocked'
WHERE id = 1;

UPDATE cards
SET daily_limit = 50000.00, monthly_limit = 500000.00
WHERE id = 1;

-- Branch and employee
INSERT INTO branches (code, name, ifsc_code, address, city, state, manager_user_id)
VALUES ('BR001', 'Main Branch', 'BANK0000001', 'Main Road', 'Chennai', 'Tamil Nadu', 1);

INSERT INTO employees (branch_id, full_name, email, designation, salary)
VALUES (1, 'Anita Rao', 'anita@bank.com', 'Relationship Manager', 55000.00);

INSERT INTO attendance (employee_id, work_date, status)
VALUES (1, CURDATE(), 'present');

INSERT INTO leave_requests (employee_id, start_date, end_date, reason)
VALUES (1, '2026-07-10', '2026-07-12', 'Family function');

INSERT INTO payroll (employee_id, month, gross_pay, deductions, net_pay, paid_on)
VALUES (1, '2026-07', 55000.00, 2500.00, 52500.00, CURDATE());

-- Notifications
INSERT INTO notifications (user_id, customer_id, channel, subject, message)
VALUES (1, 1, 'email', 'Account Created', 'Your savings account has been created.');

UPDATE notifications
SET read_at = NOW()
WHERE id = 1;

-- Reports and dashboard queries
SELECT COUNT(*) AS total_customers FROM customers;
SELECT COUNT(*) AS total_accounts, COALESCE(SUM(balance), 0) AS total_balance FROM accounts;
SELECT COUNT(*) AS total_transactions, COALESCE(SUM(amount), 0) AS transaction_volume FROM transactions;
SELECT status, COUNT(*) AS total_loans FROM loans GROUP BY status;

SELECT c.id, c.first_name, c.last_name, COUNT(a.id) AS account_count, COALESCE(SUM(a.balance), 0) AS total_balance
FROM customers c
LEFT JOIN accounts a ON a.customer_id = c.id
GROUP BY c.id, c.first_name, c.last_name;

-- Security reports
SELECT * FROM login_history ORDER BY created_at DESC LIMIT 100;
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100;

SELECT ip_address, COUNT(*) AS failed_attempts
FROM login_history
WHERE success = FALSE
GROUP BY ip_address
ORDER BY failed_attempts DESC;
