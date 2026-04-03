import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env from backend/.env
load_dotenv(dotenv_path='../backend/.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def seed_churches():
    try:
        # Load Excel
        df = pd.read_excel('../EZC GPS Coordinates (1).xlsx')
        print(f"Loaded {len(df)} rows from Excel.")
        print(f"Columns: {df.columns.tolist()}")
        print("First row data:")
        print(df.iloc[0].to_dict())
        
        churches_to_insert = []
        for index, row in df.iterrows():
            try:
                # Basic NaN check
                if pd.isna(row['Y']) or pd.isna(row['X']):
                    continue
                
                # In this file, X seems to be Lat and Y seems to be Lng
                # Let's try to parse as such
                lat = float(str(row['X']).strip())
                lng = float(str(row['Y']).strip())
                
                # Skip zeros
                if lat == 0 or lng == 0:
                    continue
                
                # Typical Zimbabwe range Check (X=Lat, Y=Lng)
                # If they are swapped in the file, we adjust.
                if not (-25 < lat < -10 and 20 < lng < 40):
                    # Try swapping just in case some rows are different? 
                    # No, let's be consistent with what we saw in head().
                    continue

                churches_to_insert.append({
                    "name": str(row['Church Name']),
                    "category": str(row.get('Catergory', '')),
                    "district_name": str(row.get('District Name', '')),
                    "pastor_name": str(row.get('Pastor ', '')).strip(),
                    "geom": {
                        "type": "Point",
                        "coordinates": [lng, lat] # GeoJSON is [lng, lat]
                    }
                })
            except (ValueError, TypeError):
                continue
            
        print(f"Preparing to insert {len(churches_to_insert)} churches...")
        if not churches_to_insert:
            print("No valid churches to insert.")
            return

        # Use public schema with ezc_ prefix
        response = supabase.table("ezc_churches").upsert(churches_to_insert).execute()
        print(f"Successfully inserted/updated {len(response.data)} records.")
        
    except Exception as e:
        print(f"Error seeding churches: {str(e)}")

if __name__ == "__main__":
    # Create scripts folder if needed, but I'll assume it exists if I'm writing to it.
    os.makedirs('scripts', exist_ok=True)
    seed_churches()
