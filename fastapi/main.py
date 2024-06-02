from fastapi import FastAPI, HTTPException
import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd
import time

from pydantic import BaseModel

app = FastAPI()


@app.get("/asset")
async def get_assets():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    query = f"""
            select DISTINCT("code") from public.price
            """
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    count = cursor.fetchall()

    cursor.close()
    conn.close()
    return pd.DataFrame(count, columns=cols)


@app.get("/price")
async def get_prices():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    query = f"""
            
            SELECT 
            p.code,
            p.type,
            p.price::float + COALESCE(e.value::float, 0) AS final_price,
            p."lastUpdate"
        FROM (
            SELECT 
                code,
                type,
                price,
                "lastUpdate",
                ROW_NUMBER() OVER (PARTITION BY code, type ORDER BY "lastUpdate" DESC) AS rn
            FROM 
                price
        ) p
        LEFT JOIN excess e ON p.code = e.code AND p.type = e.type
        WHERE 
            p.rn = 1;

            """
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    count = cursor.fetchall()

    cursor.close()
    conn.close()
    return pd.DataFrame(count, columns=cols)


class ExcessUpdate(BaseModel):
    code: str
    type: str
    value: float


@app.post("/update_excess")
async def update_excess(update_data: ExcessUpdate):
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    try:
        # Update query
        query = """
        INSERT INTO excess (code, type, value) 
        VALUES (%s, %s, %s)
        ON CONFLICT (code, type) DO UPDATE 
        SET value = EXCLUDED.value;
        """
        cursor.execute(query, (update_data.code, update_data.type, update_data.value))
        conn.commit()
    except Exception as e:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    cursor.close()
    conn.close()
    return {"message": "Excess updated successfully"}
