import streamlit as st
import pdfplumber
import textstat
import plotly.graph_objects as go
import re
import requests

API_BASE = "http://127.0.0.1:8000"

# ---------------- Session State ----------------
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "uploaded_content" not in st.session_state:
    st.session_state.uploaded_content = None
if "simplified_text" not in st.session_state:
    st.session_state.simplified_text = None

# ---------------- Helper Functions ----------------
def register_user(username, email, password, language, age):
    return requests.post(f"{API_BASE}/register", json={
        "username": username,
        "email": email,
        "password": password,
        "language": language,
        "age": age
    })

def login_user(email, password):
    return requests.post(f"{API_BASE}/login", json={
        "email": email,
        "password": password
    })

def get_profile(token):
    return requests.get(f"{API_BASE}/me", headers={"Authorization": f"Bearer {token}"})

def update_user(token, field, value):
    return requests.put(f"{API_BASE}/update-{field}", json={field: value},
                        headers={"Authorization": f"Bearer {token}"})


# ---------------- Text Simplification ----------------
def simplify_text(text):
    text = re.sub(r'\s+', ' ', text)
    replacements = {
        "utilize": "use",
        "approximately": "about",
        "demonstrate": "show",
        "endeavor": "try",
        "subsequently": "then"
    }
    for k, v in replacements.items():
        text = re.sub(r'\b' + k + r'\b', v, text, flags=re.IGNORECASE)

    simplified_sentences = []
    for sent in re.split(r'(?<=[.!?]) +', text):
        words = sent.split()
        if len(words) > 25:
            mid = len(words)//2
            simplified_sentences.append(" ".join(words[:mid]))
            simplified_sentences.append(" ".join(words[mid:]))
        else:
            simplified_sentences.append(sent)
    return " ".join(simplified_sentences)


# ---------------- Sidebar Menu ----------------
menu = ["Home", "Register", "Login", "Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- Home Page ----------------
if choice == "Home":
    st.markdown("""
    <div style="border: 2px solid #ddd; border-radius: 12px; padding: 20px; text-align: center;">
        <h2>Welcome to Smart Text Simplifier</h2>
        <img src="https://cdn-icons-png.flaticon.com/512/3081/3081680.png" width="300" style="display:block; margin-left:auto; margin-right:auto;"/>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.token:
        st.markdown('<div style="border: 2px solid #ddd; border-radius: 12px; padding: 15px; margin-top:15px;">', unsafe_allow_html=True)
        st.subheader("Upload Text or PDF for Readability & Simplification")
        uploaded_file = st.file_uploader("Upload file (.txt or .pdf)", type=["txt","pdf"])
        
        if uploaded_file:
            content = ""
            if uploaded_file.name.endswith(".txt"):
                content = uploaded_file.read().decode("utf-8")
            elif uploaded_file.name.endswith(".pdf"):
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        content += page.extract_text() + "\n"
            st.session_state.uploaded_content = content
            st.text_area("Preview of Uploaded Content", content, height=200)

        if st.session_state.uploaded_content and st.button("Simplify Text"):
            st.session_state.simplified_text = simplify_text(st.session_state.uploaded_content)
            st.markdown('<div style="border: 2px solid #ddd; border-radius: 12px; padding: 10px; margin-top:15px;">', unsafe_allow_html=True)
            st.subheader("Simplified Text")
            st.text_area("", st.session_state.simplified_text, height=250)
            
            # ---------------- Readability Metrics ----------------
            metrics_text = st.session_state.uploaded_content
            metrics = {
                "Flesch Reading Ease": textstat.flesch_reading_ease(metrics_text),
                "Flesch-Kincaid Grade": textstat.flesch_kincaid_grade(metrics_text),
                "Gunning Fog": textstat.gunning_fog(metrics_text),
                "SMOG Index": textstat.smog_index(metrics_text)
            }

            # Panels
            cols = st.columns(4)
            panel_colors = ["#38bdf8", "#fbbf24", "#34d399", "#f87171"]
            for i, (k,v) in enumerate(metrics.items()):
                with cols[i]:
                    st.markdown(f'''
                    <div style="border:1px solid #ccc; padding:15px; border-radius:10px; background-color:{panel_colors[i]}; text-align:center;">
                    <h3>{k}</h3>
                    <p style="font-size:18px; font-weight:bold;">{v:.2f}</p>
                    </div>
                    ''', unsafe_allow_html=True)

            # Graph
            fig = go.Figure(go.Bar(
                x=list(metrics.keys()), y=list(metrics.values()),
                text=[f"{v:.2f}" for v in metrics.values()],
                marker_color=panel_colors,
                hoverinfo='x+y+text'
            ))
            fig.update_layout(title="Readability Metrics", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

            # Overall Complexity
            fre = metrics["Flesch Reading Ease"]
            if fre >= 60:
                st.success("Overall Text: Easy to Read")
            elif fre >= 30:
                st.warning("Overall Text: Moderate")
            else:
                st.error("Overall Text: Difficult to Read")

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("Please *login* to access text simplification tools.")


# ---------------- Register ----------------
if choice == "Register":
    st.subheader("Create an Account")
    username = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    language = st.selectbox("Preferred Language", ["en", "hi", "fr", "es"])
    age = st.number_input("Age", min_value=10, max_value=100, step=1)
    if st.button("Register"):
        res = register_user(username, email, password, language, age)
        if res.status_code == 200:
            st.success("Account created successfully. Please login now.")
        else:
            st.error(res.json()["detail"])


# ---------------- Login ----------------
if choice == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = login_user(email, password)
        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            profile = get_profile(st.session_state.token)
            if profile.status_code == 200:
                st.session_state.user = profile.json()["user"]
            st.success("Login successful.")
        else:
            st.error(res.json()["detail"])


# ---------------- Dashboard ----------------
if choice == "Dashboard":
    if st.session_state.token and st.session_state.user:
        user = st.session_state.user
        st.subheader("User Profile")
        st.json(user)
        st.markdown("### Update Profile")
        new_username = st.text_input("Username", value=user["username"])
        new_age = st.number_input("Age", min_value=10, max_value=100, value=user["age"], step=1)
        new_language = st.selectbox("Language", ["en", "hi", "fr", "es"], index=["en","hi","fr","es"].index(user.get("language","en")))
        new_content_type = st.selectbox("Content Type", ["text", "file"], index=["text","file"].index(user.get("content_type","text")))
        if st.button("Update Profile"):
            if new_username != user["username"]:
                update_user(st.session_state.token, "username", new_username)
            if new_age != user["age"]:
                update_user(st.session_state.token, "age", new_age)
            if new_language != user.get("language","en"):
                update_user(st.session_state.token, "language", new_language)
            if new_content_type != user.get("content_type","text"):
                update_user(st.session_state.token, "content_type", new_content_type)
            st.success("Profile updated successfully. Refresh to see changes.")
    else:
        st.warning("Please login first to access Dashboard.")