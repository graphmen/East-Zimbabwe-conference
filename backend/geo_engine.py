import numpy as np
import os
import json
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon, MultiPoint, shape, mapping
import geojson

def generate_voronoi_districts(churches):
    """
    DEPRECATED: The user requested to totally discard Voronoi-based boundaries.
    Use scripts/generate_territories.py for official grid-based high-res boundaries.
    """
    return geojson.FeatureCollection([])
