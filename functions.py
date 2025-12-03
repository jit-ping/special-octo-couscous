import folium
import json
import re  # For parsing the HTML description
from haversine import haversine, Unit
from typing import List, Tuple, Dict, Any
from IPython.display import display

# --- Function 1: Load and Parse Data (Unchanged) ---
# This is the same function as before to read your GeoJSON file.

def load_mrt_data_from_geojson(geojson_path: str) -> List[Tuple[str, Tuple[float, float]]]:
    """
    Loads and parses the LTA GeoJSON file to extract MRT exit coordinates.
    """
    mrt_exits = []

    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        # The data is a 'FeatureCollection', we loop through 'features'
        for feature in data.get('features', []):
            try:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})

                # 1. Extract coordinates
                coordinates = geometry.get('coordinates')
                if not coordinates or geometry.get('type') != 'Point':
                    continue

                lon = coordinates[0]
                lat = coordinates[1]

                # 2. Extract station name from the HTML 'Description'
                description_html = properties.get('Description', '')
                match = re.search(r"<th>STATION_NA<\/th> <td>(.*?)<\/td>", description_html)

                if match:
                    station_name = match.group(1).strip()
                    if "MRT STATION" in station_name:
                        mrt_exits.append((station_name, (lat, lon)))

            except Exception as e:
                print(f"Skipping a feature due to parse error: {e}")

    except FileNotFoundError:
        print(f"Error: File not found at {geojson_path}")
        print("Please ensure the path is correct and your Google Drive is mounted.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {geojson_path}")
        return []
    return mrt_exits


# --- Function 2: Generate Map ---

def get_interactive_map_and_mrt_geojson(
    locations: List[Tuple[float, float]],
    mrt_exits_list: List[Tuple[str, Tuple[float, float]]]
) -> Tuple[str, folium.Map]:
    """
    Finds the nearest MRT, shades the area, and returns the string
    and the Folium map object.
    """

    if not locations:
        return "Error: No locations provided.", None
    if not mrt_exits_list:
        return "Error: No MRT data provided or loaded.", None

    # 1. Calculate the center point
    lats = [loc[0] for loc in locations]
    lons = [loc[1] for loc in locations]
    center_point = (sum(lats) / len(locations), sum(lons) / len(locations))

    # 2. Find the nearest MRT station exit
    nearest_station_name = "Unknown"
    min_distance = float('inf')
    nearest_station_coords = None

    for station_name, station_coords in mrt_exits_list:
        distance = haversine(center_point, station_coords, unit=Unit.KILOMETERS)
        if distance < min_distance:
            min_distance = distance
            nearest_station_name = station_name
            nearest_station_coords = station_coords

    result_string = f"The nearest MRT station is: {nearest_station_name} (distance: {min_distance:.2f} km)"

    # 3. Generate the map object
    m = folium.Map(location=center_point, zoom_start=14)

    # Add the shaded polygon area IF there are 3 or more points
    if len(locations) >= 3:
        folium.Polygon(
            locations=locations,
            popup="Input Area",
            color="#3186cc",      # Color of the border
            fill=True,
            fill_color="#3186cc", # Color of the fill
            fill_opacity=0.2    # Make it semi-transparent
        ).add_to(m)
    # --- *** END OF NEW CODE *** ---

    # Add markers for input locations
    for loc in locations:
        folium.Marker(
            location=loc,
            popup="Input Location",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    # Add marker for the center point
    folium.Marker(
        location=center_point,
        popup="Center Point",
        icon=folium.Icon(color="green", icon="star")
    ).add_to(m)

    # Add marker for the nearest MRT exit
    if nearest_station_coords:
        folium.Marker(
            location=nearest_station_coords,
            popup=f"Nearest MRT: {nearest_station_name}",
            icon=folium.Icon(color="red", icon="train", prefix="fa")
        ).add_to(m)

    # 4. Return the string AND the map object
    return result_string, m
# --- Function 3: Convert DMS to Lat Long ---

def dms_to_dd(degrees, minutes, seconds, direction):
    """Converts Degrees, Minutes, Seconds (DMS) to Decimal Degrees (DD)."""
    
    # 1. Apply the core formula
    decimal_degrees = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    
    # 2. Apply the sign based on direction
    if direction in ('S', 'W', 's', 'w'):
        decimal_degrees = -decimal_degrees
        
    return decimal_degrees
