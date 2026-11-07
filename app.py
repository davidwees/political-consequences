import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
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

DEFAULT_OPTIONS = ["Prison", "Flees country", "Cuts deal", "Other"]

# Explicit color mapping for consistent pie chart colors across all figures
COLOR_MAP = {
    "Prison": "#EF553B",        # Red / Coral
    "Flees country": "#636EFA", # Blue
    "Cuts deal": "#00CC96",     # Teal / Green
    "Other": "#AB63FA"          # Purple
}

# Helper function to extract individual avatars from sprite sheet
@st.cache_data
def load_avatars():
    sprite_sheet = Image.open("figures_spritesheet.png")
    avatars = {}
    for idx, name in enumerate(PEOPLE):
        row = idx // 2
        col = idx % 2
        # Each tile is 150x150
        crop_box = (col * 150, row * 150, (col + 1) * 150, (row + 1) * 150)
        avatars[name] = sprite_sheet.crop(crop_box)
    return avatars

avatars = load_avatars()

# Track view mode in session state ("form" or "results")
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "form"

st.title("🔮 Locking In Predictions")
st.markdown("Choose your prediction for each individual below or view the live community results!")

# --- FORM SECTION ---
if st.session_state.view_mode == "form":
    with st.form(key="prediction_form"):
        st.subheader("Make Your Predictions")
        user_choices = {}
        
        # Display in 2 columns
        cols = st.columns(2)
        for idx, person in enumerate(PEOPLE):
            col = cols[idx % 2]
            with col:
                img_col, input_col = st.columns([1, 2])
                with img_col:
                    st.image(avatars[person], width=120)
                with input_col:
                    st.write(f"### {person}")
                    choice = st.radio(
                        f"Select prediction for {person}:",
                        options=DEFAULT_OPTIONS,
                        key=f"radio_{person}",
                        label_visibility="collapsed"
                    )
                    
                    user_choices[person] = choice
                st.divider()

        submit_button = st.form_submit_button(label="Submit Predictions", width="stretch")

    if submit_button:
        records = [
            {"person_name": person, "prediction": outcome}
            for person, outcome in user_choices.items()
            if outcome
        ]
        try:
            supabase.table("predictions").insert(records).execute()
            st.session_state.view_mode = "results"
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit predictions: {e}")

    # "See Results" button to view results without submitting
    if st.button("📊 See Results Without Submitting", width="stretch"):
        st.session_state.view_mode = "results"
        st.rerun()

# --- RESULTS SECTION ---
elif st.session_state.view_mode == "results":
    st.subheader("📊 Community Predictions Overview")
    
    res = supabase.table("predictions").select("person_name, prediction").execute()
    df = pd.DataFrame(res.data)
    
    if not df.empty:
        cols = st.columns(2)
        for idx, person in enumerate(PEOPLE):
            col = cols[idx % 2]
            person_df = df[df["person_name"] == person]
            
            with col:
                head_col, chart_col = st.columns([1, 2])
                with head_col:
                    st.image(avatars[person], width=100)
                    st.markdown(f"**{person}**")
                with chart_col:
                    if not person_df.empty:
                        counts = person_df["prediction"].value_counts().reset_index()
                        counts.columns = ["Outcome", "Count"]
                        
                        fig = px.pie(
                            counts, 
                            names="Outcome", 
                            values="Count", 
                            hole=0.3,
                            color="Outcome",
                            color_discrete_map=COLOR_MAP
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=200)
                        
                        st.plotly_chart(
                            fig, 
                            key=f"chart_{person}", 
                            width="stretch"
                        )
                    else:
                        st.info("No predictions yet.")
                st.divider()
    else:
        st.info("No predictions submitted yet.")

    # Return button to go back to the form
    if st.button("✏️ Back to Predictions Form", width="stretch"):
        st.session_state.view_mode = "form"
        st.rerun()