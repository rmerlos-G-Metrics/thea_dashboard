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
    """Fetches measurement and OCT data for a specific patient."""
    conn = sqlite3.connect(DB_PATH)
    df_eye = pd.read_sql("SELECT time_of_measurement, eye_pressure FROM eyemate_measurements WHERE patient_id = ?", conn, params=(patient_id,))
    df_oct = pd.read_sql("SELECT * FROM sulzbach_processed WHERE patient_id = ?", conn, params=(patient_id,))
    conn.close()
    
    return df_eye, df_oct