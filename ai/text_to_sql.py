import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
import ollama
import json
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. CONFIGURATION & PROMPTS
# ==========================================
MODEL = "llama3.2" 

FORBIDDEN_WORDS = ['drop', 'delete', 'truncate', 'alter', 'update', 'insert', 'create', 'replace', 'grant', 'revoke']

EXAMPLE_QUESTIONS = [
    "Top 10 cities by GMV",
    "Which cuisin has the most orders?",
    "Average delivery time by city, worst first",
    "Cancel rate by payment method"
]

SCHEMA = """
Tables available (Snowflake). Use bare table names, no database or schema prefix.
 
FCT_ORDERS(order_id, order_date, customer_id, restaurant_id, city, cuisine,
           payment_method, order_status, is_delivered, sales_amount, discount,
           delivery_fee, gst, customer_rating, delivery_time_min)
DIM_RESTAURANT(restaurant_id, restaurant_name, city, cuisine, rating, cost_for_two)
DIM_CUSTOMER(customer_id, customer_name, age, age_segment, gender, city)
MART_DAILY_CITY_REVENUNE(order_date, city, orders, cancel_rate, gmv, aov)
MART_RESTAURANT_PERFORMANCE(restaurant_id, restaurant_name, city, cuisine,
                            orders, revenue, avg_customer_rating, cancel_rate)
MART_DELIVERY_SLA(city, order_hour, delivered_orders, p50_delivery_min, late_rate)
 
Note: gmv means delivered revenue. Prefer the MART_ tables when they fit the question.
"""
 
SYSTEM_PROMPT = f"""
You are a Snowflake SQL expert. Write ONE SELECT query that answers the question.
 
Rules:
- SELECT queries only, never modify data.
- Use bare table names (FCT_ORDERS, not SWIGGY.MARTS.FCT_ORDERS).
- Add a LIMIT of 100 or less, unless the question asks for a single total.
- Reply as JSON in this exact format: {{"sql": "your query here"}}
 
{SCHEMA}
"""

# ==========================================
# 2. SWIGGY UI STYLING & CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    /* Main Orange Background */
    .stApp { background-color: #FF5200; }
    
    /* Global Text Styling (White) */
    h1, h2, h3, p, label { color: white !important; font-family: 'Proxima Nova', Arial, sans-serif; }
    
    /* White rounded search/input bar */
    div[data-baseweb="base-input"] { 
        background-color: white !important; 
        border-radius: 30px !important; 
        padding: 5px 15px !important; 
        border: none !important; 
    }
    
    /* Dark text inside the input bar so users can read it */
    div[data-baseweb="input"] input { 
        color: #3d4152 !important; 
        font-weight: 500; 
        font-size: 16px; 
    }
    
    /* Dataframe and code block styling */
    [data-testid="stExpander"], [data-testid="stCodeBlock"] { 
        background-color: white !important; 
        border-radius: 20px !important; 
        border: none !important; 
        padding: 10px; 
    }
    
    /* Sidebar Background Styling */
    [data-testid="stSidebar"] {
        background-color: #e64a00;
    }
    
    /* Rounded corners for alert boxes */
    .stAlert { border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

try:
    # Make sure 'swiggy_logo.png' is in your folder
    st.image("swiggy_logo.png", width=150)
except:
    pass

st.markdown("<h1>Order food & groceries. Discover best restaurants. Swiggy it!</h1>", unsafe_allow_html=True)
st.caption(f"Ask in English about your Swiggy Data. Local {MODEL} writes the SQL, Snowflake runs it.")

# ==========================================
# 3. BACKEND FUNCTIONS
# ==========================================
@st.cache_resource
def get_connection(mfa_token):
    """Establishes Snowflake connection using the provided OTP."""
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="MARTS",
        role="DBT_ROLE",
        passcode=mfa_token
    )

def generate_sql(question):
    """Calls local Ollama AI to generate SQL based on the prompt."""
    response = ollama.chat(
        model=MODEL,
        format='json',
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )
    
    answer = response['message']['content']
    
    try:
        sql = json.loads(answer).get("sql", "")
    except json.JSONDecodeError:
        clean_answer = answer.replace("```json", "").replace("```", "").strip()
        sql = json.loads(clean_answer).get("sql", "")

    # Clean up any residual schema prefixes (Updated to Swiggy)
    sql = sql.replace("SWIGGY.MARTS.", "").replace("SWIGGY.", "")
    return sql.strip().rstrip(";")

def is_safe(sql):
    """Ensures the generated SQL is a safe SELECT statement."""
    lowered = sql.lower()
    if not lowered.startswith("select") and not lowered.startswith("with"):
        return False
    for word in FORBIDDEN_WORDS:
        if word in lowered:
            return False
    return True

def run_query(sql, token):
    """Executes the query on Snowflake."""
    conn = get_connection(token)
    cursor = conn.cursor()
    return cursor.execute(sql).fetch_pandas_all()

# ==========================================
# 4. STREAMLIT UI LOGIC
# ==========================================
with st.sidebar:
    st.header("Authentication")
    mfa_token = st.text_input("Snowflake MFA Passcode", type="password", placeholder="Enter 6-digit OTP")
    
    st.markdown("---")
    
    st.header("Example Questions")
    for q in EXAMPLE_QUESTIONS:
        st.markdown(f" - {q}")

# Main Chat Interface
question = st.text_input("Search for restaurant, item or more...", 
                         placeholder="e.g. Top 10 cities by GMV")

if question:
    # Stop if OTP is missing
    if not mfa_token:
        st.warning("Please enter your 6-digit Snowflake MFA passcode in the sidebar first.")
    else:
        with st.spinner("Generating SQL locally with Ollama..."):
            sql = generate_sql(question)
        
        st.code(sql, language="sql")

        if not is_safe(sql):
            st.error("The generated SQL is not safe to run. Please modify your question.")
        else:
            try:
                with st.spinner("Executing query on Snowflake..."):
                    df = run_query(sql, mfa_token)
                    
                st.success(f"{len(df)} rows returned")
                st.dataframe(df, hide_index=True)

                # Auto-generate bar chart if data shape allows
                if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                    st.bar_chart(df, x=df.columns[0], y=df.columns[1])

            except Exception as e:
                st.error(f"Error running query: {e}")