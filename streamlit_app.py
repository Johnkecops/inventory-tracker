from collections import defaultdict
from pathlib import Path
import sqlite3

import streamlit as st
import altair as alt
import pymysql
import pandas as pd



# Database Connection Configuration
DB_NAME = 'DrugTrackingSystem'

st.set_page_config(page_title="Drug Tracking System", layout="wide", page_icon="💊")
st.title("💊 Drug Tracking System Dashboard")

st.sidebar.header("Database Connection settings")
db_host = st.sidebar.text_input("Host", value="localhost")
db_user = st.sidebar.text_input("User", value="root")
db_password = st.sidebar.text_input("Password", type="password", help="Leave blank if your user has no password")

def get_connection():
    try:
        return pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.err.OperationalError as e:
        code, msg = e.args
        st.error(f"MySQL Error {code}: {msg}")
        st.info("Tip: If you're getting 'Access denied' and 'using password: NO', it means your database account requires a password but the password field is left empty. Conversely, if it says 'using password: YES', it means the password you provided is incorrect.")
        return None
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

menu = ["Dashboard", "Manage Drugs", "Manage Patients", "Record Purchase", "Purchase History"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Dashboard":
    st.subheader("System Overview")
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        
        col1, col2, col3 = st.columns(3)
        
        cursor.execute("SELECT COUNT(*) as count FROM Drugs")
        drug_count = cursor.fetchone()['count']
        col1.metric("Total Drugs in Catalog", drug_count)
        
        cursor.execute("SELECT COUNT(*) as count FROM Patients")
        patient_count = cursor.fetchone()['count']
        col2.metric("Total Patients", patient_count)
        
        cursor.execute("SELECT COUNT(*) as count FROM Purchases")
        purchase_count = cursor.fetchone()['count']
        col3.metric("Total Purchases", purchase_count)
        
        conn.close()
        
elif choice == "Manage Drugs":
    st.subheader("Medicine Catalog")
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Drugs")
        df = pd.DataFrame(cursor.fetchall())
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No drugs found in database.")
        
        st.markdown("---")
        st.subheader("Add New Drug")
        with st.form("add_drug_form"):
            new_name = st.text_input("Drug Name")
            new_price = st.number_input("Price", min_value=0.0, format="%.2f")
            new_stock = st.number_input("Initial Stock", min_value=0, step=1)
            new_exp = st.date_input("Expiration Date")
            submit = st.form_submit_button("Add Drug")
            
            if submit:
                try:
                    cursor.callproc('AddDrug', (new_name, new_price, new_stock, new_exp))
                    conn.commit()
                    st.success(f"Successfully added {new_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding drug: {e}")
        conn.close()

elif choice == "Manage Patients":
    st.subheader("Registered Patients")
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Patients")
        df = pd.DataFrame(cursor.fetchall())
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No patients found in database.")
            
        st.markdown("---")
        st.subheader("Register New Patient")
        with st.form("add_patient_form"):
            p_name = st.text_input("Patient Name")
            p_age = st.number_input("Age", min_value=0, step=1)
            p_symp = st.text_area("Symptoms")
            submit = st.form_submit_button("Register Patient")
            
            if submit:
                try:
                    cursor.execute("INSERT INTO Patients (name, age, symptoms) VALUES (%s, %s, %s)", (p_name, p_age, p_symp))
                    conn.commit()
                    st.success(f"Successfully registered {p_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error registering patient: {e}")
        conn.close()

elif choice == "Record Purchase":
    st.subheader("Record a New Purchase")
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Get patients
        cursor.execute("SELECT patient_id, name FROM Patients")
        patients = cursor.fetchall()
        
        # Get drugs
        cursor.execute("SELECT drug_id, name, stock_level, price FROM Drugs WHERE stock_level > 0")
        drugs = cursor.fetchall()
        
        if not patients:
            st.warning("Please register a patient first.")
        elif not drugs:
            st.warning("No available drugs in stock.")
        else:
            p_options = {f"{p['patient_id']} - {p['name']}": p['patient_id'] for p in patients}
            d_options = {f"{d['drug_id']} - {d['name']} (Stock: {d['stock_level']}, Price: {d['price']})": d['drug_id'] for d in drugs}
            
            with st.form("record_purchase_form"):
                selected_patient = st.selectbox("Select Patient", options=list(p_options.keys()))
                selected_drug = st.selectbox("Select Drug", options=list(d_options.keys()))
                symptoms = st.text_area("Symptoms (Optional)")
                submit = st.form_submit_button("Record Purchase")
                
                if submit:
                    try:
                        p_id = p_options[selected_patient]
                        d_id = d_options[selected_drug]
                        cursor.callproc('RecordPurchase', (p_id, d_id, symptoms))
                        conn.commit()
                        st.success("Purchase recorded successfully!")
                    except Exception as e:
                        st.error(f"Error recording purchase: {e}")
        conn.close()

elif choice == "Purchase History":
    st.subheader("Purchase History")
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vw_purchase_history ORDER BY purchase_date DESC")
        df = pd.DataFrame(cursor.fetchall())
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No purchases recorded yet.")
        conn.close()
    .encode(
        x="units_sold",
        y=alt.Y("item_name").sort("-x"),
    ),
    use_container_width=True,
)
