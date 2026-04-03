import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from the parent directory's .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
schema: str = os.environ.get("DB_SCHEMA", "ezc")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

# Initialize Supabase client
from supabase import create_client, Client
supabase: Client = create_client(url, key)

def export_churches():
    print(f"Fetching churches from Supabase (Table: ezc_churches)...")
    
    try:
        response = supabase.table('ezc_churches').select('*').execute()
        churches = response.data
    except Exception as e:
        print(f"Error fetching churches: {e}")
        return
    
    if not churches:
        print("No churches found.")
        return

    features = []
    for church in churches:
        # Parse geometry
        geom = church.get('geom')
        if isinstance(geom, str):
            geom = json.loads(geom)
            
        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": church.get('id'),
                "name": church.get('name'),
                "category": church.get('category'),
                "pastor_name": church.get('pastor_name'),
                "district_id": church.get('district_id')
            }
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Save to root directory for easy user access
    output_path = os.path.join(os.path.dirname(__file__), '../../ezc_churches_export.geojson')
    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=2)
        
    print(f"Successfully exported {len(features)} churches to {os.path.abspath(output_path)}")

if __name__ == "__main__":
    export_churches()
