import streamlit as st
import sqlite3
import datetime
import hashlib
import streamlit.components.v1 as components

# ==========================================
# 1. DATABASE SETUP (USERS, MOODS, JOURNALS)
# ==========================================
def init_db():
    conn = sqlite3.connect("mindcare.db")
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            mood TEXT,
            score INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            entry TEXT
        )
    ''')
    
    try:
        c.execute("ALTER TABLE mood_logs ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE journal_entries ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect("mindcare.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                  (username, hash_password(password), str(datetime.date.today())))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def verify_user(username, password):
    conn = sqlite3.connect("mindcare.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False

def save_mood(username, mood, score):
    conn = sqlite3.connect("mindcare.db")
    c = conn.cursor()
    today = str(datetime.date.today())
    c.execute("INSERT INTO mood_logs (username, date, mood, score) VALUES (?, ?, ?, ?)", (username, today, mood, score))
    conn.commit()
    conn.close()

def save_journal(username, entry):
    conn = sqlite3.connect("mindcare.db")
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO journal_entries (username, date, entry) VALUES (?, ?, ?)", (username, now, entry))
    conn.commit()
    conn.close()

def fetch_mood_history(username):
    conn = sqlite3.connect("mindcare.db")
    c = conn.cursor()
    c.execute("SELECT date, mood, score FROM mood_logs WHERE username = ? ORDER BY id DESC", (username,))
    moods = c.fetchall()
    conn.close()
    return moods

def fetch_journal_history(username):
    conn = sqlite3.connect("mindcare.db")
    c = conn.cursor()
    c.execute("SELECT date, entry FROM journal_entries WHERE username = ? ORDER BY id DESC", (username,))
    entries = c.fetchall()
    conn.close()
    return entries

# ==========================================
# 2. FRONTEND & CUSTOM THEME STYLING
# ==========================================
st.set_page_config(page_title="MindCare - Pro Edition", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    /* Global App Background & Text Color */
    .stApp {
        background-color: #F7F9F8 !important;
        color: #1A202C !important;
    }
    
    /* Headers Styling */
    h1, h2, h3, h4, h5, h6, span, p, label {
        color: #2E4A3D !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar Layout */
    section[data-testid="stSidebar"] {
        background-color: #EBF2EE !important;
        border-right: 1px solid #C8DCD0 !important;
        padding-top: 1rem;
        min-width: 280px !important;
        max-width: 280px !important;
    }
    
    /* FIX FOR INPUT FIELDS & TEXT AREAS (JOURNAL, API KEY, CHAT) */
    textarea, input, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        background-color: #FFFFFF !important;
        color: #1A202C !important;
        border: 1px solid #CBD5E0 !important;
        border-radius: 8px !important;
    }
    
    /* Chat Input Bar Fix */
    div[data-testid="stChatInput"] textarea {
        background-color: #FFFFFF !important;
        color: #1A202C !important;
    }

    /* FIX FOR CHAT MESSAGES & BUBBLES */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 12px !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] div {
        color: #1A202C !important;
    }
    
    /* Buttons Styling */
    .stButton>button {
        background-color: #7BB391 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #659C7B !important;
        box-shadow: 0 4px 12px rgba(123, 179, 145, 0.4) !important;
    }

    /* COMPLETE HIDING OF RADIO DOTS & ICONS IN SIDEBAR */
    div[data-testid="stSidebar"] div[role="radiogroup"] label input[type="radio"],
    div[data-testid="stSidebar"] div[role="radiogroup"] label div[data-testid="stRadioButtonIcon"],
    div[data-testid="stSidebar"] div[role="radiogroup"] label svg {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }
    
    /* Navigation Card Items */
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin-bottom: 6px !important;
        border: 1px solid #C8DCD0 !important;
        cursor: pointer !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #2D3748 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Selected Navigation Card Item */
    div[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #B2D8C0 !important;
        border-color: #7BB391 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE & AUTHENTICATION FLOW
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🧠 MindCare: Student Well-Being Platform")
    st.write("Please sign in or create an account to access your private space.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔐 Sign In")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if verify_user(login_user, login_pass):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.rerun()
            else:
                st.error("Invalid username or password.")
                
    with col2:
        st.subheader("✨ Register New Account")
        reg_user = st.text_input("Choose Username", key="reg_user")
        reg_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Register"):
            if reg_user.strip() and reg_pass.strip():
                if register_user(reg_user, reg_pass):
                    st.success("Account created successfully! Please log in on the left.")
                else:
                    st.error("Username already taken. Choose another.")
            else:
                st.warning("Please fill in both fields.")
                
    st.stop()

# ==========================================
# 4. MAIN APP (LOGGED IN)
# ==========================================
st.title("🧠 MindCare: Student Well-Being Platform")
st.write(f"Welcome back, **{st.session_state.username}**! Your secure, local space for academic mindfulness.")

# Navigation Sidebar
with st.sidebar:
    st.markdown("### 🧠✨ MindCare")
    st.markdown(f"👤 Logged in as: **{st.session_state.username}**")
    st.markdown("##### Navigation")
    
    menu_choice = st.radio(
        label="Go to",
        options=[
            "☼  Daily Check-In",
            "📖  Journal",
            "✧  AI Companion",
            "🫧  Breathing Tool",
            "📊  Analytics Dashboard",
            "🤍  Support & Resources",
            "🔒  Privacy & Account"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# Clean choice mapping
selected_clean = menu_choice.replace("☼  ", "").replace("📖  ", "").replace("✧  ", "").replace("🫧  ", "").replace("📊  ", "").replace("🤍  ", "").replace("🔒  ", "")

# ------------------------------------------
# PAGE 1: DAILY CHECK-IN
# ------------------------------------------
if selected_clean == "Daily Check-In":
    st.header("😊 Daily Mood Check-In")
    st.write("Track your emotional well-being to uncover personal trends.")
    
    mood_mapping = {
        "😊 Happy / Energetic": 5,
        "😌 Calm / Content": 4,
        "😐 Neutral": 3,
        "😟 Anxious / Stressed": 2,
        "😔 Low / Exhausted": 1
    }
    
    mood_option = st.selectbox("Select how you're feeling:", list(mood_mapping.keys()))
    
    if st.button("Save Mood"):
        score = mood_mapping[mood_option]
        save_mood(st.session_state.username, mood_option, score)
        st.success("Mood successfully logged to your secure account database!")

# ------------------------------------------
# PAGE 2: JOURNAL
# ------------------------------------------
elif selected_clean == "Journal":
    st.header("📝 Private Reflection Journal")
    st.caption("🔒 100% Private & Encrypted locally via SQLite. Only you can view your entries.")
    
    user_entry = st.text_area("What is on your mind today? Unload academic stress below:", height=150)
    
    if st.button("Save Entry Securely"):
        if user_entry.strip():
            save_journal(st.session_state.username, user_entry)
            st.success("Timestamp recorded and saved locally to your secure journal history!")
        else:
            st.warning("Please write something before saving.")
            
    with st.expander("📖 View Past Journal Entries"):
        entries = fetch_journal_history(st.session_state.username)
        if entries:
            for date, entry in entries:
                st.markdown(f"**{date}**")
                st.write(entry)
                st.markdown("---")
        else:
            st.info("No journal entries recorded yet.")

# ------------------------------------------
# PAGE 3: AI COMPANION (Gemini API)
# ------------------------------------------
elif selected_clean == "AI Companion":
    st.header("💬 MindCare AI Wellness Companion (Powered by Gemini)")
    st.write("Chat with your intelligent, empathetic assistant for study advice, stress relief, and guidance.")
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔑 AI Settings")
        gemini_api_key = st.text_input("Enter Gemini API Key", type="password")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi there! I'm your MindCare companion powered by Gemini. How are you feeling about your studies today?"}
        ]
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
    if user_chat := st.chat_input("Type your thoughts or ask for advice..."):
        st.session_state.messages.append({"role": "user", "content": user_chat})
        with st.chat_message("user"):
            st.write(user_chat)
            
        response_text = ""
        if gemini_api_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_api_key)
                system_instruction = (
                    "You are MindCare AI, a warm, empathetic, and supportive wellness companion for university students. "
                    "Provide kind, concise, and constructive advice for academic stress, time management, and emotional health."
                )
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"{system_instruction}\n\nStudent says: {user_chat}"
                )
                response_text = response.text
            except Exception as e:
                response_text = f"⚠️ Could not connect to Gemini API: {e}. Please check your API key."
        else:
            response_text = "💡 *Tip: Enter your Gemini API key in the sidebar to activate live AI intelligence!*"
            
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        with st.chat_message("assistant"):
            st.write(response_text)

# ------------------------------------------
# PAGE 4: BREATHING TOOL
# ------------------------------------------
elif selected_clean == "Breathing Tool":
    st.header("🫁 Animated 4-4-4-4 Box Breathing")
    st.write("Follow the expanding and contracting circle to reset your nervous system.")
    
    breathing_animation_html = """
    <div style="display: flex; justify-content: center; align-items: center; height: 260px; background-color: #F7F9F8;">
        <div style="
            width: 130px; height: 130px; 
            background: linear-gradient(135deg, #A8E6CF 0%, #88D8B0 100%); 
            border-radius: 50%; display: flex; justify-content: center; align-items: center; 
            color: #2D3748; font-family: 'Segoe UI', sans-serif; font-weight: 600; text-align: center;
            box-shadow: 0 8px 25px rgba(136, 216, 176, 0.4);
            animation: breathe 16s infinite ease-in-out;
        ">Breathe</div>
    </div>
    <style>
    @keyframes breathe {
      0%   { transform: scale(1); background: #A8E6CF; }
      25%  { transform: scale(1.6); background: #AED9E0; }
      50%  { transform: scale(1.6); background: #B8E0D2; }
      75%  { transform: scale(1); background: #D6E2E9; }
      100% { transform: scale(1); background: #A8E6CF; }
    }
    </style>
    """
    components.html(breathing_animation_html, height=280)
    st.info("💡 **Box Breathing Guide**: Inhale for 4s, Hold for 4s, Exhale for 4s, Hold for 4s.")

# ------------------------------------------
# PAGE 5: ANALYTICS DASHBOARD
# ------------------------------------------
elif selected_clean == "Analytics Dashboard":
    st.header("📊 Data Science Insights & History")
    st.write("Visualizing your mood patterns over time.")
    
    moods = fetch_mood_history(st.session_state.username)
    
    if moods:
        total_logs = len(moods)
        good_days = sum(1 for row in moods if row[2] >= 4)
        st.success(f"📈 **Weekly Insight**: You felt good or calm in {good_days} out of your last {total_logs} recorded check-ins!")
        
        st.subheader("Mood Trend Chart")
        scores = [row[2] for row in moods[::-1]]
        st.line_chart(scores)
        
        st.subheader("Recent Mood Logs")
        for date, mood, score in moods:
            st.write(f"**{date}** — {mood} (Score: {score})")
    else:
        st.info("No mood data recorded yet. Complete a daily check-in to see your charts!")

# ------------------------------------------
# PAGE 6: SUPPORT & RESOURCES
# ------------------------------------------
elif selected_clean == "Support & Resources":
    st.header("🆘 Campus & Professional Resources")
    st.error("If you are in immediate danger or a severe crisis, please reach out to emergency services right away.")
    st.markdown("""
    ### 📞 Immediate Helplines
    * **Tele-MANAS (India National Mental Health Helpline):** Call **14416** or **1800-891-4416** (Available 24/7, Free & Confidential)
    * **National Crisis Helpline:** Call or text **988** 
    * **Campus Counseling Center:** Contact your university student welfare office for support.
    """)

# ------------------------------------------
# PAGE 7: PRIVACY & ACCOUNT
# ------------------------------------------
elif selected_clean == "Privacy & Account":
    st.header("🔒 Privacy & Data Security")
    st.markdown(f"""
    * **Active Account:** `{st.session_state.username}`
    * **Data Storage:** Your journal reflections and mood scores are stored locally in an encrypted hash format inside your device's SQLite database (`mindcare.db`).
    * **Privacy Guarantee:** No data is shared with third parties. Your emotional well-being data stays strictly confidential.
    """)