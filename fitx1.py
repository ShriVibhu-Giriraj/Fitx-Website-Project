import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pytz

# Database connection parameters hardcoded for simplicity
db_config = {
    'host': 'database-1.cj4yawsiksva.ap-southeast-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'admin12345',
    'database': 'Fitxtrial'
}

def connect_to_db():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

def get_uid_by_name(name):
    """Fetches an existing user's UID by their name."""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(buffered=True) as cursor:
                cursor.execute("SELECT `U-id` FROM daily_main_sheet WHERE `Name` = %s LIMIT 1", (name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Error as e:
            st.error(f"Error fetching user by name: {e}")
        finally:
            conn.close()

def create_new_user(name):
    """Creates a new user with a unique UID."""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(`U-id`) FROM daily_main_sheet")
                max_uid = cursor.fetchone()[0] or 0
                new_uid = max_uid + 1
                cursor.execute("INSERT INTO daily_main_sheet (`U-id`, `Name`) VALUES (%s, %s)", (new_uid, name))
                conn.commit()
                return new_uid
        except Error as e:
            st.error(f"Error creating a new user: {e}")
        finally:
            conn.close()

def insert_or_update_record(date, uid, morning=None, afternoon=None, night=None, workout=None, healthify=None, daily_update=None):
    """Inserts or updates the user's record for the day with given responses."""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO daily_main_sheet (`Date`, `U-id`, `Morning`, `Afternoon`, `Night`, `Workout`, `Healthify`, `Daily Update`) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                `Morning`=VALUES(`Morning`), 
                `Afternoon`=VALUES(`Afternoon`), 
                `Night`=VALUES(`Night`),
                `Workout`=VALUES(`Workout`), 
                `Healthify`=VALUES(`Healthify`), 
                `Daily Update`=VALUES(`Daily Update`);
                """
                vals = (date, uid, morning, afternoon, night, workout, healthify, daily_update)
                cursor.execute(query, vals)
                conn.commit()
        except Error as e:
            st.error(f"Error updating record: {e}")
        finally:
            conn.close()

# Streamlit UI setup
st.title('Daily Input Form')

if 'uid' not in st.session_state:
    st.session_state.uid = None

user_type = st.radio("Are you a new or returning user?", ['New', 'Returning'])

if user_type == 'New':
    name = st.text_input("Enter your name for new user:")
    if name:
        st.session_state.uid = create_new_user(name)
        st.success(f"Welcome, {name}! Your UID is: {st.session_state.uid}")

elif user_type == 'Returning':
    name = st.text_input("Enter your name for returning user:")
    if name:
        retrieved_uid = get_uid_by_name(name)
        if retrieved_uid:
            st.session_state.uid = retrieved_uid
            st.success(f"Welcome back, {name}! Your UID is: {st.session_state.uid}")
        else:
            st.error("Name not found. Please check your input or choose 'New' to register.")

# Adjusting for Indian Standard Time (IST)
timezone = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(timezone).time()

if st.session_state.uid:
    date = datetime.now(timezone).strftime('%Y-%m-%d')
    st.text(f"Today's date is: {date}")

    # Time-based questions
    if current_time.hour < 11:
        st.session_state.morning = st.radio("Morning", ['Yes', 'No'], key='morning_radio')
    elif 11 <= current_time.hour < 18:
        st.session_state.afternoon = st.radio("Afternoon", ['Yes', 'No'], key='afternoon_radio')
    else:
        st.session_state.night = st.radio("Night", ['Yes', 'No'], key='night_radio')

    # General questions
    st.session_state.workout = st.radio("Workout", ['Yes', 'No'], key='workout_radio')
    st.session_state.healthify = st.radio("Healthify", ['Yes', 'No'], key='healthify_radio')
    st.session_state.daily_update = st.radio("Daily Update", ['Yes', 'No'], key='daily_update_radio')

    if st.button('Submit Responses'):
        insert_or_update_record(
            date, st.session_state.uid, 
            morning=st.session_state.get('morning'), 
            afternoon=st.session_state.get('afternoon'), 
            night=st.session_state.get('night'), 
            workout=st.session_state.get('workout'), 
            healthify=st.session_state.get('healthify'), 
            daily_update=st.session_state.get('daily_update')
        )
        st.success('Record updated successfully!')
