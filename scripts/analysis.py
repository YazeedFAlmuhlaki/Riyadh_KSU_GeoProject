# adding needed imports

from create_tables import get_connection
import pandas as pd
import geopandas as gpd
import psycopg2
from sql_analysis_queries import (district_stats_query, 
                                  gates_with_district_query, 
                                  gate_restaurant_distances_query, 
                                  gate_restaurants_1km_query)


def load_district_stats(conn):
    """

    helper function the excute a predefined query (district_stats_query)
    and loaded it to GeoDataFrame.
    """
    try:
        gdf = gpd.read_postgis(
        sql = district_stats_query,
        con= conn,
        geom_col= "district_geom"
        )
    except Exception as e:
        print("Error while excuting district_stats_query:" , e)

    else:
        return gdf
    

def load_gates_with_district(conn):
    """

    helper function the excute a predefined query (gates_with_district_query)
    and loaded it to GeoDataFrame.
    """
    try:
        gdf = gpd.read_postgis(
        sql = gates_with_district_query,
        con= conn,
        geom_col= "gate_geom"
        )
    except Exception as e:
        print("Error while excuting gates_with_district_query:" , e)

    else:
        return gdf
    
def load_gate_restaurant_distances(conn):
    """
    helper function the excute a predefined query (gate_restaurant_distances_query)
    and loaded it to Pandas DataFrame.
    """
    try:
        df = pd.read_sql(gate_restaurant_distances_query, conn)
    
    except Exception as e:
        print("Error while excuting gate_restaurant_distances_query:" , e)
    
    else :
        return df
    

def get_nearest_restaurant_per_gate(gate_restaurant_distances_df:pd.DataFrame):
    """

    Given a DataFrame of all (gate, restaurant) pairs with their distances,
    return a new DataFrame with exactly one row per gate corresponding to
    the nearest restaurant.
    """

    index_list = gate_restaurant_distances_df.groupby("gate_id")["dist_km"].idxmin()
    nearest_df = gate_restaurant_distances_df.loc[index_list]
    nearest_df = nearest_df.reset_index(drop=True)
    return nearest_df



def load_gate_restaurants_1km(conn):
    """

    Helper function that executes the predefined query (gate_restaurants_1km_query)
    and loads the result into a Pandas DataFrame.
    """
    try:
        df = pd.read_sql(gate_restaurants_1km_query, conn)
    except Exception as e:
        print("Error while executing gate_restaurants_1km_query:", e)
    else:
        return df


def build_gate_summary(
    gates_with_district_gdf: gpd.GeoDataFrame,
    nearest_df: pd.DataFrame,
    gate_restaurants_1km_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine gate + district info, nearest restaurant info, and 1 km statistics
    into a single summary DataFrame with one row per gate.
    """
    #
    gates_df = gates_with_district_gdf.drop(columns=["gate_geom"])
    gates_df = gates_df.drop_duplicates(subset=["gate_id"])

    
    nearest_cols = [
        "gate_id",
        "restaurant_id",
        "restaurant_name",
        "rating",
        "categories",
        "dist_km",
    ]
    nearest_df_clean = nearest_df[nearest_cols]
    summary = gates_df.merge(nearest_df_clean, on="gate_id", how="left")

   
    gate_restaurants_1km_clean = gate_restaurants_1km_df.drop(
        columns=["campus", "gate_name_en"],  
        errors="ignore"
    )

    summary = summary.merge(
        gate_restaurants_1km_clean,
        on="gate_id",
        how="left"
    )

    return summary


def main():
    """
    Orchestrates the analysis pipeline:
    - Opens a DB connection.
    - Loads district stats, gates with district info, all gate–restaurant distances,
      and 1 km stats.
    - Computes the nearest restaurant per gate.
    - Builds a gate-level summary table.
    - Prints some basic previews for quick inspection.
    """
    conn, cur = get_connection()
    

    try:
        districts_stats_gdf = load_district_stats(conn)
        gates_with_district_gdf = load_gates_with_district(conn)
        gate_restaurant_distances_df = load_gate_restaurant_distances(conn)
        gate_restaurants_1km_df = load_gate_restaurants_1km(conn)

        
        nearest_df = get_nearest_restaurant_per_gate(gate_restaurant_distances_df)

        
        gate_summary_df = build_gate_summary(
            gates_with_district_gdf,
            nearest_df,
            gate_restaurants_1km_df
        )

       
        print("\n=== District stats (head) ===")
        print(districts_stats_gdf.head())

        print("\n=== Gate summary (head) ===")
        print(gate_summary_df.head())

        
        print("\n=== Top gates by restaurants_1km ===")
        print(
            gate_summary_df.sort_values("restaurants_1km", ascending=False)
                           .head()
        )

        # Example: gates with largest distance to nearest restaurant
        print("\n=== Gates with farthest nearest restaurant ===")
        print(
            gate_summary_df.sort_values("dist_km", ascending=False)
                           .head()
        )

    finally:
        cur.close()
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
