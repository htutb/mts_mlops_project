import json
import joblib
import os
import psycopg2
import time
from db import get_connection

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from datetime import datetime

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "toxicity_requests")

MODEL_PATH = os.getenv("MODEL_PATH", "model/model_pipeline.joblib")
TOXIC_THRESHOLD = float(os.getenv("TOXIC_THRESHOLD", "0.3"))

model = joblib.load(MODEL_PATH)

consumer = None
for _ in range(60): # костыль
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id="toxicity_worker",      
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        break
    except NoBrokersAvailable:
        print("Kafka not ready yet, retrying...")
        time.sleep(1)

if consumer is None:
    raise RuntimeError("Kafka not available, giving up")

conn = get_connection()
cursor = conn.cursor()

print("Worker started, waiting for messages...")

try:
    for msg in consumer:
        data = msg.value

        request_id = data["request_id"]
        text = data["text"]
        batch_id = data.get('batch_id')
        created_at = data.get("created_at", datetime.utcnow().isoformat())

        proba = model.predict_proba([text])[0, 1]
        is_toxic = proba >= TOXIC_THRESHOLD

        cursor.execute(
            """
            INSERT INTO predictions (request_id, text, toxic_score, is_toxic, created_at, batch_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (request_id) DO NOTHING
            """,
            (request_id, text, float(proba), bool(is_toxic), created_at, batch_id),
        )

        print(f"{request_id} score={proba:.3f} toxic={is_toxic}")

finally:
    cursor.close()
    conn.close()

