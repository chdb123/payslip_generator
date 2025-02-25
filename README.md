# 📊 Payslip Generator

## 📌 Overview
The **MyAccess Payslip Generator** is a **Streamlit-based payroll management system** that enables companies to efficiently manage employee and intern details, generate payslips, and view insightful payroll analytics. The dashboard provides real-time data visualization, role-based access control, and an easy-to-use UI for payroll processing.

## 🔑 Features
- **User Authentication & Role Management** (SuperAdmin, Admin, Accounts Team)
- **Employee & Intern Management** (Add, Edit, Remove)
- **Payslip Generation & Download**
- **Dynamic Payroll Dashboard** with Charts & Metrics
- **Data Visualization** using **Plotly**
- **Database Integration** with **PostgreSQL**

---

## 📁 Database Schema
The project consists of four main tables:

### 1️⃣ `users`
| Column   | Type          | Description                        |
|----------|--------------|------------------------------------|
| `id`      | SERIAL PRIMARY KEY | Unique identifier |
| `username` | VARCHAR      | Name of the user |
| `email`    | VARCHAR (UNIQUE) | User email |
| `password` | TEXT         | Hashed password |
| `role`     | VARCHAR      | User role (Admin/SuperAdmin/Accounts Team) |

### 2️⃣ `employee_details`
| Column   | Type          | Description                        |
|----------|--------------|------------------------------------|
| `id`      | SERIAL PRIMARY KEY | Unique identifier |
| `employee_name` | VARCHAR | Name of the employee |
| `employee_id` | VARCHAR (UNIQUE) | Employee ID |
| `employee_email` | VARCHAR (UNIQUE) | Email |
| `employee_gender` | VARCHAR | Gender |
| `employee_designation` | VARCHAR | Job title |
| `employee_gross_pay` | INTEGER | Gross salary |
| `employee_basic_pay` | INTEGER | Basic salary |
| `employee_house_rent_allowance` | INTEGER | HRA |
| `employee_da` | INTEGER | Dearness Allowance |
| `employee_others_pay` | INTEGER | Other earnings |
| `employee_income_tax_deduction` | INTEGER | Tax deduction |
| `employee_provident_fund_deduction` | INTEGER | PF deduction |
| `employee_esi_deduction` | INTEGER | ESI deduction |

### 3️⃣ `intern_details`
| Column   | Type          | Description                        |
|----------|--------------|------------------------------------|
| `id`      | SERIAL PRIMARY KEY | Unique identifier |
| `intern_name` | VARCHAR | Name of the intern |
| `intern_id` | VARCHAR (UNIQUE) | Intern ID |
| `intern_email` | VARCHAR (UNIQUE) | Email |
| `university_name` | VARCHAR | University name |
| `role` | VARCHAR | Intern role |
| `intern_duration` | VARCHAR | Duration (3 Months, 6 Months, etc.) |
| `stipend` | INTEGER | Stipend amount |

### 4️⃣ `payslips`
| Column   | Type          | Description                        |
|----------|--------------|------------------------------------|
| `id`      | SERIAL PRIMARY KEY | Unique identifier |
| `employee_id` | VARCHAR | Employee ID |
| `pay_period` | VARCHAR | Month & Year of salary |
| `pdf_data` | BYTEA | Payslip PDF file |
| `generated_at` | TIMESTAMP | Date & time of payslip generation |

---

## 📌 Installation & Setup

### 🔧 Prerequisites
Ensure you have the following installed:
- **Python 3.8+**
- **PostgreSQL**
- **pip (Python Package Manager)**

### 📥 Clone the Repository
```bash
git clone https://github.com/your-repository/streamlit-payslip-generator.git
cd streamlit-payslip-generator
```
## 📊 Dashboard Overview
The dashboard provides an **interactive visualization** of payroll data:

- **Employee Count**
- **Intern Count**
- **Total Salaries Paid** (Based on selected month & year)
- **Total Payslips Generated**

### 📈 Charts & Insights
- **Employee Role Distribution** (**Treemap**)
- **Employee Designation Count** (**Bar Chart**)
- **Intern Duration Statistics** (**Pie Chart**)
- **Salary Distribution** (**Histogram**)

---

## 🔒 Authentication & User Roles
- **SuperAdmin**: Full access to manage users, employees, and payroll  
- **Admin**: Manage employees and interns but cannot edit users  
- **Accounts Team**: Limited access, only view & generate payslips  

---

## 📄 Payslip Generation
1. **Select an Employee**
2. **Choose Pay Period**
3. **Enter Salary & Deduction Details**
4. **Click Generate Payslip** → **Download PDF**

---

## 🛠 Future Enhancements
✅ **Employee Attendance & LOP Integration**  
✅ **Automated Email Payslip Delivery**  
✅ **Multi-Tenant Support for Multiple Companies**  

