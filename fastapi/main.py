from fastapi import FastAPI, HTTPException
import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd
import time
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()
# ... other imports and code ...


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://193.151.148.33",
    "http://193.151.148.33:8000",
    "http://istapex.com",
    "http://istapex.com:8000",
    "https://istapex.com",
    "https://istapex.com:8000",
    "http://www.istapex.com",
    "http://www.istapex.com:8000",
    "https://www.istapex.com",
    "https://www.istapex.com:8000",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
       WITH sell_prices AS (
    SELECT
        code,
        CAST(price AS numeric) AS sell_price,
        "lastUpdate",
        ROW_NUMBER() OVER (PARTITION BY code ORDER BY "lastUpdate" DESC) AS rn
    FROM
        price
    WHERE type = 'sell'
),
prev AS (
    SELECT
        code,
        sell_price AS prev_price,
        "lastUpdate"
    FROM
        sell_prices
    WHERE rn = 2
),
current AS (
    SELECT
        code,
        sell_price AS current_price,
        "lastUpdate"
    FROM
        sell_prices
    WHERE rn = 1
),
excess_sums AS (
    SELECT
        code,
        SUM(CASE WHEN type = 'buy' THEN CAST(value AS numeric) ELSE 0 END) AS total_buy,
        SUM(CASE WHEN type = 'sell' THEN CAST(value AS numeric) ELSE 0 END) AS total_sell
    FROM
        excess
    GROUP BY
        code
)
SELECT
    c.code,
    t.type,
    CASE 
        WHEN c.code = 'TRYIRR' THEN 
            CASE t.type
                WHEN 'buy' THEN
                    CASE
                        WHEN MOD(c.current_price + COALESCE(es.total_buy, 0), 10) < 3 THEN FLOOR((c.current_price + COALESCE(es.total_buy, 0)) / 10) * 10
                        WHEN MOD(c.current_price + COALESCE(es.total_buy, 0), 10) BETWEEN 3 AND 7 THEN ROUND((c.current_price + COALESCE(es.total_buy, 0)) / 5) * 5
                        ELSE CEIL((c.current_price + COALESCE(es.total_buy, 0)) / 10) * 10
                    END
                WHEN 'sell' THEN
                    CASE
                        WHEN MOD(c.current_price + COALESCE(es.total_sell, 0), 10) < 3 THEN FLOOR((c.current_price + COALESCE(es.total_sell, 0)) / 10) * 10
                        WHEN MOD(c.current_price + COALESCE(es.total_sell, 0), 10) BETWEEN 3 AND 7 THEN ROUND((c.current_price + COALESCE(es.total_sell, 0)) / 5) * 5
                        ELSE CEIL((c.current_price + COALESCE(es.total_sell, 0)) / 10) * 10
                    END
            END
        ELSE 
            CASE t.type
                WHEN 'buy' THEN ROUND((c.current_price + COALESCE(es.total_buy, 0)) / 10) * 10
                WHEN 'sell' THEN ROUND((c.current_price + COALESCE(es.total_sell, 0)) / 10) * 10
            END
    END AS final_price,
    c."lastUpdate",
    CASE
        WHEN p.prev_price > (c.current_price + COALESCE(es.total_buy, 0) + COALESCE(es.total_sell, 0)) THEN 'positive'
        WHEN p.prev_price < (c.current_price + COALESCE(es.total_buy, 0) + COALESCE(es.total_sell, 0)) THEN 'negative'
        ELSE 'no change'
    END AS change_direction,
    CASE
        WHEN p.prev_price <> (c.current_price + COALESCE(es.total_buy, 0) + COALESCE(es.total_sell, 0)) THEN ROUND(
            CAST(
                ABS((c.current_price + COALESCE(es.total_buy, 0) + COALESCE(es.total_sell, 0)) - p.prev_price) / p.prev_price * 100 AS numeric
            ), 2)
        ELSE 0
    END AS change_percentage
FROM
    current AS c
CROSS JOIN (SELECT DISTINCT type FROM price) AS t
LEFT JOIN prev AS p ON c.code = p.code
LEFT JOIN excess_sums AS es ON c.code = es.code;


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
                slug = code[0][
                    :-3
                ].lower()  # Extract the slug by slicing the 'code' value
                asset_data = assets[code[0]] = {
                    "code": code[0],
                    "lastUpdate": code[3],
                    "change_direction": code[4],
                    "change_percentage": code[5],
                    "prices": {},
                    "slug": slug,  # Add the 'slug' key
                }
            asset_data["prices"][code[1]] = {"type": code[1], "price": code[2]}
        elif code[0].endswith("AYAR"):
            gold_data = gold.get(code[0])
            if not gold_data:
                gold_data = gold[code[0]] = {
                    "code": code[0],
                    "lastUpdate": code[3],
                    "change_direction": code[4],
                    "change_percentage": code[5],
                    "prices": {},
                }
            gold_data["prices"][code[1]] = {"type": code[1], "price": code[2]}
        else:
            parity_data = parity.get(code[0])
            if not parity_data:
                parity_data = parity[code[0]] = {
                    "code": code[0],
                    "lastUpdate": code[3],
                    "change_direction": code[4],
                    "change_percentage": code[5],
                    "prices": {},
                }
            parity_data["prices"][code[1]] = {"type": code[1], "price": code[2]}

    return {
        "assets": list(assets.values()),
        "gold": list(gold.values()),
        "parity": list(parity.values()),
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
async def update_excess(update_data: List[ExcessUpdate]):
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
        # cursor.execute(query, (update_data.code, update_data.type, update_data.value))
        for update in update_data:
            cursor.execute(query, (update.code, update.type, update.value))
        conn.commit()
    except Exception as e:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    cursor.close()
    conn.close()
    return {"message": "Excess updated successfully"}


class Promotion(BaseModel):
    textvalue: str


@app.get("/get_promo_text")
async def get_promo_text():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    query = f"""
            select "textvalue" from public.promotion ORDER BY "lastUpdate" DESC LIMIT 1
            """
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    count = cursor.fetchall()

    cursor.close()
    conn.close()
    # return pd.DataFrame(count, columns=cols)
    result = Promotion(textvalue=count[0][0])
    return result


@app.post("/update_promo_text")
async def update_promo_text(update_data: Promotion):
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
        INSERT INTO promotion ("textvalue", "lastUpdate", "enabled") 
        VALUES (%s, NOW(), 'True')
        """
        cursor.execute(query, (update_data.textvalue,))
        conn.commit()
    except Exception as e:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    cursor.close()
    conn.close()
    return {"message": "Promotion updated successfully"}


@app.post("/promo_toggle")
async def toggle_promo():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    conn = None
    try:
        conn = psycopg2.connect(
            host=host, database=database, user=user, password=password
        )
        cursor = conn.cursor()

        query = """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM public.promotion WHERE "enabled" = True) THEN
                UPDATE public.promotion SET "enabled" = False;
            ELSE
                UPDATE public.promotion SET "enabled" = True;
            END IF;
        END $$;
        """

        cursor.execute(query)
        conn.commit()

        cursor.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn is not None:
            conn.close()

    return {"status": "success"}


class PromoStatus(BaseModel):
    enabled: bool


@app.get("/promo_status")
async def get_promo_status():
    load_dotenv()
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    cursor = conn.cursor()

    query = f"""
            select "enabled" from public.promotion ORDER BY "lastUpdate" DESC LIMIT 1
            """
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]

    count = cursor.fetchall()

    cursor.close()
    conn.close()
    # return pd.DataFrame(count, columns=cols)
    result = PromoStatus(enabled=count[0][0])
    return result


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
    # result = [ExcessUpdate(code=code[0], type=code[1], value=code[2]) for code in count]
    # return result

    result = {}

    for code, type_, value in count:
        if code not in result:
            result[code] = {"code": code, type_: value}
        else:
            result[code][type_] = value

    return result
