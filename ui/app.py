import json
import os
import time
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime

from kafka import KafkaProducer
from db import get_connection

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "toxicity_requests")

POLL_TIMEOUT_SEC = 10      
POLL_INTERVAL_SEC = 0.3    

@st.cache_resource
def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=20,
    )


def fetch_prediction_by_request_id(cur, request_id: str):
    cur.execute(
        """
        SELECT request_id, text, toxic_score, is_toxic, created_at
        FROM predictions
        WHERE request_id = %s
        """,
        (request_id,),
    )
    return cur.fetchone()


def fetch_latest_predictions(cur, limit: int = 20):
    cur.execute(
        """
        SELECT request_id, toxic_score, is_toxic, created_at, left(text, 120) as text_preview
        FROM predictions
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return cur.fetchall()


def fetch_batch_predictions(cur, batch_id: str, limit: int = 2000):
    cur.execute(
        """
        SELECT request_id, toxic_score, is_toxic, created_at, left(text, 200) as text_preview
        FROM predictions
        WHERE batch_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (batch_id, limit),
    )
    return cur.fetchall()


st.set_page_config(page_title="Toxicity Detector", layout="wide")
st.title("Toxicity Detector")

producer = get_producer()


# SINGLE TEXT INFERENCE

st.header("Single text")

text_input = st.text_area("Enter text", height=120, placeholder="Type text here...")

col1, col2 = st.columns([1, 2])
with col1:
    do_predict = st.button("Predict", type="primary")

if do_predict:
    if not text_input.strip():
        st.warning("Please enter non-empty text.")
    else:
        request_id = str(uuid.uuid4())
        payload = {
            "request_id": request_id,
            "text": text_input,
            "created_at": datetime.utcnow().isoformat(),
        }
        producer.send(KAFKA_TOPIC, payload)
        producer.flush()

        st.info(f"Sent to Kafka. request_id={request_id}")

        conn = get_connection()
        cur = conn.cursor()

        start = time.time()
        row = None
        while time.time() - start < POLL_TIMEOUT_SEC:
            row = fetch_prediction_by_request_id(cur, request_id)
            if row is not None:
                break
            time.sleep(POLL_INTERVAL_SEC)

        cur.close()
        conn.close()

        if row is None:
            st.warning("No result yet. Check 'Latest predictions'.")
        else:
            _, full_text, score, is_toxic, created_at = row
            st.success("Result received!")
            st.write(
                {
                    "request_id": request_id,
                    "toxic_score": float(score),
                    "is_toxic": bool(is_toxic),
                    "created_at": str(created_at),
                }
            )
            st.text_area("Text", value=full_text, height=120)


st.divider()


# CSV FILE INFERENCE

st.header("Batch CSV")

st.markdown(
    """
**CSV requirement:** must contain a text column named **`text`** or **`comment_text`**.  
"""
)

uploaded = st.file_uploader("Upload CSV", type=["csv"])

batch_col1, batch_col2 = st.columns([1, 2])
with batch_col1:
    send_batch = st.button("Send batch to Kafka")

if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.write("Preview:", df.head(5))

    text_col = None
    if "text" in df.columns:
        text_col = "text"
    elif "comment_text" in df.columns:
        text_col = "comment_text"

    if text_col is None:
        st.error("CSV must have a column named 'text' (or 'comment_text').")
    else:
        st.success(f"Using column: {text_col}")
        df[text_col] = df[text_col].fillna("").astype(str)

        if send_batch:
            batch_id = str(uuid.uuid4())
            sent = 0

            progress = st.progress(0)
            n = len(df)

            for i, txt in enumerate(df[text_col].tolist()):
                payload = {
                    "request_id": str(uuid.uuid4()),
                    "batch_id": batch_id,
                    "text": txt,
                    "created_at": datetime.utcnow().isoformat(),
                }
                producer.send(KAFKA_TOPIC, payload)
                sent += 1

                if n > 0 and (i % 200 == 0 or i == n - 1):
                    progress.progress(min(1.0, (i + 1) / n))

            producer.flush()
            st.success(f"Batch sent: {sent} messages. batch_id={batch_id}")

            st.session_state["last_batch_id"] = batch_id


# batch results viewer
st.subheader("Batch results")
batch_id = st.text_input("batch_id", value=st.session_state.get("last_batch_id", ""))

if st.button("Load batch results"):
    if not batch_id.strip():
        st.warning("Enter batch_id.")
    else:
        conn = get_connection()
        cur = conn.cursor()
        rows = fetch_batch_predictions(cur, batch_id=batch_id)
        cur.close()
        conn.close()

        if not rows:
            st.warning("No rows found for this batch_id yet.")
        else:
            out = pd.DataFrame(
                rows,
                columns=["request_id", "toxic_score", "is_toxic", "created_at", "text_preview"],
            )
            st.dataframe(out, use_container_width=True)


st.divider()


st.header("Latest predictions")

limit = st.slider("How many rows", min_value=5, max_value=100, value=20, step=5)

if st.button("Refresh latest"):
    conn = get_connection()
    cur = conn.cursor()
    rows = fetch_latest_predictions(cur, limit=limit)
    cur.close()
    conn.close()

    if not rows:
        st.info("No predictions yet. Send a message first.")
    else:
        latest = pd.DataFrame(
            rows,
            columns=["request_id", "toxic_score", "is_toxic", "created_at", "text_preview"],
        )
        st.dataframe(latest, use_container_width=True)