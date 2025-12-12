# adding needed imports
import psycopg2
import geopandas as gpd
import pandas as pd
from create_tables import get_connection
from sql_queries import insert_into_districts_table,insert_into_restaurants_table,insert_into_ksu_gates_table


def load_districts(file_path , conn , cur):
    """
    Load Riyadh district polygones from a GeoJSON file into the districts table.
    """
    try:
        gdf = gpd.read_file(file_path)
        gdf.to_crs("EPSG:32638" , inplace=True)
        column_names_mapper = {
            "OBJECTID" : "source_objectid",
            "DISTRICTNO" : "district_code",
            "NEIGHBORHCODE" : "neighborh_code",
            "NEIGHBORHENAME" : "district_name_en",
            "NEIGHBORHANAME" : "district_name_ar",
            "MUNICIPALITYCODE" : "municipality_code",
            "MUNICIPALITYNO" : "municipality_no",
            "HASRIYADH" : "has_riyadh"
        }
        gdf = gdf.rename(columns=column_names_mapper)
        gdf["area_m2"] = gdf.geometry.area
        gdf["area_km2"] = gdf["area_m2"] / 10 ** 6
        gdf["has_riyadh"] = gdf["has_riyadh"].apply(lambda num : True if num == 1 else False)
        
        try:
            for row in gdf.itertuples(index=False):
                cur.execute(
                    insert_into_districts_table,
                    (
                    row.district_code,
                    row.neighborh_code,
                    row.district_name_en,
                    row.district_name_ar,
                    row.municipality_code,
                    row.municipality_no,
                    row.has_riyadh,
                    row.source_objectid,
                    row.area_m2,
                    row.area_km2,
                    row.geometry.wkt  
                    )
                )
            conn.commit()
        except psycopg2.OperationalError as e:
            print("Error inserting into districts table:" , e)
        else:
            print("loading to districts table is done!")

    except FileNotFoundError as e:
        print("Error reading district file:" , e)



def load_restaurants(file_path , conn , cur):
    """
    Load restrunts from a GeoJSON file into the restaurants table.
    """
    try:
        gdf = gpd.read_file(file_path)
        gdf.to_crs("EPSG:32638" , inplace=True)
        
        columns_names_mapper = {
            "ratingSignals" : "rating_signals",
            "postcode" : "post_code"
        }

        gdf = gdf.rename(columns=columns_names_mapper)
        try:
            for row in gdf.itertuples(index=False):
                cur.execute(
                    insert_into_restaurants_table,
                    (
                    row.name,
                    row.categories,
                    row.address,
                    row.price,
                    row.likes,
                    row.photos,
                    row.tips,
                    row.rating,        
                    row.rating_signals,
                    row.price_code,
                    row.post_code,
                    row.geometry.wkt,  
                    )
                )
            conn.commit()
        except psycopg2.OperationalError as e :
            print("Error inserting into restaurants table:" , e)
        else:
            print("loading to restaurants table is done!")
    except FileNotFoundError as e:
        print("Error reading restrunat file:" , e)


def load_ksu_gates(file_path, conn, cur):
    """
    Load KSU gates from a CSV file into the ksu_gates table.
    """
    try:
        
        df = pd.read_csv(file_path)
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
            crs="EPSG:4326"
        )
        gdf.to_crs("EPSG:32638", inplace=True)

        try:
            for row in gdf.itertuples(index=False):
                cur.execute(
                    insert_into_ksu_gates_table,
                    (
                        row.gate_name_en,
                        row.gate_name_ar,
                        row.campus,
                        row.road_name_en,
                        row.road_name_ar,
                        row.gate_type,
                        row.access_notes,
                        row.latitude,
                        row.longitude,
                        row.geometry.wkt, 
                    )
                )
            conn.commit()
        except psycopg2.OperationalError as e:
            print("Error inserting into ksu_gates:", e)
        
        else:
            print("loading to ksu_gates is done!")

    except FileNotFoundError as e:
        print("Error reading ksu_gates file:", e)



def main():
   
    conn, cur = get_connection()
   

    load_districts("data/districts_sample_200.geojson", conn, cur)
    load_restaurants("data/restaurants_sample_in_my_district.geojson", conn, cur)
    load_ksu_gates("data/ksu_gates.csv", conn, cur)


    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
