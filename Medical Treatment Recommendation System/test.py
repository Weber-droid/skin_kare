import streamlit as st
import openai
import pandas as pd
import json
from datetime import datetime
import hashlib
import sqlite3
import os
from typing import Dict, List

# Initialize database
def init_db():
    conn = sqlite3.connect('medical_records.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients
        (id TEXT PRIMARY KEY,
         name TEXT,
         age INTEGER,
         genetic_profile TEXT,
         medical_history TEXT,
         created_at TIMESTAMP)
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS recommendations
        (id TEXT PRIMARY KEY,
         patient_id TEXT,
         recommendation TEXT,
         created_at TIMESTAMP,
         FOREIGN KEY (patient_id) REFERENCES patients(id))
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Streamlit configuration
st.set_page_config(page_title="Medical Treatment Recommendation System", layout="wide")
st.title("🏥 Medical Treatment Recommendation System")

# Sidebar for API configuration
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter OpenRouter API Key", type="password")
    model = st.selectbox(
        "Select AI Model",
        ["anthropic/claude-3-opus", "anthropic/claude-3-sonnet", "google/gemini-pro"]
    )

def generate_patient_id(name: str, dob: str) -> str:
    """Generate a unique patient ID."""
    return hashlib.md5(f"{name}{dob}".encode()).hexdigest()

def save_patient_data(patient_data: Dict):
    """Save patient data to SQLite database."""
    conn = sqlite3.connect('medical_records.db')
    c = conn.cursor()
    
    patient_id = generate_patient_id(patient_data['name'], str(patient_data['dob']))
    
    c.execute('''
        INSERT OR REPLACE INTO patients
        (id, name, age, genetic_profile, medical_history, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        patient_id,
        patient_data['name'],
        patient_data['age'],
        json.dumps(patient_data['genetic_profile']),
        json.dumps(patient_data['medical_history']),
        datetime.now()
    ))
    
    conn.commit()
    conn.close()
    return patient_id

def get_ai_recommendation(patient_data: Dict) -> str:
    """Get AI-powered treatment recommendation."""
    if not api_key:
        return "Please enter an API key in the sidebar to get recommendations."
    
    prompt = f"""Based on the following patient data, provide a detailed treatment recommendation:

Patient Information:
- Age: {patient_data['age']}
- Genetic Profile: {patient_data['genetic_profile']}
- Medical History: {patient_data['medical_history']}

Please provide:
1. Primary treatment recommendations
2. Alternative treatment options
3. Lifestyle modifications
4. Monitoring requirements
5. Potential drug interactions to watch for

Format the response in a clear, medical professional-friendly format."""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = openai.ChatCompletion.create(
            api_base="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            **data
        )
        
        recommendation = response.choices[0].message.content
        
        # Save recommendation to database
        conn = sqlite3.connect('medical_records.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO recommendations (id, patient_id, recommendation, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            hashlib.md5(recommendation.encode()).hexdigest(),
            generate_patient_id(patient_data['name'], str(patient_data['dob'])),
            recommendation,
            datetime.now()
        ))
        conn.commit()
        conn.close()
        
        return recommendation
    except Exception as e:
        return f"Error generating recommendation: {str(e)}"

# Main application interface
tab1, tab2 = st.tabs(["New Patient", "View Records"])

with tab1:
    st.header("Patient Information")
    
    # Basic Information
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120)
        dob = st.date_input("Date of Birth")
    
    # Genetic Profile
    st.subheader("Genetic Profile")
    genetic_markers = st.text_area(
        "Enter genetic markers or upload genetic profile",
        height=100,
        help="Enter known genetic markers, mutations, or relevant genetic information"
    )
    
    # Medical History
    st.subheader("Medical History")
    conditions = st.multiselect(
        "Existing Conditions",
        ["Diabetes", "Hypertension", "Heart Disease", "Cancer", "Asthma", "Other"]
    )
    
    medications = st.text_area("Current Medications", height=100)
    allergies = st.text_area("Allergies", height=68)
    
    if st.button("Generate Recommendation"):
        if name and age:
            patient_data = {
                "name": name,
                "age": age,
                "dob": dob,
                "genetic_profile": genetic_markers,
                "medical_history": {
                    "conditions": conditions,
                    "medications": medications,
                    "allergies": allergies
                }
            }
            
            # Save patient data
            patient_id = save_patient_data(patient_data)
            
            # Get AI recommendation
            with st.spinner("Generating treatment recommendation..."):
                recommendation = get_ai_recommendation(patient_data)
                
            st.success("Recommendation generated successfully!")
            st.markdown("### Treatment Recommendation")
            st.markdown(recommendation)
        else:
            st.error("Please fill in all required fields.")

with tab2:
    st.header("Patient Records")
    
    # Database query for existing records
    conn = sqlite3.connect('medical_records.db')
    patients_df = pd.read_sql_query("SELECT * FROM patients", conn)
    recommendations_df = pd.read_sql_query("SELECT * FROM recommendations", conn)
    conn.close()
    
    if not patients_df.empty:
        selected_patient = st.selectbox(
            "Select Patient",
            patients_df['name'].unique()
        )
        
        if selected_patient:
            patient_data = patients_df[patients_df['name'] == selected_patient].iloc[0]
            recommendations = recommendations_df[
                recommendations_df['patient_id'] == patient_data['id']
            ].sort_values('created_at', ascending=False)
            
            st.subheader("Patient Information")
            st.json(json.loads(patient_data['medical_history']))
            
            st.subheader("Treatment History")
            for _, rec in recommendations.iterrows():
                st.markdown(f"**Recommendation Date:** {rec['created_at']}")
                st.markdown(rec['recommendation'])
                st.markdown("---")
    else:
        st.info("No patient records found. Add a new patient to get started.")

# Footer
st.markdown("---")
st.markdown(
    "⚠️ **Disclaimer:** This system is for research purposes only. "
    "Always consult with qualified healthcare professionals for medical decisions."
)