import os
import json
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Path to .env in backend
load_dotenv(dotenv_path='../backend/.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def export_geojson():
    try:
        print("Fetching districts for export...")
        res = supabase.table("ezc_districts").select("*").execute()
        districts = res.data
        
        if not districts:
            print("No districts found to export.")
            return

        features = []
        for d in districts:
            geom = json.loads(d['geom']) if isinstance(d['geom'], str) else d['geom']
            feature = {
                "type": "Feature",
                "id": d['id'],
                "properties": {
                    "id": d['id'],
                    "name": d['name'],
                    "church_id": d['church_id']
                },
                "geometry": geom
            }
            features.append(feature)

        fc = {
            "type": "FeatureCollection",
            "features": features
        }

        output_path = "../../ezc_districts_export.geojson"
        with open(output_path, "w") as f:
            json.dump(fc, f, indent=2)
            
        print(f"Successfully exported {len(features)} districts to {os.path.abspath(output_path)}")
        
    except Exception as e:
        print(f"Error during export: {str(e)}")

if __name__ == "__main__":
    export_geojson()
