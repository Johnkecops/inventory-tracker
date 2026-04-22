import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

# Database Connection Configuration
# Note: Users should update these credentials to match their local MySQL setup
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '' # Enter your database password
DB_NAME = 'DrugTrackingSystem'

def get_connection():
    """Establish and return a connection to the database."""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# ----- App Layout & Styling -----
st.set_page_config(page_title="Drug Tracking System", page_icon="💊", layout="wide")

# Add some custom CSS to ensure proper sidebar rendering
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

st.title("💊 Drug Tracking System")

# ----- Sidebar Navigation -----
st.sidebar.title("Navigation")
menu = ["📊 Dashboard", "🩺 Manage Patients", "💊 Manage Drugs", "🛒 Record Purchase"]
# Ensure unique key for selectbox to prevent potential issues
choice = st.sidebar.selectbox("Go to", menu, key="main_navigation")

# ----------------- Dashboard -----------------
if choice == "📊 Dashboard":
    st.header("Dashboard - Purchase History")
    
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            # Using the view created in the SQL script
            cursor.execute("SELECT * FROM vw_purchase_history ORDER BY purchase_date DESC")
            result = cursor.fetchall()
            if result:
                df = pd.DataFrame(result)
                # Formatting the date for better display
                if 'purchase_date' in df.columns:
                    df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No purchase history found.")
        conn.close()

# ----------------- Manage Patients -----------------
elif choice == "🩺 Manage Patients":
    st.header("Manage Patients")
    
    # Form to add a new patient
    with st.expander("➕ Add New Patient"):
        with st.form("add_patient_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Patient Name", max_chars=100)
                age = st.number_input("Age", min_value=0, step=1)
            with col2:
                symptoms = st.text_area("Initial Symptoms")
            
            submit = st.form_submit_button("Add Patient")
            
            if submit:
                if not name:
                    st.warning("Patient name is required.")
                else:
                    conn = get_connection()
                    if conn:
                        try:
                            with conn.cursor() as cursor:
                                sql = "INSERT INTO Patients (name, age, symptoms) VALUES (%s, %s, %s)"
                                cursor.execute(sql, (name, age, symptoms))
                            conn.commit()
                            st.success(f"Patient '{name}' added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding patient: {e}")
                        finally:
                            conn.close()
                        
    # Display registered patients
    st.subheader("Registered Patients")
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Patients ORDER BY created_at DESC")
            result = cursor.fetchall()
            if result:
                df = pd.DataFrame(result)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No patients found.")
        conn.close()

# ----------------- Manage Drugs -----------------
elif choice == "💊 Manage Drugs":
    st.header("Manage Drugs")
    
    # Form to add a new drug
    with st.expander("➕ Add New Drug"):
        with st.form("add_drug_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Drug Name", max_chars=100)
                price = st.number_input("Price", min_value=0.0, format="%.2f")
            with col2:
                stock_level = st.number_input("Initial Stock Level", min_value=0, step=1)
                expiration_date = st.date_input("Expiration Date")
                
            submit = st.form_submit_button("Add Drug")
            
            if submit:
                if not name:
                    st.warning("Drug name is required.")
                else:
                    conn = get_connection()
                    if conn:
                        try:
                            with conn.cursor() as cursor:
                                # Using the stored procedure from SQL
                                cursor.execute("CALL AddDrug(%s, %s, %s, %s)", (name, price, stock_level, expiration_date))
                            conn.commit()
                            st.success(f"Drug '{name}' added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding drug: {e}")
                        finally:
                            conn.close()
    
    # Display current drug inventory
    st.subheader("Current Drugs Inventory")
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Drugs ORDER BY name ASC")
            result = cursor.fetchall()
            if result:
                df = pd.DataFrame(result)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No drugs found.")
        conn.close()

# ----------------- Record Purchase -----------------
elif choice == "🛒 Record Purchase":
    st.header("Record a Purchase")
    
    conn = get_connection()
    if conn:
        patients = []
        drugs = []
        try:
            with conn.cursor() as cursor:
                # Get patients
                cursor.execute("SELECT patient_id, name FROM Patients ORDER BY name ASC")
                patients = cursor.fetchall()
                
                # Get drugs that are in stock and not expired
                cursor.execute("SELECT drug_id, name, stock_level FROM Drugs WHERE stock_level > 0 AND (expiration_date IS NULL OR expiration_date >= CURDATE()) ORDER BY name ASC")
                drugs = cursor.fetchall()
        except Exception as e:
            st.error(f"Error retrieving data: {e}")
        finally:
            conn.close()
        
        if not patients:
            st.warning("Please register at least one patient first.")
        elif not drugs:
            st.warning("No available drugs in stock.")
        else:
            patient_options = {f"{p['name']} (ID: {p['patient_id']})": p['patient_id'] for p in patients}
            drug_options = {f"{d['name']} (Stock: {d['stock_level']})": d['drug_id'] for d in drugs}
            
            with st.form("record_purchase_form"):
                selected_patient = st.selectbox("Select Patient", list(patient_options.keys()))
                selected_drug = st.selectbox("Select Drug", list(drug_options.keys()))
                symptoms = st.text_area("Patient's Symptoms (Optional)", help="Leave blank if not applicable")
                
                submit = st.form_submit_button("Record Purchase")
                
                if submit:
                    patient_id = patient_options[selected_patient]
                    drug_id = drug_options[selected_drug]
                    
                    conn = get_connection()
                    if conn:
                        try:
                            with conn.cursor() as cursor:
                                # Using the stored procedure to handle logic (stock reduction, checks)
                                cursor.execute("CALL RecordPurchase(%s, %s, %s)", (patient_id, drug_id, symptoms))
                            conn.commit()
                            st.success("Purchase recorded successfully!")
                            st.balloons()
                        except pymysql.MySQLError as e:
                            # Catch specific MySQL errors (like the signals in triggers)
                            st.error(f"Database Error: {e.args[1]}")
                        except Exception as e:
                            st.error(f"Error recording purchase: {e}")
                        finally:
                            conn.close()
