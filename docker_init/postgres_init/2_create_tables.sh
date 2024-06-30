#!/bin/bash
set -e

# Assuming ASSETS is a comma-separated list of asset names

export PGPASSWORD=$POSTGRES_PASSWORD

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
    CREATE TABLE IF NOT EXISTS public.price
    (
        code character varying COLLATE pg_catalog."default" NOT NULL,
        type character varying COLLATE pg_catalog."default" NOT NULL,
        "lastUpdate" character varying COLLATE pg_catalog."default" NOT NULL,
        price character varying COLLATE pg_catalog."default",
        CONSTRAINT price_pkey PRIMARY KEY (code, "lastUpdate", type)
    )

    TABLESPACE pg_default;

    ALTER TABLE IF EXISTS public.price
    OWNER TO $POSTGRES_USER; 
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
    CREATE TABLE IF NOT EXISTS public.excess
    (
        code character varying COLLATE pg_catalog."default" NOT NULL,
        type character varying COLLATE pg_catalog."default" NOT NULL,
        value character varying COLLATE pg_catalog."default",
        CONSTRAINT excess_pkey PRIMARY KEY (code, type)
    )

    TABLESPACE pg_default;

    ALTER TABLE IF EXISTS public.excess
    OWNER TO $POSTGRES_USER; 
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
    CREATE TABLE IF NOT EXISTS public.promotion
    (
        textValue character varying COLLATE pg_catalog."default" NOT NULL,
        "lastUpdate" character varying COLLATE pg_catalog."default" NOT NULL,
        "enabled" boolean,
        CONSTRAINT promo_pkey PRIMARY KEY ("lastUpdate")
    )

    TABLESPACE pg_default;

    ALTER TABLE IF EXISTS public.promotion
    OWNER TO $POSTGRES_USER; 
EOSQL


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
    INSERT INTO public.excess(
        code, type, value)
        VALUES ('USDIRR', 'sell', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
    INSERT INTO public.excess(
	code, type, value)
	VALUES ('USDIRR', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('EURIRR', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('EURIRR', 'sell', '150');
EOSQL


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('TRYIRR', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('TRYIRR', 'sell', '150');
EOSQL


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('GBPIRR', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('GBPIRR', 'sell', '150');
EOSQL


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('CHFIRR', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('CHFIRR', 'sell', '150');
EOSQL


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('AUDIRR', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('AUDIRR', 'sell', '150');
EOSQL


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('CADIRR', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('CADIRR', 'sell', '150');
EOSQL



psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('USDIRRt', 'buy', '200');
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATABASE" <<-EOSQL
   INSERT INTO public.excess(
	code, type, value)
	VALUES ('USDIRRt', 'sell', '150');
EOSQL