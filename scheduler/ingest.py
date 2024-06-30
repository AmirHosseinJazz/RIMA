import requests
import json
import pandas as pd
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import requests
from requests_html import HTMLSession


def get_cookie_http():
    url = "https://rimafinance.com"
    response = requests.get(url, timeout=55, verify=False)
    cookies = response.cookies
    for cookie in cookies:
        if cookie.name == "PHPSESSID":
            return cookie.value


# If the cookie is set via JavaScript:
def get_cookie_js():
    session = HTMLSession()
    url = "https://rimafinance.com"
    response = session.get(url, timeout=55, verify=False)
    response.html.render()  # This will execute the JavaScript
    cookies = session.cookies
    for cookie in cookies:
        if cookie.name == "PHPSESSID":
            return cookie.value


def ingest_data():
    cookie_value = get_cookie_http() or get_cookie_js()
    cookies = {
        "PHPSESSID": cookie_value,
    }
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en,en-US;q=0.9,de;q=0.8,sm;q=0.7,fa;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'PHPSESSID=elklm86dd23r97s1mt89usc570',
        "Pragma": "no-cache",
        "Referer": "https://www.rimafinance.com/?size=500",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "X-Requested-With": "XMLHttpRequest",
    }

    response = requests.get(
        "https://www.rimafinance.com/ajax/all_prices",
        headers=headers,
        cookies=cookies,
        timeout=55,
        verify=False,
    )
    last_updated = json.loads(response.text)["meta"]["time"]
    df = pd.DataFrame(json.loads(response.text)["data"]).T
    df = df[["code", "alis", "satis", "tarih"]]
    df = df[~df["code"].isna()]
    df.columns = ["code", "buy", "sell", "lastUpdate"]
    df1 = df[["code", "buy", "lastUpdate"]]
    df1.columns = ["code", "price", "lastUpdate"]
    df1["type"] = "buy"
    df2 = df[["code", "sell", "lastUpdate"]]
    df2.columns = ["code", "price", "lastUpdate"]
    df2["type"] = "sell"
    df1 = df1[["code", "type", "lastUpdate", "price"]]
    df2 = df2[["code", "type", "lastUpdate", "price"]]
    df_total = pd.concat([df1, df2])
    load_dotenv()
    db_name = os.getenv("DATABASE")
    db_user = os.getenv("POSTGRES_USER")
    db_pass = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_table = "public.price"
    conn_params = {
        "dbname": db_name,
        "user": db_user,
        "password": db_pass,
        "host": db_host,
    }
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            tuples = [tuple(x) for x in df_total.to_numpy()]
            cols = ",".join([f'"{i}"' for i in df_total.columns.tolist()])
            query = f"INSERT INTO {db_table} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
            try:
                execute_values(cur, query, tuples)
                conn.commit()
                print(f"Data inserted into {db_table} successfully.")
            except Exception as e:
                print("Error: ", e)
                conn.rollback()
    print(f"Data inserted into {db_table} successfully.")
