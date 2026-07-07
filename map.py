import folium
from logic import GlobalCapitalRouter

# -------------------------------
# 📍 Country Coordinates
# -------------------------------
COUNTRY_COORDS = {
    "INDIA": (20.5937, 78.9629),
    "USA": (37.0902, -95.7129),
    "SINGAPORE": (1.3521, 103.8198),
    "UAE": (23.4241, 53.8478),
    "MAURITIUS": (-20.3484, 57.5522),
    "UK": (55.3781, -3.4360),
    "UNITED KINGDOM": (55.3781, -3.4360),
    "CANADA": (56.1304, -106.3468),
    "FRANCE": (46.2276, 2.2137),
    "GERMANY": (51.1657, 10.4515),
    "JAPAN": (36.2048, 138.2529),
    "NETHERLANDS": (52.1326, 5.2913),
    "HONG_KONG": (22.3193, 114.1694),
    "CHINA": (35.8617, 104.1954),
    "BRAZIL": (-14.2350, -51.9253),
    "ARGENTINA": (-38.4161, -63.6167),
    "NIGERIA": (9.0820, 8.6753),
    "SOUTH_AFRICA": (-30.5595, 22.9375),
}


# -------------------------------
# 🗺️ MAP FUNCTION (Dynamic)
# -------------------------------

def create_dynamic_route_map(source: str, destination: str, via_countries: list, output_path: str = "map.html"):
    """
    Generate a folium map showing:
      - Red dashed line: Direct route (source → destination)
      - Green solid line: Optimized route (source → via... → destination)

    Args:
        source: Source country name (e.g. "INDIA")
        destination: Destination country name (e.g. "USA")
        via_countries: List of intermediate countries (e.g. ["UAE"])
        output_path: Where to save the HTML file
    """
    source = source.upper()
    destination = destination.upper()
    via_countries = [v.upper() for v in via_countries]

    # Validate all countries have coordinates
    all_countries = [source] + via_countries + [destination]
    for country in all_countries:
        if country not in COUNTRY_COORDS:
            raise ValueError(f"Missing coordinates for country: '{country}'. Available: {list(COUNTRY_COORDS.keys())}")

    # Build coordinate lists
    direct_coords = [COUNTRY_COORDS[source], COUNTRY_COORDS[destination]]
    optimized_coords = [COUNTRY_COORDS[c] for c in all_countries]

    # Center map between source and destination
    center_lat = (COUNTRY_COORDS[source][0] + COUNTRY_COORDS[destination][0]) / 2
    center_lon = (COUNTRY_COORDS[source][1] + COUNTRY_COORDS[destination][1]) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=3)

    # 🔵 Source Marker
    folium.Marker(
        COUNTRY_COORDS[source],
        tooltip=f"Source: {source}",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    # 🔴 Destination Marker
    folium.Marker(
        COUNTRY_COORDS[destination],
        tooltip=f"Destination: {destination}",
        icon=folium.Icon(color="red")
    ).add_to(m)

    # 🔴 DIRECT ROUTE (RED DASHED)
    folium.PolyLine(
        direct_coords,
        color="red",
        weight=4,
        dash_array="5,5",
        tooltip="Direct Route (Higher Cost)"
    ).add_to(m)

    # 🟢 OPTIMIZED ROUTE (GREEN SOLID)
    folium.PolyLine(
        optimized_coords,
        color="green",
        weight=5,
        tooltip=f"Optimized Route: {' → '.join(all_countries)}"
    ).add_to(m)

    # 🟢 Intermediate (Via) Markers
    for country in via_countries:
        folium.Marker(
            COUNTRY_COORDS[country],
            tooltip=f"Via: {country}",
            icon=folium.Icon(color="green")
        ).add_to(m)

    # 🧾 Legend
    legend_html = f"""
     <div style="
     position: fixed; 
     bottom: 30px; left: 30px; width: 260px; 
     background-color: white; 
     border:2px solid grey; z-index:9999; font-size:14px;
     padding: 12px; border-radius: 6px;
     ">
     <b>Route Legend</b><br><br>
     <i style="color:red;">━━━</i> Direct Route ({source} → {destination})<br>
     <i style="color:green;">━━━</i> Optimized Route ({" → ".join(all_countries)})
     </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(output_path)
    print(f"Map saved: {output_path}")
    return output_path


# -------------------------------
# ▶️ RUN (standalone test)
# -------------------------------
if __name__ == "__main__":
    create_dynamic_route_map(
        source="INDIA",
        destination="USA",
        via_countries=["SINGAPORE"],
        output_path="capital_route_comparison.html"
    )
