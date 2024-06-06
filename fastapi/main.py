from fastapi import FastAPI, HTTPException
import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd
import time

from pydantic import BaseModel

app = FastAPI()


class Asset(BaseModel):
    code: str


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
    # return pd.DataFrame(count, columns=cols)
    result = [Asset(code=code[0]) for code in count]
    return result


class Price(BaseModel):
    code: str
    type: str
    price: float
    lastUpdate: str
    change_direction: str
    change_percentage: float


@app.get("/pricev2")
async def get_prices():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    query = f"""
    WITH prev AS (
        SELECT
            code,
            type,
            CAST(price AS numeric) AS prev_price,
            "lastUpdate"
        FROM (
            SELECT
                code,
                type,
                price,
                "lastUpdate",
                ROW_NUMBER() OVER (PARTITION BY code, type ORDER BY "lastUpdate" DESC) AS rn
            FROM
                price
        ) AS subquery
        WHERE subquery.rn = 2
    ),
    current AS (
        SELECT
            code,
            type,
            CAST(price AS numeric) AS current_price,
            "lastUpdate"
        FROM (
            SELECT
                code,
                type,
                price,
                "lastUpdate",
                ROW_NUMBER() OVER (PARTITION BY code, type ORDER BY "lastUpdate" DESC) AS rn
            FROM
                price
        ) AS subquery
        WHERE subquery.rn = 1
    )
    SELECT
        current.code,
        current.type,
        current.current_price AS final_price,
        current."lastUpdate",
        CASE
            WHEN prev.prev_price > current.current_price THEN 'positive'
            WHEN prev.prev_price < current.current_price THEN 'negative'
            ELSE 'no change'
        END AS change_direction,
        CASE
            WHEN prev.prev_price <> current.current_price THEN ROUND(
                CAST(
                    ABS(current.current_price - prev.prev_price)/ prev.prev_price* 100 AS numeric), 2)
            ELSE 0
        END AS change_percentage
        FROM
            current
        LEFT JOIN prev ON current.code = prev.code AND current.type = prev.type;
        """

    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    count = cursor.fetchall()

    cursor.close()
    conn.close()

    
    assets = {}
    gold = {}
    parity = {}

    for code in count:
        if code[0].endswith("IRR"):
            asset_data = assets.get(code[0])
            if not asset_data:
                slug = code[0][:-3].lower()  # Extract the slug by slicing the 'code' value
                asset_data = assets[code[0]] = {
                    "code": code[0],
                    "lastUpdate": code[3],
                    "change_direction": code[4],
                    "change_percentage": code[5],
                    "prices": {},
                    "slug": slug  # Add the 'slug' key
                }
            asset_data["prices"][code[1]] = {
                "type": code[1],
                "price": code[2]
            }
        elif code[0].endswith("AYAR"):
            gold_data = gold.get(code[0])
            if not gold_data:
                gold_data = gold[code[0]] = {
                    "code": code[0],
                    "lastUpdate": code[3],
                    "change_direction": code[4],
                    "change_percentage": code[5],
                    "prices": {}
                }
            gold_data["prices"][code[1]] = {
                "type": code[1],
                "price": code[2]
            }
        else:
            parity_data = parity.get(code[0])
            if not parity_data:
                parity_data = parity[code[0]] = {
                    "code": code[0],
                    "lastUpdate": code[3],
                    "change_direction": code[4],
                    "change_percentage": code[5],
                    "prices": {}
                }
            parity_data["prices"][code[1]] = {
                "type": code[1],
                "price": code[2]
            }

    return {
            "assets": list(assets.values()),
            "gold": list(gold.values()),
            "parity": list(parity.values())
        }

    # result = [
    #     Price(
    #         code=code[0],
    #         type=code[1],
    #         price=code[2],
    #         lastUpdate=code[3],
    #         change_direction=code[4],
    #         change_percentage=code[5]
    #     )
    #     for code in count
    # ]
    # return result




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
            current.code,
            current.type,
            CAST(CAST(current.price AS float) + COALESCE(CAST(current_excess.value AS float), 0) AS numeric) AS final_price,
            current."lastUpdate",
            ROUND(
                CAST(
                    (CAST(current.price AS float) - COALESCE(CAST(prev.price AS float), CAST(current.price AS float)))
                    / COALESCE(CAST(prev.price AS float), 1)
                    AS numeric
                ), 2
            ) AS change_percentage
        FROM (
            SELECT 
                code,
                type,
                price,
                "lastUpdate",
                ROW_NUMBER() OVER (PARTITION BY code, type ORDER BY "lastUpdate" DESC) AS rn
            FROM 
                price
            WHERE code like '%IRR%'
        ) AS current
        LEFT JOIN excess AS current_excess ON current.code = current_excess.code AND current.type = current_excess.type
        LEFT JOIN (
            SELECT 
                code,
                type,
                price,
                "lastUpdate",
                ROW_NUMBER() OVER (PARTITION BY code, type ORDER BY "lastUpdate" DESC) AS rn
            FROM 
                price
        ) AS prev ON current.code = prev.code AND current.type = prev.type AND prev.rn = 2
        WHERE 
            current.rn = 1;



            """
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    count = cursor.fetchall()

    cursor.close()
    conn.close()
    result = [
        Price(
            code=code[0],
            type=code[1],
            price=code[2],
            lastUpdate=code[3],
            change_percentage=code[4],
        )
        for code in count
    ]
    return result


@app.get("/parity")
async def get_parities():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    query = f"""
            SELECT
            current.code,
            current.type,
            CAST(CAST(current.price AS float) + COALESCE(CAST(current_excess.value AS float), 0) AS numeric) AS final_price,
            current."lastUpdate",
            ROUND(
                CAST(
                    (CAST(current.price AS float) - COALESCE(CAST(prev.price AS float), CAST(current.price AS float)))
                    / COALESCE(CAST(prev.price AS float), 1)
                    AS numeric
                ), 2
            ) AS change_percentage
        FROM (
            SELECT 
                code,
                type,
                price,
                "lastUpdate",
                ROW_NUMBER() OVER (PARTITION BY code, type ORDER BY "lastUpdate" DESC) AS rn
            FROM 
                price
            WHERE code not like '%IRR%'
        ) AS current
        LEFT JOIN excess AS current_excess ON current.code = current_excess.code AND current.type = current_excess.type
        LEFT JOIN (
            SELECT 
                code,
                type,
                price,
                "lastUpdate",
                ROW_NUMBER() OVER (PARTITION BY code, type ORDER BY "lastUpdate" DESC) AS rn
            FROM 
                price
        ) AS prev ON current.code = prev.code AND current.type = prev.type AND prev.rn = 2
        WHERE 
            current.rn = 1;



            """
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    count = cursor.fetchall()

    cursor.close()
    conn.close()
    # return pd.DataFrame(count, columns=cols)
    result = [
        Price(
            code=code[0],
            type=code[1],
            price=code[2],
            lastUpdate=code[3],
            change_percentage=code[4],
        )
        for code in count
    ]
    return result



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


@app.get("/excess")
async def get_excess():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    query = f"""
            select * from public.excess
            """
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    count = cursor.fetchall()

    cursor.close()
    conn.close()
    # return pd.DataFrame(count, columns=cols)
    result = [ExcessUpdate(code=code[0], type=code[1], value=code[2]) for code in count]
    return result