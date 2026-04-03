import geopandas as gpd
from shapely.geometry import Point, box, Polygon
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

def generate_church_territories(boundary_path, churches_path, output_path):
    print("Starting Spatial Allocation Engine (Grid Mode)...")
    gdf_boundaries = gpd.read_file(boundary_path).to_crs("EPSG:32736")
    gdf_churches = gpd.read_file(churches_path).to_crs("EPSG:32736")
    adm_col = 'adm2_name' if 'adm2_name' in gdf_boundaries.columns else gdf_boundaries.columns[0]
    all_processed = []

    for _, row in gdf_boundaries.iterrows():
        dist_name, dist_geom = row[adm_col], row.geometry
        subset = gdf_churches[gdf_churches.within(dist_geom)]
        num = len(subset)
        print(f"Dist: {dist_name} ({num})")
        if num == 0:
            all_processed.append(gpd.GeoDataFrame({'name': [f"{dist_name} Unassigned"], 'church_id': ['NONE'], 'district': [dist_name]}, geometry=[dist_geom], crs="EPSG:32736"))
        elif num == 1:
            c = subset.iloc[0]
            all_processed.append(gpd.GeoDataFrame({'name': [c['name']], 'church_id': [c.get('id', 'UNK')], 'district': [dist_name]}, geometry=[dist_geom], crs="EPSG:32736"))
        else:
            from shapely.ops import voronoi_diagram
            from shapely.geometry import MultiPoint
            
            # --- Centroidal Voronoi (Lloyd's Algorithm) ---
            # We run 2 iterations to 'smooth' the Voronoi cells into organic administrative shapes
            current_seeds = subset.geometry.tolist()
            env = dist_geom.envelope.buffer(dist_geom.envelope.length * 0.1)
            
            for _ in range(2):
                points = MultiPoint(current_seeds)
                regions = voronoi_diagram(points, envelope=env)
                
                new_seeds = []
                # For each region, find its centroid clipped by the district
                # and use that as the next iteration's seed.
                for region in regions.geoms:
                    final_region = region.intersection(dist_geom)
                    if not final_region.is_empty:
                        new_seeds.append(final_region.centroid)
                
                if len(new_seeds) == len(current_seeds):
                    current_seeds = new_seeds
            
            # --- Final Partitioning ---
            points = MultiPoint(current_seeds)
            regions = voronoi_diagram(points, envelope=env)
            
            church_polys = []
            for region in regions.geoms:
                center = region.centroid
                # Find which original church is closest to this balanced centroid
                idx = subset.geometry.distance(center).idxmin()
                
                final_poly = region.intersection(dist_geom)
                if not final_poly.is_empty:
                    church_polys.append({
                        'church_id': subset.loc[idx].get('id', 'UNK'),
                        'church_name': subset.loc[idx]['name'],
                        'geometry': final_poly
                    })
            
            if church_polys:
                df = gpd.GeoDataFrame(church_polys, crs="EPSG:32736")
                df = df.dissolve(by='church_id', aggfunc={'church_name': 'first'}).reset_index()
                # Light simplification to keep GeoJSON size small
                df['geometry'] = df.geometry.simplify(tolerance=5, preserve_topology=True)
                all_processed.append(df)

    if all_processed:
        import time
        import glob
        import json
        ts = int(time.time())
        res = pd.concat(all_processed).to_crs("EPSG:4326")
        res['name'] = res['church_name'] if 'church_name' in res.columns else res['name']
        
        # 1. Save versioned file
        ver_filename = f"church_territories_v{ts}.geojson"
        out_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
        output_path = os.path.join(out_dir, ver_filename)
        res.to_file(output_path, driver='GeoJSON')
        
        # 2. Update config registry
        config_path = os.path.join(out_dir, "gis_config.json")
        config = {
            "lastUpdated": time.ctime(),
            "latestFile": f"/{ver_filename}",
            "version": ts
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"Generated Smoothed Version: {ver_filename}")
        
        # 3. Cleanup old versions (Keep last 3)
        old_files = sorted(glob.glob(os.path.join(out_dir, "church_territories_v*.geojson")))
        if len(old_files) > 3:
            for f in old_files[:-3]:
                try: os.remove(f)
                except: pass

if __name__ == "__main__":
    generate_church_territories(
        'ezc_boundaries.geojson', 
        'ezc_churches_export.geojson', 
        None # Path handled internally
    )
