## this file will continas all needed analysis queries.


district_stats_query = """
SELECT 
    district_id,
    district_name_en,
    district_name_ar,
    area_km2,
    COUNT(restaurant_id) AS restaurant_count,
    AVG(rating) AS avg_rating,
    (COUNT(restaurant_id) / area_km2) AS restaurants_per_km2,
    districts.geom AS district_geom
FROM 
districts INNER JOIN restaurants 
ON 
ST_Contains(districts.geom, restaurants.geom)
GROUP BY 1,2,3,4,8;
"""


gates_with_district_query = """
SELECT 
    gate_id,
    gate_name_en,
    gate_name_ar,
    campus,
    gate_type,
    access_notes,
    ksu_gates.geom as gate_geom,
    district_id,
    district_name_en,
    district_name_ar
FROM 
ksu_gates LEFT JOIN districts
ON 
ST_Contains(districts.geom, ksu_gates.geom);
"""


gate_restaurant_distances_query = """
SELECT 
    gate_id,
    gate_name_en,
    campus,
    restaurant_id,
    name as restaurant_name,
    rating,
    categories,
    ST_Distance(ksu_gates.geom ,restaurants.geom) / 1000 AS dist_km
FROM ksu_gates , restaurants;
"""

gate_restaurants_1km_query = """
SELECT 
    gate_id,
    gate_name_en,
    campus,
    COUNT(restaurant_id) as restaurants_1km,
    AVG(rating) as avg_rating_1km
FROM 
ksu_gates INNER JOIN restaurants
ON ST_DWithin(ksu_gates.geom, restaurants.geom, 1000)
GROUP BY 1,2,3;
"""