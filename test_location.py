import math

# Base location coordinates (RPSU)
BASE_LAT = 23.601004
BASE_LON = 90.498348

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Test points
test_points = [
    (23.601004, 90.498348, "Same point"),
    (23.610004, 90.498348, "Approx 1km north"),
    (23.628004, 90.498348, "Approx 3km north"),
]

for lat, lon, desc in test_points:
    distance = haversine(BASE_LAT, BASE_LON, lat, lon)
    allowed = distance <= 2.0
    print(f"{desc}: Distance {distance:.2f} km, Allowed: {allowed}")
