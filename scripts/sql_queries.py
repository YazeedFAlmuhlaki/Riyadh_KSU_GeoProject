# this file contins all needed queries.


drop_districts_table = "DROP TABLE IF EXISTS districts;"
drop_restaurants_table = "DROP TABLE IF EXISTS restaurants;"
drop_ksu_gates_table = "DROP TABLE IF EXISTS ksu_gates;"

create_districts_table = """
CREATE TABLE IF NOT EXISTS districts (
    district_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    district_code INT,
    neighborh_code INT,
    district_name_en TEXT,
    district_name_ar TEXT,
    municipality_code INT,
    municipality_no INT,
    has_riyadh BOOLEAN,
    source_objectid INT,
    area_m2 NUMERIC,
    area_km2 NUMERIC,
    geom geometry(MultiPolygon, 32638)
);
"""

insert_into_districts_table = """
INSERT INTO districts (
    district_code,
    neighborh_code,
    district_name_en,
    district_name_ar,
    municipality_code,
    municipality_no,
    has_riyadh,
    source_objectid,
    area_m2,
    area_km2,
    geom
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    ST_GeomFromText(%s, 32638)
);
"""

create_restaurants_table = """
CREATE TABLE IF NOT EXISTS restaurants (
    restaurant_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT,
    categories TEXT,
    address TEXT,
    price TEXT,
    likes NUMERIC, 
    photos NUMERIC,
    tips NUMERIC,
    rating NUMERIC,
    rating_signals NUMERIC,
    price_code NUMERIC,
    post_code TEXT,
    geom geometry(Point,32638)
);
"""


insert_into_restaurants_table = """
INSERT INTO restaurants (
    name,
    categories,
    address,
    price,
    likes, 
    photos,
    tips,
    rating,
    rating_signals,
    price_code,
    post_code,
    geom
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s,
    ST_GeomFromText(%s, 32638)
);
"""

create_ksu_gates_table = """
CREATE TABLE IF NOT EXISTS ksu_gates (
    gate_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gate_name_en TEXT,
    gate_name_ar TEXT,
    campus TEXT,
    road_name_en TEXT,
    road_name_ar TEXT,
    gate_type TEXT,
    access_notes TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geom geometry(Point, 32638)
);
"""

insert_into_ksu_gates_table = """
INSERT INTO ksu_gates (
    gate_name_en,
    gate_name_ar,
    campus,
    road_name_en,
    road_name_ar,
    gate_type,
    access_notes,
    latitude,
    longitude,
    geom
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s,
    ST_GeomFromText(%s, 32638)
);
"""


drop_table_queries = [
    drop_districts_table,
    drop_restaurants_table,
    drop_ksu_gates_table
]

create_table_queries = [
    create_districts_table,
    create_restaurants_table,
    create_ksu_gates_table
]

