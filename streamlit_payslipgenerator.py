import streamlit as st
from streamlit_option_menu import option_menu
import psycopg2
import time
import json
import io
import bcrypt
import pandas as pd 
from weasyprint import HTML
from num2words import num2words
# from xhtml2pdf import pisa
from jinja2 import *
from datetime import datetime, timedelta
import plotly.express as px

db_config = {
    "dbname": "payslipgenerator",
    "user": "postgres",  # Your PostgreSQL username
    "password": "12345",  # Your PostgreSQL password
    "host": "127.0.0.1",  # Keep this as it is
    "port": "5432"  # Default PostgreSQL port
}



def connect_to_database():
    try:
        connection = psycopg2.connect(**db_config)
        return connection, connection.cursor()
    except Exception as e:
        print("Database connection error:", e)
        return None, None
    

# Create User Table
def create_user_table(cursor, connection):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR NULL,
        email VARCHAR UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role VARCHAR NOT NULL
    );
    """)
    connection.commit()


# Create Employee Data Table
def create_employee_data_table(cursor,connection):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_details (
        id SERIAL PRIMARY KEY,
        employee_name VARCHAR NOT NULL,
        employee_id VARCHAR UNIQUE NOT NULL,
        employee_email VARCHAR UNIQUE NOT NULL,
        employee_gender VARCHAR NOT NULL,
        employee_designation VARCHAR NOT NULL,
        employee_PAN VARCHAR NOT NULL,
        employee_bank_name VARCHAR NOT NULL,
        employee_bank_account_number VARCHAR NOT NULL,
        employee_UAN_number VARCHAR NULL,
        employee_ESI_number VARCHAR NULL,
        employee_gross_pay INTEGER NULL,
        employee_basic_pay INTEGER NULL,
        employee_house_rent_allowance INTEGER NULL,
        employee_DA INTEGER NULL,
        employee_others_pay INTEGER NULL,
        employee_income_tax_deduction INTEGER NULL,
        employee_provident_fund_deduction INTEGER NULL,
        employee_ESI_deduction INTEGER NULL,
        employee_LOP_deduction INTEGER NULL    
    );
    """)
    connection.commit()
def create_intern_data_table(cursor, connection):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intern_details (
        id SERIAL PRIMARY KEY,
        intern_name VARCHAR NOT NULL,
        intern_id VARCHAR UNIQUE NOT NULL,
        intern_email VARCHAR UNIQUE NOT NULL,
        intern_gender VARCHAR NOT NULL,
        university_name VARCHAR NOT NULL,
        role VARCHAR NOT NULL,
        intern_duration VARCHAR NOT NULL,
        stipend INTEGER,
        intern_PAN VARCHAR,
        intern_bank_name VARCHAR,
        intern_bank_account_number VARCHAR
    );
    """)
    connection.commit()







def create_payslip_table(cursor, connection):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payslips (
        id SERIAL PRIMARY KEY,
        employee_id VARCHAR NOT NULL,
        pay_period VARCHAR NOT NULL,
        pdf_data BYTEA NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    connection.commit()


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


# Create SuperAdmin User
def create_superadmin(cursor, connection):
    password = "myaccess"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute("""
    INSERT INTO users (username, email, password, role)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (email) DO NOTHING;
    """, ("MYACCESS PRIVATE LIMITED", "streamlit@myaccessio.com", hashed_password, "SuperAdmin"))
    connection.commit()


#Add Users
def create_user(cursor, connection, email, username, role):
    try:
        password = "myaccess@123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("SELECT email FROM users WHERE email = %s;", (email,))
        if cursor.fetchone() is not None:
            st.warning("A user with this email already exists.")
            return False

        cursor.execute("""
        INSERT INTO users (username, email,password, role)
        VALUES (%s,%s,%s,%s);
        """, (username, email,hashed_password, role))
        connection.commit()
        st.success("User added successfully.")
        return True
    except Exception as e:
        st.error(f"Error adding user: {e}")
        return False


#Delete User
def delete_user(cursor, email, connection):
    verify_user_query = "SELECT COUNT(*) FROM users WHERE email = %s"
    cursor.execute(verify_user_query, (email,))
    result = cursor.fetchone()
    
    if result[0] > 0:
        delete_user_query = "DELETE FROM users WHERE email = %s;"
        cursor.execute(delete_user_query, (email,))
        connection.commit()


#Edit User
def edit_user(cursor, connection, email, username, role):
    query = "UPDATE users SET username = %s, role = %s WHERE email = %s"
    cursor.execute(query, (username, role, email))
    connection.commit()


#Fetch All Users from Database
def fetch_users(cursor):
    query = "SELECT username, email, role FROM users;"
    cursor.execute(query)
    return cursor.fetchall()


#Verify User Exists
def check_user_exists(cursor, email, username):
    query = "SELECT COUNT(*) FROM users WHERE email = %s OR username = %s"
    cursor.execute(query, (email, username))
    result = cursor.fetchone()
    return result[0] > 0 


#Fetch Users Email
def fetch_users_email(cursor):
    if st.session_state['role'] == "SuperAdmin":
        query = "SELECT email FROM users WHERE role != 'SuperAdmin';"
    elif st.session_state['role'] == "Admin":
        query = "SELECT email FROM users WHERE role NOT IN ('SuperAdmin', 'Admin');"
    else:
        return []
    cursor.execute(query)
    return cursor.fetchall()


#Fetch User from Database
def fetch_user(cursor, email):
    query = "SELECT username, role FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    return cursor.fetchone()


if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False  
if 'page' not in st.session_state:
    st.session_state['page'] = 'Login'  


#Login
def login(cursor, email, password):
    query = "SELECT username, role, password FROM users WHERE email = %s;"
    try:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        if result:
            username, role, hashed_password = result
            if verify_password(password, hashed_password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                return True
            else:
                st.error("Invalid password.")
        else:
            st.error("User not found.")
        return False
    except Exception as e:
        st.error("An error occurred during login.")
        print(f"Error: {e}")
        return False



# Streamlit Login Page
def login_page():
    st.title('Welcome to MyAccess Payslip Generator')
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    if st.button('Login'):
        connection, cursor = connect_to_database()
        if connection and cursor:
            if login(cursor, email, password):
                st.success("Login successful!")
                st.session_state['page'] = 'Dashboard'
                time.sleep(0.5)
                st.rerun()
            cursor.close()
            connection.close()


def fetch_dashboard_data(selected_month, selected_year):
    connection, cursor = connect_to_database()  # ✅ Correctly unpack both values
    if not connection or not cursor:
        print("Database connection failed!")
        return 0, 0, 0, 0, [], [], [], []

    selected_month_number = datetime.strptime(selected_month, "%B").month

    # ✅ Keep employee and intern counts static (do not depend on date)
    cursor.execute("SELECT COUNT(*) FROM employee_details;")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM intern_details;")
    total_interns = cursor.fetchone()[0]

    # ✅ Fetch total salaries paid (Only salaries for selected month)
    cursor.execute("""
        SELECT SUM(e.employee_gross_pay)
        FROM employee_details e
        JOIN payslips p ON e.employee_id = p.employee_id
        WHERE EXTRACT(MONTH FROM p.generated_at) = %s 
        AND EXTRACT(YEAR FROM p.generated_at) = %s;
    """, (selected_month_number, selected_year))
    total_salaries = cursor.fetchone()[0] or 0  # If no data, return 0

    # ✅ Fetch total payslips (Only for selected month)
    cursor.execute("""
        SELECT COUNT(*) FROM payslips 
        WHERE EXTRACT(MONTH FROM generated_at) = %s 
        AND EXTRACT(YEAR FROM generated_at) = %s;
    """, (selected_month_number, selected_year))
    total_payslips = cursor.fetchone()[0]

    # ✅ Fetch employee role distribution (Irrespective of Date)
    cursor.execute("""
        SELECT role, COUNT(*) 
        FROM users 
        GROUP BY role;
    """)
    role_counts = cursor.fetchall()

    # ✅ Fetch intern duration distribution (Irrespective of Date)
    cursor.execute("""
        SELECT intern_duration, COUNT(*)
        FROM intern_details 
        GROUP BY intern_duration;
    """)
    intern_durations = cursor.fetchall()

    # ✅ Fetch designation distribution (Date-Dependent)
    cursor.execute("""
        SELECT e.employee_designation, COUNT(*)
        FROM employee_details e
        JOIN payslips p ON e.employee_id = p.employee_id
        WHERE EXTRACT(MONTH FROM p.generated_at) = %s 
        AND EXTRACT(YEAR FROM p.generated_at) = %s
        GROUP BY e.employee_designation;
    """, (selected_month_number, selected_year))
    designation_counts = cursor.fetchall()

    # ✅ Fetch salary data (Only for selected month)
    cursor.execute("""
        SELECT e.employee_gross_pay
        FROM employee_details e
        JOIN payslips p ON e.employee_id = p.employee_id
        WHERE EXTRACT(MONTH FROM p.generated_at) = %s 
        AND EXTRACT(YEAR FROM p.generated_at) = %s;
    """, (selected_month_number, selected_year))
    salary_data = [row[0] for row in cursor.fetchall()]  # Convert tuple list to normal list

    cursor.close()
    connection.close()

    return total_employees, total_interns, total_salaries, total_payslips, role_counts, designation_counts, intern_durations, salary_data


def dashboard_page():
    st.set_page_config(page_title="MyAccess Dashboard", layout="wide")
    st.title("📊 Company Payroll Dashboard")

    # Sidebar
    with st.sidebar:
        role = st.session_state.get("role", "Guest")

        menu_options = ["Dashboard", "Payslip", "Manage Users", "Logout"] if role not in ['Accounts Team Member'] else ["Dashboard", "Payslip", "Logout"]

        selected = option_menu(
            menu_title="Menu",
            options=menu_options,
            icons=["speedometer2", "envelope-paper-fill", "people-fill", "box-arrow-left"][:len(menu_options)],
            menu_icon="list"
        )

        if selected == "Logout":
            st.session_state['logged_in'] = False
            st.session_state['page'] = 'Login'
            st.rerun()
        elif selected == "Payslip":
            time.sleep(0.5)
            st.session_state['page'] = 'Payslip Page'
            st.rerun()
        elif selected == "Manage Users":
            time.sleep(0.5)
            st.session_state['page'] = 'Manage Users'
            st.rerun()

        # Month and Year Selection
        st.markdown("### Select Month and Year")
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        
        if "selected_month" not in st.session_state:
            st.session_state["selected_month"] = datetime.now().strftime("%B")

        if "selected_year" not in st.session_state:
            st.session_state["selected_year"] = datetime.now().year

        selected_month = st.selectbox("Month", months, index=months.index(st.session_state["selected_month"]))
        selected_year = st.number_input("Year", min_value=2000, max_value=2100, value=st.session_state["selected_year"], step=1)

        st.session_state["selected_month"] = selected_month
        st.session_state["selected_year"] = selected_year


    # Fetch data based on selected month & year
    st.subheader(f"📅 Payroll Data for {selected_month} {selected_year}")
    total_employees, total_interns, total_salaries, total_payslips, role_counts, designation_counts, intern_durations, salary_data = fetch_dashboard_data(selected_month, selected_year)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👨‍💼 Employees", total_employees)
    col2.metric("🧑‍🎓 Interns", total_interns)
    col3.metric("💰 Salaries Paid", f"₹ {total_salaries:,}")
    col4.metric("📄 Payslips Generated", total_payslips)

    # ========== Row 2: Charts (4 charts in 2 rows) ==========
    st.markdown("---")
    col5, col6, col7, col8 = st.columns(4)

    # Convert data to Pandas DataFrame

    # Convert role_counts to a DataFrame
    roles_df = pd.DataFrame(role_counts, columns=["Role", "Count"])

    # Create a Treemap instead of a Pie Chart
    fig_roles = px.treemap(roles_df, path=["Role"], values="Count", title="Employee Role Distribution")


    designation_df = pd.DataFrame(designation_counts, columns=["Designation", "Count"])
    fig_designations = px.bar(designation_df, x="Designation", y="Count", title="Designation Distribution", color="Designation")

    intern_duration_df = pd.DataFrame(intern_durations, columns=["Duration", "Count"])
    fig_interns = px.pie(intern_duration_df, names="Duration", values="Count", title="Intern Duration")

    salary_df = pd.DataFrame(salary_data, columns=["Salary"])
    fig_salary = px.histogram(salary_df, x="Salary", nbins=10, title="Salary Distribution")

    col5.plotly_chart(fig_roles, use_container_width=True)
    col6.plotly_chart(fig_designations, use_container_width=True)
    col7.plotly_chart(fig_interns, use_container_width=True)
    col8.plotly_chart(fig_salary, use_container_width=True)

    # ========== Row 3: Employee & Intern Tables ==========
    st.markdown("---")
    




#Streamlit Manage Users Page
def manage_users_page():
    with st.sidebar:
        selected=option_menu(
            menu_title= "Menu",
            options = ["User's List","Add User","Remove User", "Edit User","Home"],
            icons= ["list-ul","plus-circle","trash", "pencil-square","house-door-fill"],
            menu_icon="list",
            )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Add User":
            time.sleep(0.5)
            st.session_state['page'] = 'Add User'
            st.rerun()
        elif selected == "User's List":
            time.sleep(0.5)
            st.session_state['page'] = "User's List"
            st.rerun()
        elif selected == "Remove User":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove User'
            st.rerun()
        elif selected == "Edit User":
            time.sleep(0.5)
            st.session_state['page'] = 'Edit User'
            st.rerun() 


#Streamlit User List Page
def users_list_page(cursor):
    with st.sidebar:
        selected=option_menu(
            menu_title= "Menu",
            options = ["User's List","Add User","Remove User", "Edit User","Home",],
            icons= ["people-fill","plus-circle","trash", "pencil-square","house-door-fill"],
            menu_icon="list",
            )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Add User":
            time.sleep(0.5)
            st.session_state['page'] = "Add User"
            st.rerun()
        elif selected == "Remove User":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove User'
            st.rerun()
        elif selected == "Edit User":
            time.sleep(0.5)
            st.session_state['page'] = 'Edit User'
            st.rerun()
    st.title("User's List")
    users = fetch_users(cursor)
    
    user_data = pd.DataFrame(users, columns=["Username", "Email", "Role"])
    st.table(user_data.style.set_table_styles(
        [
            {'selector': 'th', 'props': [('background-color', '#1f2937'), ('color', 'white'), ('font-size', '20px')]},
            {'selector': 'td', 'props': [('font-size', '18px')]}
        ]
    ))


#Streamlit Add User Page
def add_user_page(cursor):
    with st.sidebar:
        selected=option_menu(
            menu_title= "Menu",
            options = ["User's List","Add User","Remove User", "Edit User","Home",],
            icons= ["people-fill","plus-circle","trash", "pencil-square","house-door-fill"],
            menu_icon="list",
            )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "User's List":
            time.sleep(0.5)
            st.session_state['page'] = "User's List"
            st.rerun()
        elif selected == "Remove User":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove User'
            st.rerun()
        elif selected == "Edit User":
            time.sleep(0.5)
            st.session_state['page'] = 'Edit User'
            st.rerun()

    st.title("Add New User")
    new_username = st.text_input('Username')
    new_email = st.text_input('Email')

    if st.session_state['role'] == "SuperAdmin":
        print(st.session_state['role'])
        options = ['Select The Role', 'Admin', 'Accounts Team Member']
    else:
        options = ['Accounts Team Member']
    new_role = st.selectbox('Role', options=options)
            
    if st.button("Submit"):
        if new_username == "":
            st.error("Username cannot be empty.")
        elif new_email == "":
            st.error("Email cannot be empty.")
        elif check_user_exists(cursor, new_email, new_username):
            st.error("User with this email or username already exists.")
        elif new_role == "Select The Role":
            st.error("Please Select the Role")
        elif not new_role in options:
            st.error("Please Select the Role")
        else:
            create_user(cursor, connection, new_email, new_username, new_role)
            time.sleep(0.5)
            st.rerun()


#Streamlit Remove User Page
def remove_users_page(cursor,connection):
    with st.sidebar:
        selected=option_menu(
            menu_title= "Menu",
            options = ["User's List","Add User","Remove User", "Edit User","Home",],
            icons= ["people-fill","plus-circle","trash", "pencil-square","house-door-fill"],
            menu_icon="list",
            )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Add User":
            time.sleep(0.5)
            st.session_state['page'] = "Add User"
            st.rerun()
        elif selected == "User's List":
            time.sleep(0.5)
            st.session_state['page'] = "User's List"
            st.rerun()
        elif selected == "Edit User":
            time.sleep(0.5)
            st.session_state['page'] = 'Edit User'
            st.rerun()
    st.title("Remove User From this Site")
    emails = fetch_users_email(cursor)
    if emails:
        emails = [email[0] for email in emails if email[0]]
        email_selection = st.multiselect('Select Emails to Remove', options=emails)
        
        if st.button("Submit"):
            for email in email_selection:
                delete_user(cursor, email, connection)
            st.success("Selected users deleted successfully.")
            time.sleep(0.5)
            st.rerun()
    else:
        st.write("No emails found for deletion.")


#Streamlit Edit User Page
def edit_user_page(cursor):
    with st.sidebar:
        selected=option_menu(
            menu_title= "Menu",
            options = ["User's List","Add User","Remove User", "Edit User","Home",],
            icons= ["people-fill","plus-circle","trash", "pencil-square","house-door-fill"],
            menu_icon="list",
            )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Add User":
            time.sleep(0.5)
            st.session_state['page'] = "Add User"
            st.rerun()
        elif selected == "User's List":
            time.sleep(0.5)
            st.session_state['page'] = "User's List"
            st.rerun()
        elif selected == "Remove User":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove User'
            st.rerun()
    st.title("Edit User")
    emails = fetch_users_email(cursor)
    if emails:
        emails = [email[0] for email in emails if email[0]]
        email_selection = st.selectbox('Select Email to Edit', options=["Select the Email"]+emails)
        if email_selection != "Select the Email":
            user_data = fetch_user(cursor, email_selection)
            
            if user_data:
                username, role = user_data
                new_username = st.text_input("Username", value=username)
                if st.session_state['role'] == "SuperAdmin":
                    new_role = st.selectbox("Role", options=["Admin", "Procurement Team Member", "Hardware Team Member"], 
                                        index=["Admin", "Procurement Team Member", "Hardware Team Member"].index(role))     
                else:
                    new_role = st.selectbox("Role", options=["Procurement Team Member", "Hardware Team Member"], 
                                        index=["Procurement Team Member", "Hardware Team Member"].index(role))                
                if st.button("Update"):
                    edit_user(cursor, connection, email_selection, new_username, new_role)
                    st.success("User updated successfully!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.error("Email not found.")
        else:
            st.info("Please select a valid email to edit.")
    else:
        st.write("No Emails Found to Edit")


#Streamlit Manage Users Page
def payslip_page():
    with st.sidebar:
        selected=option_menu(
            menu_title= "Menu",
            options = ["Generate Payslip","Employee's List","Add Employee Details","Edit Employee Details", "Remove Employee Details","Home"],
            icons= ["file-earmark-pdf-fill","person-lines-fill","person-fill-add","person-fill-gear", "person-fill-dash","house-door-fill"],
            menu_icon="list",
            )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Generate Payslip":
            time.sleep(0.5)
            st.session_state['page'] = 'Generate Payslip'
            st.rerun()
        elif selected == "Add Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Add Employee Details'
            st.rerun()
        elif selected == "Employee's List":
            time.sleep(0.5)
            st.session_state['page'] = "Employee's List"
            st.rerun()
        elif selected == "Edit Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Edit Employee Details'
            st.rerun()
        elif selected == "Remove Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove Employee Details'
            st.rerun() 



def generate_payslip_page(cursor):
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu",
            options=["Generate Payslip", "Employee's List", "Add Employee Details", "Edit Employee Details", "Remove Employee Details", "Home"],
            icons=["file-earmark-pdf-fill", "person-lines-fill", "person-add", "person-gear", "person-dash", "house-door-fill"],
            menu_icon="list",
            default_index=0
        )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Employee's List":
            time.sleep(0.5)
            st.session_state['page'] = "Employee's List"
            st.rerun()
        elif selected == "Add Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Add Employee Details'
            st.rerun()
        elif selected == "Edit Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Edit Employee Details'
            st.rerun()
        elif selected == "Remove Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove Employee Details'
            st.rerun()

    st.title("Generate Payslip")

    # Step 1: Select Employee
    cursor.execute("SELECT employee_id, employee_email, employee_name FROM employee_details;")
    employees = cursor.fetchall()

    if not employees:
        st.warning("No employees found.")
        return

    employee_options = ["Select Employee"] + [f"{emp[0]} - {emp[1]} - {emp[2]}" for emp in employees]
    selected_employee = st.selectbox("Select Employee (ID - Email - Name)", options=employee_options)

    if selected_employee != "Select Employee":
        employee_id, employee_email, employee_name = selected_employee.split(" - ")

        # Fetch employee details for confirmation
        cursor.execute("SELECT * FROM employee_details WHERE employee_id = %s AND employee_email = %s;",
                       (employee_id, employee_email))
        employee_data = cursor.fetchone()

        if not employee_data:
            st.error("Employee details not found.")
            return

        st.write("### Employee Details")
        st.json({
            "Employee Name": employee_data[1],
            "Employee ID": employee_data[2],
            "Employee Email": employee_data[3],
            "Employee Gender": employee_data[4],
            "Employee Designation": employee_data[5],
            "Employee PAN Number":employee_data[6],
            "Employee Bank Name":employee_data[7],
            "Emplopyee Bank Account Number":employee_data[8],
            "UAN Number":employee_data[9],
            "ESI Number":employee_data[10],
            "Earnings": {
                "Basic": employee_data[12],
                "House Rent Allowance": employee_data[13],
                "DA": employee_data[14],
                "Others": employee_data[15],
                "Gross Earnings": employee_data[11]
            },
            "Deductions": {
                "Income Tax": employee_data[16],
                "Provident Fund": employee_data[17],
                "ESI": employee_data[18]
            }
        })

        # Form to input pay details
        submitted = False
        with st.form("generate_payslip_form"):
            current_date = datetime.now()
            months = [datetime(2000, i, 1).strftime("%B") for i in range(1, 13)]
            col1, col2 = st.columns(2)
            with col1:
                selected_month = st.selectbox("Select Month Of The Pay Period", months, index=current_date.month - 1)
            with col2:
                selected_year = st.number_input("Select Year Of The Pay Period", min_value=2024, value=current_date.year, step=1)
            pay_period = f"{selected_month} {selected_year}"
            pay_date = st.date_input("Pay Date")
            transaction_id = st.text_input("Transacation ID", placeholder="Enter Transaction ID")
            paid_days = st.number_input("Paid Days", min_value=0)
            lop_days = st.number_input("LOP (Loss of Pay) Days", min_value=0)
            submitted = st.form_submit_button("Generate Payslip")

        # If form is submitted
        if submitted:
            # Calculate Net Pay
            gross_pay = employee_data[11]
            total_deductions = sum([
                employee_data[16],  # Income Tax
                employee_data[17],  # Provident Fund
                employee_data[18]   # ESI
            ])
            net_pay = gross_pay - total_deductions
        #To convert the monthly amount to Words
            net_pay_in_words = num2words(net_pay, lang='en_IN')
            net_pay_in_words = net_pay_in_words.title()
            # html_file = "1.html"
            env = Environment(loader=FileSystemLoader('.'))  # Load templates from the current directory
            template = env.get_template('1.html')
            # Render the HTML template with data
            # template = Template(html_file)
            rendered_html = template.render(
                employee_name=employee_data[1],
                employee_id=employee_data[2],
                pay_period=pay_period,
                pay_date=pay_date,
                paid_days = paid_days,
                lop_days = lop_days,
                employee_gender = employee_data[4],
                employee_designation = employee_data[5],
                transaction_id = transaction_id,
                PAN_number = employee_data[6],
                bank_name = employee_data[7],
                bank_account_number = employee_data[8],
                UAN_number = employee_data[9],
                ESI_number = employee_data[10],
                basic_pay = employee_data[12],
                house_rent_allowance = employee_data[13],
                DA_pay = employee_data[14],
                others_pay = employee_data[15],
                income_tax_deduction = employee_data[16],
                PF_deduction = employee_data[17],
                ESI_deduction = employee_data[18],
                gross_pay=gross_pay,
                total_deductions=total_deductions,
                net_pay=net_pay,
                net_pay_in_words = net_pay_in_words
            )
            
            # Generate PDF using WeasyPrint
            pdf_output = io.BytesIO()
            HTML(string=rendered_html, base_url=".").write_pdf(pdf_output)
            pdf_output.seek(0)

            # Streamlit success message and download button
            try:
                cursor.execute("""
                    INSERT INTO payslips (employee_id, pay_period, pdf_data)
                    VALUES (%s, %s, %s);
                """, (employee_id, pay_period, pdf_output.read()))
                connection.commit()
                st.success("Payslip saved to the database successfully!")
                st.download_button(
                    label="Download Payslip as PDF",
                    data=pdf_output,
                    file_name=f"Payslip_{employee_id}_{pay_period}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error saving payslip to database: {e}")


def employee_list_page(cursor):
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu",
            options=["Generate Payslip","Employee's List", "Add Employee Details", "Edit Employee Details", "Remove Employee Details", "Home"],
            icons=["file-earmark-pdf-fill","person-lines-fill", "person-add", "person-gear", "person-dash", "house-door-fill"],
            menu_icon="list",
            default_index=1
        )
        if selected in ["Home", "Generate Payslip", "Add Employee Details", "Edit Employee Details", "Remove Employee Details"]:
            st.session_state['page'] = selected
            time.sleep(0.5)
            st.rerun()

    st.title("Employee & Intern List")

    # --- Dropdown for selection (Top-right) ---
    col1, col2 = st.columns([2, 1.5])  # Adjust width to make it smaller
    with col2:
        view_option = st.selectbox("View", ["Employees", "Interns", "Both"], label_visibility="collapsed")  # Hide label

    # --- Fetch & Display Employee Data ---
    if view_option in ["Employees", "Both"]:
        try:
            cursor.execute("""
                SELECT employee_id, employee_name, employee_email, employee_gender, employee_designation, 
                    employee_gross_pay, employee_basic_pay, employee_house_rent_allowance, employee_DA, 
                    employee_others_pay, employee_income_tax_deduction, employee_provident_fund_deduction,
                    employee_ESI_deduction
                FROM employee_details;
            """)
            employees = cursor.fetchall()

            if employees:
                st.subheader("Employee Details")
                employee_data = pd.DataFrame(employees, columns=[
                    "Employee ID", "Name", "Email", "Gender", "Designation", "Gross Pay", "Basic Pay", 
                    "HRA", "DA", "Other Pay", "Income Tax Deduction", "PF Deduction", "ESI Deduction"
                ])
                st.table(employee_data.style.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#1f2937'), ('color', 'white'), ('font-size', '18px')]},
                    {'selector': 'td', 'props': [('font-size', '16px')]}
                ]))
            else:
                st.warning("No Employee details found.")
        except Exception as e:
            st.error(f"Error fetching employee data: {e}")

    # --- Fetch & Display Intern Data ---
    if view_option in ["Interns", "Both"]:
        try:
            cursor.execute("""
                SELECT intern_name, intern_id, intern_email, intern_gender, university_name, role, 
                intern_duration, stipend, intern_PAN, intern_bank_name, intern_bank_account_number
                FROM intern_details;
            """)
            interns = cursor.fetchall()

            if interns:
                st.subheader("Intern Details")
                intern_data = pd.DataFrame(interns, columns=[
                    "Intern Name", "Intern ID", "Email", "Gender", "University",
                    "Role", "Duration", "Stipend", "PAN", "Bank Name", "Account Number"
                ])

                st.table(intern_data.style.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#1f2937'), ('color', 'white'), ('font-size', '18px')]},
                    {'selector': 'td', 'props': [('font-size', '16px')]}
                ]))
            else:
                st.warning("No Intern details found.")
        except Exception as e:
            st.error(f"Error fetching intern data: {e}")



def add_employee_details_page(cursor):
    with st.sidebar:
        selected=option_menu(
            menu_title= "Menu",
            options = ["Generate Payslip","Employee's List","Add Employee Details","Edit Employee Details", "Remove Employee Details","Home"],
            icons= ["file-earmark-pdf-fill","person-lines-fill","person-add","person-gear", "person-dash","house-door-fill"],
            menu_icon="list",
            default_index=2
            )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Generate Payslip":
            time.sleep(0.5)
            st.session_state['page'] = 'Generate Payslip'
            st.rerun()
        elif selected == "Employee's List":
            time.sleep(0.5)
            st.session_state['page'] = "Employee's List"
            st.rerun()
        elif selected == "Edit Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Edit Employee Details'
            st.rerun()
        elif selected == "Remove Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove Employee Details'
            st.rerun()     
    st.title("Add Employee Details") 

    col1, col2 = st.columns([2, 1.5])
    with col2:
        user_type = st.selectbox("Select Type", ["Employee", "Intern"], label_visibility="collapsed")

    with st.form("employee_form" if user_type == "Employee" else "intern_form"):
        name = st.text_input("Full Name", placeholder="Enter Full Name")
        user_id = st.text_input(f"{user_type} ID", placeholder=f"Enter {user_type} ID")
        email = st.text_input(f"{user_type} Email", placeholder=f"Enter {user_type} Email")
        gender = st.selectbox(f"{user_type} Gender", ["Select Gender", "Male", "Female", "Rather Not To Say"])

        if user_type == "Employee":
            designation = st.text_input("Designation", placeholder="Enter Designation")
            pan = st.text_input("PAN", placeholder="Enter PAN")
            bank_name = st.text_input("Bank Name", placeholder="Enter Bank Name")
            account_number = st.text_input("Bank Account Number", placeholder="Enter Bank Account Number")
            uan_number = st.text_input("UAN Number", placeholder="Enter UAN Number")
            esi_number = st.text_input("ESI Number", placeholder="Enter ESI Number")
            gross_pay = st.text_input("Gross Pay", placeholder="Enter Gross Pay")
            basic_pay = st.text_input("Basic Pay", placeholder="Enter Basic Pay")
            hra = st.text_input("House Rent Allowance", placeholder="Enter House Rent Allowance")
            da = st.text_input("DA", placeholder="Enter DA")
            others_pay = st.text_input("Others Pay", placeholder="Enter Others Pay")
            income_tax = st.text_input("Income Tax Deduction", placeholder="Enter Income Tax Deduction")
            provident_fund = st.text_input("Provident Fund Deduction", placeholder="Enter Provident Fund Deduction")
            esi_deduction = st.text_input("ESI Deduction", placeholder="Enter ESI Deduction")

        else:  # Intern form
            university = st.text_input("University Name", placeholder="Enter University Name") 
            role = st.text_input(f"{user_type} Role", placeholder=f"Enter {user_type} Role")
            duration = st.selectbox("Internship Duration", ["Select Duration", "3 Months", "6 Months", "1 Year"])
            stipend = st.text_input("Stipend", placeholder="Enter Stipend (if any)")

            intern_pan = st.text_input("PAN Number", placeholder="Enter PAN Number")
            intern_bank_name = st.text_input("Bank Name", placeholder="Enter Bank Name")
            intern_account_number = st.text_input("Bank Account Number", placeholder="Enter Bank Account Number")

        submit_button = st.form_submit_button("Submit")

        if submit_button:
            try:
                table_name = "employee_details" if user_type == "Employee" else "intern_details"
                id_column = "employee_id" if user_type == "Employee" else "intern_id"
                email_column = "employee_email" if user_type == "Employee" else "intern_email"

                # Check if the user already exists
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {email_column} = %s OR {id_column} = %s;", (email, user_id,))
                result = cursor.fetchone()
                if result[0] > 0:
                    st.error(f"A {user_type} with this Email or ID already exists.")
                    return

                if user_type == "Employee":
                    # Validate numeric fields
                    numeric_fields = {
                        "Gross Pay": gross_pay,
                        "Basic Pay": basic_pay,
                        "House Rent Allowance": hra,
                        "DA": da,
                        "Others Pay": others_pay,
                        "Income Tax Deduction": income_tax,
                        "Provident Fund Deduction": provident_fund,
                        "ESI Deduction": esi_deduction
                    }

                    validated_fields = {}
                    for field_name, value in numeric_fields.items():
                        if not value.isdigit():
                            st.error(f"{field_name} must be a number.")
                            return
                        validated_fields[field_name] = int(value)

                    gross_components_sum = (
                        validated_fields["Basic Pay"] +
                        validated_fields["House Rent Allowance"] +
                        validated_fields["DA"] +
                        validated_fields["Others Pay"]
                    )

                    if validated_fields["Gross Pay"] != gross_components_sum:
                        st.error("Gross Pay does not match the sum of Basic Pay, House Rent Allowance, DA, and Others Pay.")
                        return

                    cursor.execute("""
                    INSERT INTO employee_details (
                        employee_name, employee_id, employee_email, employee_gender, employee_designation, employee_PAN,
                        employee_bank_name, employee_bank_account_number, employee_UAN_number, employee_ESI_number,
                        employee_gross_pay, employee_basic_pay, employee_house_rent_allowance, employee_DA,
                        employee_others_pay, employee_income_tax_deduction, employee_provident_fund_deduction, employee_ESI_deduction, employee_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        name, user_id, email, gender, designation, pan, bank_name, account_number, uan_number, esi_number,
                        validated_fields["Gross Pay"], validated_fields["Basic Pay"],
                        validated_fields["House Rent Allowance"], validated_fields["DA"],
                        validated_fields["Others Pay"], validated_fields["Income Tax Deduction"],
                        validated_fields["Provident Fund Deduction"], validated_fields["ESI Deduction"], "Employee"
                    ))

                else:  # Intern
                    stipend_value = int(stipend) if stipend.isdigit() else None  # Convert stipend to integer or None

                    st.write(f"INSERT INTO intern_details VALUES: {name}, {user_id}, {email}, {gender}, {university}, {role}, {duration}, {stipend}, {intern_pan}, {intern_bank_name}, {intern_account_number}")

                    try:
                        cursor.execute("""
                        INSERT INTO intern_details (
                            intern_name, intern_id, intern_email, intern_gender, university_name, role, 
                            intern_duration, stipend, intern_PAN, intern_bank_name, intern_bank_account_number
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """, (name, user_id, email, gender, university, role, duration, stipend, intern_pan, intern_bank_name, intern_account_number))

                        connection.commit()
                        st.success("Intern details added successfully!")

                    except Exception as e:
                        st.error(f"Database error: {e}")
                        connection.rollback()


            except Exception as e:
                connection.rollback()  # ❌ Rollback if error occurs
                st.error(f"Database error: {e}")


def edit_employee_details_page(cursor):
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu",
            options=["Generate Payslip","Employee's List", "Add Employee Details", "Edit Employee Details", "Remove Employee Details", "Home"],
            icons=["file-earmark-pdf-fill","person-lines-fill", "person-add", "person-gear", "person-dash", "house-door-fill"],
            menu_icon="list",
            default_index=3
        )
        if selected == "Home":
            time.sleep(0.5)
            st.session_state['page'] = 'Dashboard'
            st.rerun()
        elif selected == "Generate Payslip":
            time.sleep(0.5)
            st.session_state['page'] = 'Generate Payslip'
            st.rerun()
        elif selected == "Employee's List":
            time.sleep(0.5)
            st.session_state['page'] = "Employee's List"
            st.rerun()
        elif selected == "Add Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Add Employee Details'
            st.rerun()
        elif selected == "Remove Employee Details":
            time.sleep(0.5)
            st.session_state['page'] = 'Remove Employee Details'
            st.rerun()

    st.title("Edit Employee/Intern Details")

    # Selection Dropdown (Intern or Employee)
    col1, col2 = st.columns([2, 1.5]) # Adjust column width ratio as needed

    with col2:
        category = st.selectbox("Select Type", ["Employee", "Intern"], label_visibility="collapsed")
    if category == "Select":
        st.warning("Please select a category.")
        return

    # Fetch Employees or Interns Based on Selection
    if category == "Employee":
        cursor.execute("SELECT employee_id, employee_email FROM employee_details;")
    else:
        cursor.execute("SELECT intern_id, intern_email FROM intern_details;")
        
    records = cursor.fetchall()

    #if not records:
        #st.warning(f"No {category.lower()} details found to edit.")
       # return

    record_options = ["Select"] + [f"{rec[0]} - {rec[1]}" for rec in records]
    selected_record = st.selectbox(f"Select {category} (ID - Email)", options=record_options)

    if selected_record != "Select":
        record_id, record_email = selected_record.split(" - ")

        # Fetch details based on selection
        if category == "Employee":
            cursor.execute("SELECT * FROM employee_details WHERE employee_id = %s AND employee_email = %s;",
                           (record_id, record_email))
        else:
            cursor.execute("SELECT * FROM intern_details WHERE intern_id = %s AND intern_email = %s;",
                           (record_id, record_email))

        record_data = cursor.fetchone()

        if not record_data:
            st.error(f"{category} details not found.")
            return

        # Unpack details
        if category == "Employee":
            (
                id, emp_name, emp_id, emp_email, emp_gender, emp_designation, emp_pan, emp_bank_name, emp_account_number,
                emp_uan, emp_esi, emp_gross_pay, emp_basic_pay, emp_hra, emp_da, emp_others_pay, emp_tax_deduction,
                emp_pf_deduction, emp_esi_deduction, emp_lop_deduction
            ) = record_data
        else:
            (
                id, intern_name, intern_id, intern_email, intern_gender, 
                university_name, role, intern_duration, stipend, 
                intern_pan, intern_bank_name, intern_bank_account_number
            ) = record_data


        # Dynamic Form
        with st.form("edit_form"):
            if category == "Employee":
                name = st.text_input("Employee Name", value=emp_name)
                designation = st.text_input("Designation", value=emp_designation)
                PAN = st.text_input("PAN", value=emp_pan)
                bank_name = st.text_input("Bank Name", value=emp_bank_name)
                account_number = st.text_input("Bank Account Number", value=emp_account_number)
                UAN = st.text_input("UAN Number", value=emp_uan)
                ESI = st.text_input("ESI Number", value=emp_esi)
                gross_pay = st.text_input("Gross Pay", value=str(emp_gross_pay))
                basic_pay = st.text_input("Basic Pay", value=str(emp_basic_pay))
                hra = st.text_input("House Rent Allowance", value=str(emp_hra))
                da = st.text_input("DA", value=str(emp_da))
                others_pay = st.text_input("Others Pay", value=str(emp_others_pay))
                income_tax = st.text_input("Income Tax Deduction", value=str(emp_tax_deduction))
                pf_deduction = st.text_input("Provident Fund Deduction", value=str(emp_pf_deduction))
                esi_deduction = st.text_input("ESI Deduction", value=str(emp_esi_deduction))
            else:  # Intern form
                name = st.text_input("Intern Name", value=intern_name)
                university = st.text_input("University Name", value=university_name)
                role = st.text_input("Role", value=role)
                duration = st.selectbox("Internship Duration", ["3 Months", "6 Months", "1 Year"], index=["3 Months", "6 Months", "1 Year"].index(intern_duration))
                stipend = st.text_input("Stipend", value=str(stipend))
                pan = st.text_input("PAN Number", value=intern_pan)
                bank_name = st.text_input("Bank Name", value=intern_bank_name)
                account_number = st.text_input("Bank Account Number", value=intern_bank_account_number)
            submit_button = st.form_submit_button("Update")

            if submit_button:
                try:
                    if category == "Employee":
                        numeric_fields = {
                            "Gross Pay": gross_pay,
                            "Basic Pay": basic_pay,
                            "HRA": hra,
                            "DA": da,
                            "Others Pay": others_pay,
                            "Income Tax Deduction": income_tax,
                            "Provident Fund Deduction": pf_deduction,
                            "ESI Deduction": esi_deduction
                        }
                        validated_fields = {}
                        for field_name, value in numeric_fields.items():
                            if not value.isdigit():
                                st.error(f"{field_name} must be a number.")
                                return
                            validated_fields[field_name] = int(value)

                        gross_components_sum = (
                            validated_fields["Basic Pay"] +
                            validated_fields["HRA"] +
                            validated_fields["DA"] +
                            validated_fields["Others Pay"]
                        )
                        if validated_fields["Gross Pay"] != gross_components_sum:
                            st.error("Gross Pay does not match the sum of Basic Pay, HRA, DA, and Others Pay.")
                            return

                        cursor.execute("""
                            UPDATE employee_details
                            SET employee_name = %s, employee_designation = %s, employee_PAN = %s,
                                employee_bank_name = %s, employee_bank_account_number = %s, employee_UAN_number = %s,
                                employee_ESI_number = %s, employee_gross_pay = %s, employee_basic_pay = %s,
                                employee_house_rent_allowance = %s, employee_DA = %s, employee_others_pay = %s,
                                employee_income_tax_deduction = %s, employee_provident_fund_deduction = %s,
                                employee_ESI_deduction = %s
                            WHERE employee_id = %s AND employee_email = %s;
                        """, (
                            name, designation, PAN, bank_name, account_number, UAN, ESI,
                            validated_fields["Gross Pay"], validated_fields["Basic Pay"], validated_fields["HRA"],
                            validated_fields["DA"], validated_fields["Others Pay"], validated_fields["Income Tax Deduction"],
                            validated_fields["Provident Fund Deduction"], validated_fields["ESI Deduction"],
                            record_id, record_email
                        ))
                    else:
                        cursor.execute("""
                            UPDATE intern_details
                            SET intern_name = %s, university_name = %s, role = %s,
                                intern_duration = %s, stipend = %s, intern_PAN = %s,
                                intern_bank_name = %s, intern_bank_account_number = %s
                            WHERE intern_id = %s AND intern_email = %s;
                        """, (name, university, role, duration, stipend, pan, bank_name, account_number, record_id, record_email))


                    st.success(f"{category} details updated successfully.")
                except Exception as e:
                    st.error(f"Error updating {category} details: {e}")




def remove_employee_details_page(cursor):
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu",
            options=["Generate Payslip", "Employee's List", "Add Employee Details", "Edit Employee Details", "Remove Employee Details", "Home"],
            icons=["file-earmark-pdf-fill", "person-lines-fill", "person-add", "person-gear", "person-dash", "house-door-fill"],
            menu_icon="list",
            default_index=4
        )
        if selected != "Remove Employee Details":
            st.session_state['page'] = selected
            time.sleep(0.5)
            st.rerun()

    st.title("Remove Employee/Intern Details")

    # Dropdown to select category (Employee or Intern)
    col1, col2 = st.columns([2, 1.5])
    with col2:
        category = st.selectbox("Select Type", ["Employee", "Intern"], label_visibility="collapsed")

    if category == "Select":
        st.warning("Please select a category.")
        return

    # Fetch records based on selection
    table_name = "employee_details" if category == "Employee" else "intern_details"
    id_column = "employee_id" if category == "Employee" else "intern_id"
    email_column = "employee_email" if category == "Employee" else "intern_email"

    cursor.execute(f"SELECT {id_column}, {email_column} FROM {table_name};")
    records = cursor.fetchall()

    if not records:
        st.warning(f"No {category.lower()} details found to remove.")
        return

    record_options = ["Select"] + [f"{rec[0]} - {rec[1]}" for rec in records]
    selected_record = st.selectbox(f"Select {category} (ID - Email)", options=record_options)

    if selected_record != "Select":
        record_id, record_email = selected_record.split(" - ")

        st.error(f"Are you sure you want to delete {category} with ID **{record_id}** and Email **{record_email}**?")
        
        if st.button(f"Remove {category}"):
            try:
                cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = %s AND {email_column} = %s;", (record_id, record_email))
                connection.commit()
                st.success(f"{category} details removed successfully!")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error removing {category}: {e}")




if st.session_state['logged_in']:
    if st.session_state['page'] == 'Dashboard':
        dashboard_page()
    elif st.session_state['page'] == 'Manage Users':
        manage_users_page()
    elif st.session_state['page'] == "User's List":    
        connection,cursor = connect_to_database()
        users_list_page(cursor)
    elif st.session_state['page'] == 'Add User': 
        connection,cursor = connect_to_database()
        add_user_page(cursor)
    elif st.session_state['page'] == "Remove User":    
        connection,cursor = connect_to_database()
        remove_users_page(cursor,connection)
    elif st.session_state['page'] == "Edit User":
        connection,cursor = connect_to_database()
        edit_user_page(cursor) 
    elif st.session_state['page'] == 'Payslip Page':
        payslip_page()
    elif st.session_state['page'] == "Employee's List":
        connection,cursor = connect_to_database()
        employee_list_page(cursor)
    elif st.session_state['page'] == "Add Employee Details":
        connection,cursor = connect_to_database()
        add_employee_details_page(cursor)
    elif st.session_state['page'] == "Edit Employee Details":
        connection,cursor = connect_to_database()
        edit_employee_details_page(cursor)
    elif st.session_state['page'] == "Remove Employee Details":
        connection,cursor = connect_to_database()
        remove_employee_details_page(cursor)
    elif st.session_state['page'] == "Generate Payslip":
        connection, cursor = connect_to_database()
        generate_payslip_page(cursor)

else:
    login_page()


if __name__ == "__main__":
    connection, cursor = connect_to_database()
    if connection and cursor:
        create_user_table(cursor, connection)
        create_superadmin(cursor, connection)
        create_employee_data_table(cursor,connection)
        create_intern_data_table(cursor, connection)
        create_payslip_table(cursor, connection)
        cursor.close()
        connection.close()

