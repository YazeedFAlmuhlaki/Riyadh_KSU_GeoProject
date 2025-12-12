
# Riyadh_KSU_GeoProject

Spatial data science mini-project built around **Riyadh districts**, **restaurants**, and **King Saud University (KSU) gates**, using:

- PostgreSQL + **PostGIS** (spatial database)
- Python (GeoPandas / Pandas / psycopg2)
- Streamlit (exploratory web UI)

The goal is to practice working like a real spatial data scientist:

1. Load GeoJSON data into a spatial database.
2. Compute geometry-aware features (areas, distances, buffers).
3. Join multiple spatial layers (districts, restaurants, KSU gates).
4. Serve the results to an interactive Streamlit app.

---

## 1. Data layers

### 1.1 Districts (`districts` table)

Polygon layer of Riyadh districts (or a sample).

Key columns:

- `district_id` – surrogate key (identity)
- `district_code` – district number from source data
- `neighborh_code` – source neighbourhood code
- `district_name_en` – district name (EN)
- `district_name_ar` – district name (AR)
- `municipality_code`, `municipality_no` – municipality attributes
- `has_riyadh` – boolean flag from original `HASRIYADH` field (0/1 → False/True)
- `area_m2` – area in square metres (computed in EPSG:32638)
- `area_km2` – area in square kilometres
- `geom` – `geometry(MultiPolygon, 32638)`

### 1.2 Restaurants (`restaurants` table)

Point layer of restaurants / cafes in Riyadh (sample around the chosen district).

Important columns:

- `restaurant_id` – surrogate key (identity)
- `name` – restaurant name (Arabic / English / mixed)
- `categories` – Foursquare-style categories (e.g. *Coffee Shop, Bakery*)
- `address` – text address
- `price` – price level (text from source)
- `likes`, `photos`, `tips` – engagement metrics (numeric)
- `rating` – restaurant rating (0–10)
- `rating_signals` – number of ratings
- `price_code` – numeric price level
- `post_code` – postal code (string, may be null)
- `geom` – `geometry(Point, 32638)` (reprojected from WGS84 lat/lon)

### 1.3 KSU gates (`ksu_gates` table)

Hand-crafted CSV of important KSU gates (main campus, female campus, medical city).

Columns:

- `gate_id` – identity key
- `gate_name_en` / `gate_name_ar` – gate name in EN / AR
- `campus` – logical campus (`main_male`, `female`, `medical_city`)
- `road_name_en` / `road_name_ar` – adjacent road
- `gate_type` – `main_iconic`, `vehicle_main`, `vehicle_cars`, `vehicle_buses`, …
- `access_notes` – text notes (what this gate is used for)
- `latitude`, `longitude` – WGS84 coordinates
- `geom` – `geometry(Point, 32638)` (computed from lat/long)

---

## 2. Analysis layer

Analysis SQL is kept in `scripts/sql_analysis_queries.py`.

Main queries:

### 2.1 District-level stats: `district_stats_query`

For each district, compute:

- number of restaurants inside the district (`restaurant_count`)
- mean rating (`avg_rating`)
- restaurant density (`restaurants_per_km2`)

Logic:

```sql
SELECT
    district_id,
    district_name_en,
    district_name_ar,
    area_km2,
    COUNT(restaurant_id) AS restaurant_count,
    AVG(rating) AS avg_rating,
    (COUNT(restaurant_id) / area_km2) AS restaurants_per_km2,
    districts.geom AS district_geom
FROM districts
INNER JOIN restaurants
    ON ST_Contains(districts.geom, restaurants.geom)
GROUP BY 1,2,3,4,8;
```

Loaded into a **GeoDataFrame** via `geopandas.read_postgis`.

---

### 2.2 Gates with districts: `gates_with_district_query`

Attach each KSU gate to the district polygon that contains it:

- gate attributes (`gate_id`, `gate_name_en`, `campus`, `gate_type`, `access_notes`, `gate_geom`)
- matching district attributes (`district_id`, `district_name_en`, `district_name_ar`)

Uses `ST_Contains(districts.geom, ksu_gates.geom)` with `LEFT JOIN` so gates outside any district (if any) still appear.

---

### 2.3 Gate–restaurant distances: `gate_restaurant_distances_query`

Compute the distance from **every gate to every restaurant**:

- `dist_km = ST_Distance(ksu_gates.geom, restaurants.geom) / 1000`

This is loaded as a plain Pandas DataFrame and used to:

- find the **nearest restaurant** per gate (`get_nearest_restaurant_per_gate`)
- filter by distance thresholds if needed.

---

### 2.4 Restaurants within 1 km of each gate: `gate_restaurants_1km_query`

For each gate, summarise all restaurants within 1 km buffer:

- `restaurants_1km` – count of restaurants where `ST_DWithin(geom, geom, 1000)` is true
- `avg_rating_1km` – mean rating of those restaurants

Resulting DataFrame is joined with the “nearest restaurant” table to build the **gate summary**.

---

### 2.5 Gate summary table (`gate_summary_df`)

This table is what the Streamlit app displays.

Each **row = one gate** and includes:

- Gate attributes:
  - `gate_id`, `gate_name_en`, `gate_name_ar`
  - `campus`, `gate_type`, `district_name_en`
- Nearest restaurant:
  - `restaurant_name`
  - `rating`
  - `categories`
  - `dist_km` – distance to that restaurant (km)
- Neighbourhood stats:
  - `restaurants_1km` – **how many restaurants** within 1 km of the gate
  - `avg_rating_1km` – average rating of those restaurants

Example interpretation:

> For Gate X: there are 35 restaurants within 1 km;  
> the closest one is *Nutellaplus* (0.158 km away) with rating 7.5.

---

## 3. Project structure

```text
Riyadh_KSU_GeoProject/
├── config/
│   |
│   └── db.cfg               # add it 
├── data/
│                  
│   
├── scripts/
│   ├── create_tables.py     # create PostGIS tables
│   ├── etl.py               # load GeoJSON/CSV into PostGIS
│   ├── sql_queries.py       # DDL + insert queries for ETL
│   ├── sql_analysis_queries.py  # analysis SQL (joins, ST_DWithin, etc.)
│   ├── analysis.py          # Python helpers to run analysis queries
│   └── app.py               # Streamlit app
├── .gitignore
├── pyproject.toml           # project dependencies (for uv / pip)
├── uv.lock                  # lockfile
└── README.md
```

---

## 4. Setup (local development)

### 4.1 Prerequisites

- Python 3.11+ (or similar)
- PostgreSQL with **PostGIS** extension installed locally
- `psycopg2`, `geopandas`, `streamlit`, etc. (already listed in `pyproject.toml`)

### 4.2 Install Python dependencies

Using **uv**:

```bash
uv sync
```

Or with a classic virtualenv:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt # if you export one
```

### 4.3 Configure database connection

Copy the template and fill in your own local credentials:

```bash
cp config/db_example.cfg config/db.cfg
```

add `config/db.cfg`:

```ini
[postgresql]
host=localhost
dbname=riyadh_ksu_geo
user=YOUR_DB_USER
password=YOUR_DB_PASSWORD
port=5432
```

---

## 5. Load data into PostGIS

1. **Create tables:**

   ```bash
   python scripts/create_tables.py
   ```

2. **Run ETL to load GeoJSON and CSV:**

   ```bash
   python scripts/etl.py
   ```

This will:

- Read districts GeoJSON into a GeoDataFrame.
- Reproject to EPSG:32638.
- Compute `area_m2` / `area_km2` and cast `HASRIYADH` to boolean.
- Insert polygons into `districts`.

And similarly for:

- Restaurants (with `ST_GeomFromText` for points).
- KSU gates (from CSV, converting lat/lon to `geom`).

---

## 6. Run analysis (Python helpers)

`scripts/analysis.py` contains functions that:

- Run analysis SQL queries against PostgreSQL.
- Return GeoDataFrames / DataFrames:

  - `load_district_stats(conn)`
  - `load_gates_with_district(conn)`
  - `load_gate_restaurant_distances(conn)`
  - `load_gate_restaurants_1km(conn)`
  - `get_nearest_restaurant_per_gate(df)`
  - `build_gate_summary(...)`

You can import these into notebooks or other scripts to explore the spatial relationships further.

---

## 7. Streamlit app

The Streamlit UI is in `scripts/app.py`.

### 7.1 Running locally

From the project root:

```bash
streamlit run scripts/app.py
```

The app will:

1. Open a DB connection using `get_connection()` (reads `config/db.cfg`).
2. Load analysis tables via `analysis.py`.
3. Show several sections:
   - **District stats**: table of restaurant counts and density per district.
   - **Gate summary**: interactive table filtered by campus / gate.
   - **Gates map**: map of KSU gates with optional summary info.

---

## 8. Deployment notes

This repo is **designed primarily for local development** with a local PostGIS instance.

To deploy online (e.g. Streamlit Cloud), you have two options:

1. **Cloud Postgres (e.g. Neon, Supabase, Render):**

   - Create a Postgres + PostGIS instance.
   - Run `create_tables.py` and `etl.py` against it.
   - Store connection details in Streamlit Secrets:

     ```toml
     [postgresql]
     host = "..."
     dbname = "riyadh_ksu_geo"
     user = "..."
     password = "..."
     port = 5432
     ```

   - Make `get_connection()` read from `st.secrets["postgresql"]` when deployed.


---

## 9. Possible extensions

Ideas for future work:

- Add time-of-day / opening hours for restaurants and study how that affects each gate.
- Compare gate accessibility between male/female/medical campuses.
- Introduce isochrones (e.g. 5-minute walk area vs 1-km buffer).
- Replace sample data with full Riyadh district + roads network and do routing.

---

## 10. License / usage

This project is intended as a **learning and portfolio** project for geospatial data science and PostGIS.  
Feel free to fork it and adapt to your own city / university, but make sure to respect the licenses of any underlying spatial datasets you use.
