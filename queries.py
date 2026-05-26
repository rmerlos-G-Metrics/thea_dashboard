import sqlite3
import pandas as pd

DB_PATH = 'THEA.db'

def load_patient_master_list():
    """Loads the master list of patients for the dropdowns and filters."""
    conn = sqlite3.connect(DB_PATH)
    query = """
    WITH ValidPatients AS (
        SELECT patient_id FROM sulzbach_processed
        UNION SELECT patient_id FROM bochum
        UNION SELECT patient_id FROM mainz
    )
    SELECT DISTINCT v.patient_id, e.gender, e.type_of_glaucoma, e.npgs_type
    FROM ValidPatients v LEFT JOIN eyemate_measurements e ON v.patient_id = e.patient_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    df.fillna('Unknown', inplace=True)
    return df

def get_patient_data(patient_id):
    """Fetches measurement and OCT data, searching clinic tables until the patient is found."""
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch Eye Pressure Data
    df_eye = pd.read_sql(
        "SELECT time_of_measurement, eye_pressure FROM eyemate_measurements WHERE patient_id = ?", 
        conn, params=(patient_id,)
    )
    
    # 2. Smart Search for OCT Data
    df_oct = pd.DataFrame() # Start with an empty dataframe
    clinics = ['sulzbach_processed', 'bochum', 'mainz']
    
    for clinic_table in clinics:
        # We use an f-string for the table name, which is safe here because we hardcoded the list
        query = f"SELECT * FROM {clinic_table} WHERE patient_id = ?"
        temp_df = pd.read_sql(query, conn, params=(patient_id,))
        
        if not temp_df.empty:
            df_oct = temp_df
            break # We found the patient! Stop checking the other tables.
            
    conn.close()
    
    return df_eye, df_oct

def get_visit_data(patient_id):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT date, mnpvislabel, gat_mean, argos_mean FROM all_visits WHERE patient_id = ?"
    df_visits = pd.read_sql(query, conn, params=(patient_id,))
    conn.close()
    return df_visits