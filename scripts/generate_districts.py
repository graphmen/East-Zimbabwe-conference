import os
import sys
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Add backend to path for geon_engine import
sys.path.append('../backend')
import geo_engine

# Load env from backend/.env
load_dotenv(dotenv_path='../backend/.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_and_save():
    try:
        # 1. Fetch churches
        print("Fetching churches from Supabase...")
        res = supabase.table("ezc_churches").select("*").execute()
        churches = res.data
        if not churches:
            print("No churches found.")
            return
            
        print(f"Loaded {len(churches)} churches. Generating Voronoi districts...")
        
        # 2. Generate
        districts_fc = geo_engine.generate_voronoi_districts(churches)
        
        if not districts_fc['features']:
            print("No districts generated.")
            return

        print(f"Generated {len(districts_fc['features'])} districts. Saving to Supabase...")
        
        # 3. Save to ezc_districts (UPSERT logic to avoid FK errors)
        print("Mapping existing district IDs for stability...")
        res_old = supabase.table("ezc_districts").select("id, church_id").execute()
        old_map = {d['church_id']: d['id'] for d in res_old.data}

        districts_to_save = []
        for feature in districts_fc['features']:
            cid = feature['properties']['church_id']
            payload = {
                "church_id": cid,
                "name": feature['properties']['district_name'],
                "geom": json.dumps(feature['geometry'])
            }
            if cid in old_map:
                payload["id"] = old_map[cid]
            districts_to_save.append(payload)

        print(f"Upserting {len(districts_to_save)} districts...")
        # Break into chunks of 100
        for i in range(0, len(districts_to_save), 100):
            chunk = districts_to_save[i:i+100]
            supabase.table("ezc_districts").upsert(chunk).execute()
            
        # 4. Link churches to districts
        print("Linking churches to districts...")
        # Get the new districts to map church_id -> district_id
        res_dist = supabase.table("ezc_districts").select("id, church_id").execute()
        mapping = {d['church_id']: d['id'] for d in res_dist.data}
        
        for cid, did in mapping.items():
            supabase.table("ezc_churches").update({"district_id": did}).eq("id", cid).execute()
            
        print("Generation complete!")
        
    except Exception as e:
        print(f"Error during generation: {str(e)}")

if __name__ == "__main__":
    generate_and_save()
