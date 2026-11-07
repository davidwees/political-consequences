import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Locking In Predictions",
    page_icon="🔮",
    layout="wide"
)

# --- DATABASE CONNECTION ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- CONFIGURATION DATA ---
PEOPLE = [
    "Pete Hegseth",
    "Greg Bovino",
    "Stephen Miller",
    "Kash Patel",
    "RFK Jr.",
    "Marco Rubio",
    "JD Vance",
    "\"Big Balls\"",
    "Don Jr.",
    "Natalie Harp"
]

DEFAULT_OPTIONS = ["Prison", "Flees country", "Cuts deal"]

# Session state to track if user submitted in this session
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("🔮 Locking In Predictions")
st.markdown("Choose your prediction for each individual below and submit to see aggregate community results!")

# --- FORM SECTION ---
if not st.session_state.submitted:
    with st.form(key="prediction_form"):
        st.subheader("Make Your Predictions")
        user_choices = {}
        
        # Display figures in a 2-column grid to match the original layout
        cols = st.columns(2)
        for idx, person in enumerate(PEOPLE):
            col = cols[idx % 2]
            with col:
                st.write(f"### {person}")
                choice = st.radio(
                    f"Select prediction for {person}:",
                    options=DEFAULT_OPTIONS + ["Other (Custom)"],
                    key=f"radio_{person}",
                    label_visibility="collapsed"
                )
                
                custom_val = ""
                if choice == "Other (Custom)":
                    custom_val = st.text_input(f"Custom outcome for {person}:", key=f"custom_{person}")
                
                user_choices[person] = custom_val.strip() if choice == "Other (Custom)" and custom_val.strip() else choice

        submit_button = st.form_submit_button(label="Submit Predictions", use_container_width=True)

    if submit_button:
        # Prepare records for insertion
        records = [
            {"person_name": person, "prediction": outcome}
            for person, outcome in user_choices.items()
            if outcome
        ]
        
        try:
            supabase.table("predictions").insert(records).execute()
            st.session_state.submitted = True
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit predictions: {e}")

# --- RESULTS SECTION ---
if st.session_state.submitted:
    st.success("🎉 Your predictions have been locked in!")
    st.subheader("📊 Community Predictions Overview")
    
    # Fetch all records
    res = supabase.table("predictions").select("person_name, prediction").execute()
    df = pd.DataFrame(res.data)
    
    if not df.empty:
        cols = st.columns(2)
        for idx, person in enumerate(PEOPLE):
            col = cols[idx % 2]
            person_df = df[df["person_name"] == person]
            
            with col:
                st.markdown(f"### {person}")
                if not person_df.empty:
                    counts = person_df["prediction"].value_counts().reset_index()
                    counts.columns = ["Outcome", "Count"]
                    
                    fig = px.pie(
                        counts, 
                        names="Outcome", 
                        values="Count", 
                        title=f"{person} Outcomes",
                        hole=0.3,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(showlegend=False, margin=dict(t=30, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No predictions logged yet for this figure.")
    
    if st.button("Submit Another Response"):
        st.session_state.submitted = False
        st.rerun()