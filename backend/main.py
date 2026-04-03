import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import geo_engine
import json

load_dotenv()

app = FastAPI(title="EZC Church GIS Dashboard API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ChurchUpsert(BaseModel):
    name: str
    category: Optional[str]
    district_name: Optional[str]
    pastor_name: Optional[str]
    lat: float
    lng: float

@app.get("/")
async def root():
    return {"message": "EZC GIS Backend is running!"}

@app.post("/api/churches/bulk-upsert")
async def bulk_upsert_churches(churches: List[ChurchUpsert]):
    try:
        data_to_upsert = []
        for church in churches:
            data_to_upsert.append({
                "name": church.name,
                "category": church.category,
                "district_name": church.district_name,
                "pastor_name": church.pastor_name,
                "geom": f"SRID=4326;POINT({church.lng} {church.lat})"
            })
        
        # Use public schema with ezc_ prefix
        response = supabase.table("ezc_churches").upsert(data_to_upsert).execute()
        return {"status": "success", "count": len(response.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/districts/generate")
async def generate_districts():
    try:
        # 1. Load churches
        response = supabase.table("ezc_churches").select("*").execute()
        churches = response.data
        if not churches:
            return {"status": "error", "message": "No churches found to generate districts."}
        
        # 2. Run Geo Engine
        districts_geojson = geo_engine.generate_voronoi_districts(churches)
        
        # 3. Save to database
        for dist in districts_geojson['features']:
            church_id = dist['properties']['church_id']
            supabase.table("ezc_districts").insert({
                "church_id": church_id,
                "name": dist['properties']['name'],
                "geom": json.dumps(dist['geometry'])
            }).execute()
            
        return {"status": "success", "message": f"Generated {len(districts_geojson['features'])} districts."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/districts")
async def get_districts():
    response = supabase.table("ezc_districts").select("id, name, church_id").execute()
    return response.data

@app.get("/api/districts/{id}/geojson")
async def get_district_geojson(id: str):
    # Fetch GeoJSON directly from PostGIS using a raw selectivity or RPC
    # For now, let's just fetch the record
    response = supabase.table("ezc_districts").select("geom").eq("id", id).execute()
    if response.data:
        return response.data[0]['geom']
    raise HTTPException(status_code=404, detail="District not found")

@app.post("/api/reports")
async def submit_report(report: dict):
    response = supabase.table("ezc_reports").insert(report).execute()
    return response.data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
