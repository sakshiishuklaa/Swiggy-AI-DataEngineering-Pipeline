import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
import ollama
from dotenv import load_dotenv

load_dotenv()

# Ollama Models & Setup
EMBEDDING_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2"
NEW_REVIEWS = 500
TOK_K = 5
CACHE_FILE = "ollama_review_embeddings.parquet" 

# ==========================================
# 1. SWIGGY UI STYLING & CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #FF5200; }
    h1, h2, h3, p, label { color: white !important; font-family: 'Proxima Nova', Arial, sans-serif; }
    div[data-baseweb="base-input"] { background-color: white !important; border-radius: 30px !important; padding: 5px 15px !important; border: none !important; }
    div[data-baseweb="input"] input { color: #3d4152 !important; font-weight: 500; font-size: 16px; }
    [data-testid="stExpander"] { background-color: white !important; border-radius: 20px !important; border: none !important; padding: 10px; }
    [data-testid="stExpander"] p, [data-testid="stExpander"] span, [data-testid="stExpander"] div { color: #3d4152 !important; }
    .stAlert { border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

try:
    st.image("swiggy_logo.png", width=150)
except:
    pass

st.markdown("<h1>Order food & groceries. Discover best restaurants. Swiggy it!</h1>", unsafe_allow_html=True)
st.caption(f"Searching {NEW_REVIEWS} reviews, answering with local {CHAT_MODEL} model")

# ==========================================
# 2. DATA PROCESSING & BACKEND FUNCTIONS
# ==========================================
def read_reviews_from_snowflake(mfa_token):
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        passcode=mfa_token 
    )
    query = f"SELECT REVIEW_ID, CITY, RATING, COMMENT FROM SWIGGY.STAGING.STG_REVIEWS SAMPLE ({NEW_REVIEWS} ROWS)"
    df = conn.cursor().execute(query).fetch_pandas_all()
    conn.close()
    df.columns = [col.lower() for col in df.columns]
    return df

def embed(texts):
    """Local Ollama embeddings. No internet needed, no API limits."""
    all_embeddings = []
    
    for text in texts:
        safe_text = str(text) if text else "empty"
        # Call local Ollama instance
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=safe_text)
        all_embeddings.append(response['embedding'])
            
    return all_embeddings

@st.cache_data(show_spinner="Embedding reviews locally with Ollama... This happens only once!")
def load_reviews(mfa_token=None):
    if os.path.exists(CACHE_FILE):
        return pd.read_parquet(CACHE_FILE)
    df = read_reviews_from_snowflake(mfa_token)
    df['embedding'] = embed(df['comment'].tolist())
    df.to_parquet(CACHE_FILE)
    return df

def consine_simiarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_similar_reviews(question, df):
    question_vector = embed([question])[0]
    scores = [consine_simiarity(question_vector, rv) for rv in df['embedding']]
    df = df.copy()
    df['score'] = scores
    return df.nlargest(TOK_K, 'score')

def ask_llm(question, top_reviews):
    conext = ""
    for _, row in top_reviews.iterrows():
        conext += f" ({row['city']}, {row['rating']} stars) {row['comment']}\n"

    system_prompt = "Answer ONLY using the customer reviews provided. Be concise. If the reviews don't covert it, say so"
    user_prompt = f"Questions: {question}\n\nReviews:\n{conext}"

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response['message']['content']

# ==========================================
# 3. MAIN UI LOGIC
# ==========================================
needs_download = not os.path.exists(CACHE_FILE)
mfa_token = None

if needs_download:
    st.info("Initial setup: We need to pull data from Snowflake. This only happens once.")
    mfa_token = st.text_input("Enter your 6-digit Snowflake MFA Passcode:", type="password")
    
    if not mfa_token:
        st.warning("Please enter your OTP above to continue.")
        st.stop()

try:
    review_df = load_reviews(mfa_token)
except Exception as e:
    st.error(f"Failed to fetch data. Is your OTP correct? Error: {e}")
    st.stop()

question = st.text_input("Search for restaurant, item, or ask about reviews...", 
                         placeholder="e.g. What are the most common complaints about delivery?")

if question:
    with st.spinner("Asking local AI..."):
        top_reviews = find_similar_reviews(question, review_df)
        answer = ask_llm(question, top_reviews)

        st.markdown(f"**Answer:**")
        st.write(answer)

        with st.expander("View the reviews used to build this answer"):
            st.dataframe(top_reviews[['city', 'rating', 'comment']], hide_index=True)