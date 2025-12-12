"""
Streamlit app for exploring KSU + Riyadh restaurants spatial analysis.

This app relies on:
- create_tables.get_connection
- analysis.py helpers:
    - load_district_stats
    - load_gates_with_district
    - load_gate_restaurant_distances
    - load_gate_restaurants_1km
    - get_nearest_restaurant_per_gate
    - build_gate_summary
"""

import streamlit as st
import pandas as pd
import geopandas as gpd

from create_tables import get_connection
from analysis import (
    load_district_stats,
    load_gates_with_district,
    load_gate_restaurant_distances,
    load_gate_restaurants_1km,
    get_nearest_restaurant_per_gate,
    build_gate_summary,
)

# -------------------------------------------------------------------
# Page config
# -------------------------------------------------------------------
st.set_page_config(
    page_title="KSU Gates & Restaurants Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------------------------------------------------
# Data loading (cached)
# -------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def load_all_data():
    """
    Run the full analysis pipeline once and cache the results.

    Returns
    -------
    districts_stats_gdf : GeoDataFrame
        District-level stats (density, avg rating, etc.).
    gates_with_district_gdf : GeoDataFrame
        Gate locations with district attributes.
    gate_restaurant_distances_df : DataFrame
        All (gate, restaurant) pairs with distances.
    gate_restaurants_1km_df : DataFrame
        Per-gate stats for restaurants within 1km.
    nearest_df : DataFrame
        Nearest restaurant per gate.
    gate_summary_df : DataFrame
        Final gate-level summary (gate + district + nearest + 1km stats).
    """
    conn, cur = get_connection()
    try:
        districts_stats_gdf = load_district_stats(conn)
        gates_with_district_gdf = load_gates_with_district(conn)
        gate_restaurant_distances_df = load_gate_restaurant_distances(conn)
        gate_restaurants_1km_df = load_gate_restaurants_1km(conn)
        nearest_df = get_nearest_restaurant_per_gate(
            gate_restaurant_distances_df
        )
        gate_summary_df = build_gate_summary(
            gates_with_district_gdf,
            nearest_df,
            gate_restaurants_1km_df,
        )
    finally:
        cur.close()
        conn.close()

    return (
        districts_stats_gdf,
        gates_with_district_gdf,
        gate_restaurant_distances_df,
        gate_restaurants_1km_df,
        nearest_df,
        gate_summary_df,
    )


# Load everything (from cache after first run)
(
    districts_stats_gdf,
    gates_with_district_gdf,
    gate_restaurant_distances_df,
    gate_restaurants_1km_df,
    nearest_df,
    gate_summary_df,
) = load_all_data()


# -------------------------------------------------------------------
# Sidebar: filters
# -------------------------------------------------------------------
st.sidebar.title("Filters")

# Campus filter
campus_options = (
    ["All"]
    + sorted(
        [c for c in gate_summary_df["campus"].dropna().unique().tolist()]
    )
)
campus_selected = st.sidebar.selectbox(
    "Select campus", campus_options, index=0
)

# Filter by campus
filtered_gate_summary = gate_summary_df.copy()
if campus_selected != "All":
    filtered_gate_summary = filtered_gate_summary[
        filtered_gate_summary["campus"] == campus_selected
    ]

# Gate filter (depends on campus filter)
gate_name_options = (
    ["All"]
    + sorted(
        filtered_gate_summary["gate_name_en"]
        .dropna()
        .unique()
        .tolist()
    )
)
gate_selected = st.sidebar.selectbox(
    "Select gate", gate_name_options, index=0
)

if gate_selected != "All":
    filtered_gate_summary = filtered_gate_summary[
        filtered_gate_summary["gate_name_en"] == gate_selected
    ]

st.sidebar.markdown("---")
st.sidebar.write("Rows after filter:", len(filtered_gate_summary))


# -------------------------------------------------------------------
# Main layout
# -------------------------------------------------------------------
st.title("KSU Gates & Restaurants Explorer 🍔📍")
st.caption(
    "Explore KSU gates, nearby restaurants, and district-level restaurant density "
    "using PostGIS + Python + Streamlit."
)

# Tabs for different views
tab_gates, tab_districts, tab_raw = st.tabs(
    ["🚪 Gates overview", "🗺️ Districts overview", "📄 Raw data"]
)


# -------------------------------------------------------------------
# Tab 1: Gates overview
# -------------------------------------------------------------------
with tab_gates:
    st.subheader("Gate accessibility & nearest restaurants")

    if len(filtered_gate_summary) == 0:
        st.warning("No gates match the current filters.")
    else:
        # --- Top metrics ---
        col1, col2, col3 = st.columns(3)

        # Metric 1: number of gates
        num_gates = filtered_gate_summary["gate_id"].nunique()
        col1.metric("Number of gates", num_gates)

        # Metric 2: average restaurants within 1km
        if "restaurants_1km" in filtered_gate_summary.columns:
            avg_rest_1km = (
                filtered_gate_summary["restaurants_1km"]
                .dropna()
                .mean()
            )
        else:
            avg_rest_1km = None

        col2.metric(
            "Avg restaurants within 1 km",
            f"{avg_rest_1km:.1f}" if avg_rest_1km is not None else "—",
        )

        # Metric 3: average distance to nearest restaurant
        if "dist_km" in filtered_gate_summary.columns:
            avg_dist_km = (
                filtered_gate_summary["dist_km"].dropna().mean()
            )
        else:
            avg_dist_km = None

        col3.metric(
            "Avg distance to nearest restaurant (km)",
            f"{avg_dist_km:.2f}" if avg_dist_km is not None else "—",
        )

        st.markdown("---")

        # --- Gate table ---
        st.markdown("### Gate summary table")

        gate_cols_to_show = [
            col
            for col in [
                "gate_id",
                "gate_name_en",
                "gate_name_ar",
                "campus",
                "gate_type",
                "district_name_en",
                "restaurant_name",
                "rating",
                "categories",
                "dist_km",
                "restaurants_1km",
                "avg_rating_1km",
            ]
            if col in filtered_gate_summary.columns
        ]

        gate_table = (
            filtered_gate_summary[gate_cols_to_show]
            .sort_values(["restaurants_1km", "dist_km"], ascending=[False, True])
        )

        st.dataframe(gate_table, use_container_width=True)

        # --- Small ranking snippets ---
        st.markdown("### Quick rankings")

        col_left, col_right = st.columns(2)

        # Best food access within 1km
        if "restaurants_1km" in gate_summary_df.columns:
            top_1km = (
                gate_summary_df.dropna(subset=["restaurants_1km"])
                .sort_values("restaurants_1km", ascending=False)
                .head(5)
            )
            col_left.write("**Gates with most restaurants within 1 km**")
            col_left.dataframe(
                top_1km[
                    [
                        "gate_name_en",
                        "campus",
                        "restaurants_1km",
                        "avg_rating_1km",
                    ]
                ],
                use_container_width=True,
            )

        # Farthest nearest restaurant
        if "dist_km" in gate_summary_df.columns:
            farthest = (
                gate_summary_df.dropna(subset=["dist_km"])
                .sort_values("dist_km", ascending=False)
                .head(5)
            )
            col_right.write("**Gates farthest from nearest restaurant**")
            col_right.dataframe(
                farthest[
                    [
                        "gate_name_en",
                        "campus",
                        "dist_km",
                        "restaurant_name",
                        "rating",
                    ]
                ],
                use_container_width=True,
            )

        st.markdown("---")

                # --- Map of gates ---
        st.markdown("### Gates map")

        try:
            # Make sure we're using the right geometry column (gate_geom)
            gates_map_gdf = (
                gates_with_district_gdf
                .set_geometry("gate_geom")   # tell GeoPandas which column is geometry
                .to_crs(epsg=4326)           # reproject to WGS84 for web maps
                .copy()
            )

            # Extract lat/lon from geometry
            gates_map_gdf["lat"] = gates_map_gdf.geometry.y
            gates_map_gdf["lon"] = gates_map_gdf.geometry.x

            # Merge summary info (restaurants_1km / dist_km) onto gates for context
            gates_map_df = pd.merge(
                gates_map_gdf.drop(columns=["gate_geom"]),   # <- was "geometry" before
                gate_summary_df[["gate_id", "restaurants_1km", "dist_km"]],
                on="gate_id",
                how="left",
            )

            # Apply same campus/gate filters used in the table
            map_df = gates_map_df.copy()
            if campus_selected != "All":
                map_df = map_df[map_df["campus"] == campus_selected]
            if gate_selected != "All":
                map_df = map_df[map_df["gate_name_en"] == gate_selected]

            if len(map_df) == 0:
                st.info("No gate points to display for current filters.")
            else:
                st.map(
                    map_df[["lat", "lon"]],
                    zoom=None,
                )

        except Exception as e:
            st.error(f"Error while preparing map: {e}")



# -------------------------------------------------------------------
# Tab 2: Districts overview
# -------------------------------------------------------------------
with tab_districts:
    st.subheader("District-level restaurant density")

    if districts_stats_gdf is None or len(districts_stats_gdf) == 0:
        st.warning("No district stats loaded.")
    else:
        # Table sorted by restaurants_per_km2
        st.markdown("### Districts sorted by restaurants_per_km2")

        district_table_cols = [
            "district_id",
            "district_name_en",
            "district_name_ar",
            "area_km2",
            "restaurant_count",
            "restaurants_per_km2",
            "avg_rating",
        ]
        district_table_cols = [
            c for c in district_table_cols if c in districts_stats_gdf.columns
        ]

        district_table = (
            districts_stats_gdf[district_table_cols]
            .sort_values("restaurants_per_km2", ascending=False)
        )

        st.dataframe(district_table, use_container_width=True)

        # Simple bar chart of density
        st.markdown("### Restaurants per km² (top 15 districts)")

        top15 = district_table.head(15).set_index("district_name_en")
        st.bar_chart(top15["restaurants_per_km2"])


# -------------------------------------------------------------------
# Tab 3: Raw data
# -------------------------------------------------------------------
with tab_raw:
    st.subheader("Raw analysis tables")

    st.markdown("#### gate_summary_df")
    st.dataframe(gate_summary_df.head(50), use_container_width=True)

    st.markdown("#### districts_stats_gdf (head)")
    st.dataframe(districts_stats_gdf.head(50), use_container_width=True)

    st.markdown("#### gate_restaurant_distances_df (head)")
    st.dataframe(gate_restaurant_distances_df.head(50), use_container_width=True)
