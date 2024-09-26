import streamlit as st
import speech_recognition as sr
import re
from transformers import pipeline
import base64

# Set page config at the very beginning
st.set_page_config(layout="wide")

# GPT-2 setup
@st.cache_resource
def load_model():
    return pipeline('text-generation', model='gpt2-medium')

generator = load_model()

def generate_invitation(params, max_length, temperature):
    prompt = f"""Generate an engaging invitation for the following event:

Event: {params['event_name']}
Organized by: {params['club_name']}
Date: {params['event_date']}
Venue: {params['venue']}
Chief Guest: {params['chief_guest']}, {params['chief_guest_designation']}
Target Audience: {params['target_audience']}

Event Description: {params['event_description']}
Club Description: {params['club_description']}

The invitation should be {params['tone'].lower()} in tone and include the following points:
{params['additional_notes']}

Invitation:
"""
    
    response = generator(prompt, max_length=max_length, temperature=temperature, num_return_sequences=1)
    generated_text = response[0]['generated_text']
    
    # Extract the generated invitation (everything after "Invitation:")
    invitation = re.split(r'Invitation:', generated_text, flags=re.IGNORECASE)[-1].strip()
    
    return invitation

def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Say your query or 'open invitation form' to proceed.")
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio).lower()
        st.success(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        st.error("Could not understand audio")
        return ""
    except sr.RequestError:
        st.error("Could not request results; check your network connection")
        return ""

def generate_response(query):
    prompt = f"User: {query}\nAssistant:"
    response = generator(prompt, max_length=100, num_return_sequences=1)
    return response[0]['generated_text'].split("Assistant:")[-1].strip()

# Function to generate sound for button click
def get_audio_html(sound_file):
    audio_base64 = base64.b64encode(open(sound_file, "rb").read()).decode()
    return f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}"></audio>'

# Custom CSS for the big button with halo effect
st.markdown("""
<style>
.container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 80vh;
    position: relative;
}
.halo {
    position: absolute;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% {
        transform: scale(1);
        opacity: 1;
    }
    100% {
        transform: scale(1.3);
        opacity: 0;
    }
}
.big-button {
    width: 300px !important;
    height: 300px !important;
    border-radius: 50% !important;
    font-size: 24px !important;
    background-color: #4CAF50 !important;
    color: white !important;
    border: none !important;
    cursor: pointer !important;
    transition: all 0.3s !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    padding: 10px !important;
    position: relative !important;
    z-index: 1 !important;
}
.big-button:hover {
    background-color: #45a049 !important;
    transform: scale(1.05) !important;
}
.stButton>button {
    width: 100%;
    height: 100%;
    border-radius: 50% !important;
}
</style>
""", unsafe_allow_html=True)

# Main app logic
if 'show_form' not in st.session_state:
    st.session_state.show_form = False

if 'play_sound' not in st.session_state:
    st.session_state.play_sound = False

st.title("Event Invitation Generator")

if not st.session_state.show_form:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="container"><div class="halo"></div></div>', unsafe_allow_html=True)
        if st.button("How can I help you?", key="main_button", use_container_width=True):
            st.session_state.play_sound = True
            st.rerun()

    if st.session_state.play_sound:
        st.markdown(get_audio_html("button_click.mp3"), unsafe_allow_html=True)
        st.session_state.play_sound = False
        command = listen_for_command()
        if 'open invitation form' in command:
            st.session_state.show_form = True
            st.rerun()
        else:
            with st.spinner("Generating response..."):
                response = generate_response(command)
            st.text_area("You:", value=command, height=50, disabled=True)
            st.text_area("Assistant:", value=response, height=100, disabled=True)

else:
    with st.form("event_form"):
        col1, col2 = st.columns(2)
        with col1:
            club_name = st.text_input("Name of the Club")
            event_name = st.text_input("Name of the Event")
            event_date = st.date_input("Date of the Event")
            venue = st.text_input("Venue")
            chief_guest = st.text_input("Name of the Chief Guest")
            chief_guest_designation = st.text_input("Designation of the Chief Guest")
        with col2:
            club_description = st.text_area("Brief about the Club")
            event_description = st.text_area("What's the Event about?")
            target_audience = st.text_input("Target Audience")
            tone = st.selectbox("Overall Tone", ["Informative", "Exciting", "Formal", "Casual"])
            additional_notes = st.text_area("Any other points to note?")

        max_length = st.slider("Maximum Length", min_value=100, max_value=500, value=300, step=50)
        temperature = st.slider("Temperature", min_value=0.1, max_value=1.0, value=0.7, step=0.1)

        submitted = st.form_submit_button("Generate Invitation")

    if submitted:
        params = {
            "club_name": club_name,
            "club_description": club_description,
            "event_name": event_name,
            "event_description": event_description,
            "chief_guest": chief_guest,
            "chief_guest_designation": chief_guest_designation,
            "event_date": str(event_date),
            "venue": venue,
            "target_audience": target_audience,
            "tone": tone,
            "additional_notes": additional_notes
        }
        
        with st.spinner("Generating invitation..."):
            invitation = generate_invitation(params, max_length, temperature)
            st.subheader("Generated Invitation:")
            st.markdown(invitation)

        if st.button("Regenerate"):
            with st.spinner("Regenerating invitation..."):
                invitation = generate_invitation(params, max_length, temperature)
                st.subheader("Regenerated Invitation:")
                st.markdown(invitation)

        if st.button("Copy to Clipboard"):
            st.text_area("Copy this text:", value=invitation, height=300)

    if st.button("Start Over"):
        st.session_state.show_form = False
        st.rerun()