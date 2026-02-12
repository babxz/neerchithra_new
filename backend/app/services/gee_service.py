# backend/app/services/gee_service.py
import ee
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np

class GEEService:
    def __init__(self):
        try:
            ee.Initialize()
            self.initialized = True
        except Exception as e:
            print(f"GEE Initialization failed: {e}")
            self.initialized = False
    
    def get_water_body_history(
        self, 
        lat: float, 
        lon: float, 
        radius: int = 500,
        start_date: str = "2019-01-01",
        end_date: str = "2024-12-31"
    ) -> Dict:
        """Get 5-year satellite history for water body"""
        
        if not self.initialized:
            raise Exception("Google Earth Engine not initialized")
        
        # Create geometry
        point = ee.Geometry.Point([lon, lat])
        region = point.buffer(radius)
        
        # Sentinel-2 collection
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR')
              .filterBounds(region)
              .filterDate(start_date, end_date)
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)))
        
        # Calculate NDWI for each image
        def calculate_ndwi(image):
            ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
            water_mask = ndwi.gt(0).rename('water_mask')
            return image.addBands([ndwi, water_mask])
        
        with_ndwi = s2.map(calculate_ndwi)
        
        # Time series extraction
        def extract_stats(image):
            date = image.date().format('YYYY-MM-dd')
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=10,
                maxPixels=1e9
            )
            return ee.Feature(None, {
                'date': date,
                'ndwi': stats.get('NDWI'),
                'water_pixels': stats.get('water_mask')
            })
        
        time_series = with_ndwi.map(extract_stats).getInfo()
        
        # Process to DataFrame
        features = time_series.get('features', [])
        data = []
        for f in features:
            props = f['properties']
            if props.get('ndwi') is not None:
                data.append({
                    'date': props['date'],
                    'ndwi': props['ndwi'],
                    'water_presence': props.get('water_pixels', 0)
                })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate trends
        df['ndwi_30d_avg'] = df['ndwi'].rolling(window=3).mean()
        df['degradation_trend'] = df['ndwi'].diff().rolling(window=6).mean()
        
        # Detect anomalies (encroachment events)
        mean_ndwi = df['ndwi'].mean()
        std_ndwi = df['ndwi'].std()
        df['anomaly'] = np.abs(df['ndwi'] - mean_ndwi) > (2 * std_ndwi)
        
        return {
            'time_series': df.to_dict('records'),
            'statistics': {
                'mean_ndwi': float(mean_ndwi),
                'trend_direction': 'degrading' if df['degradation_trend'].iloc[-1] < 0 else 'improving',
                'total_observations': len(df),
                'anomaly_count': int(df['anomaly'].sum())
            },
            'region': {'lat': lat, 'lon': lon, 'radius_m': radius}
        }
    
    def detect_encroachment(
        self,
        lat: float,
        lon: float,
        compare_dates: Tuple[str, str] = ("2019-06-01", "2024-06-01")
    ) -> Dict:
        """Detect land encroachment by comparing two time periods"""
        
        region = ee.Geometry.Point([lon, lat]).buffer(300)
        
        def get_water_mask(date_start, date_end):
            collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                         .filterBounds(region)
                         .filterDate(date_start, date_end)
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                         .median())
            
            ndwi = collection.normalizedDifference(['B3', 'B8'])
            water_mask = ndwi.gt(0.1)
            return water_mask
    
        # Get water masks for both periods
        old_water = get_water_mask(compare_dates[0], 
                                   (datetime.strptime(compare_dates[0], "%Y-%m-%d") + 
                                    timedelta(days=30)).strftime("%Y-%m-%d"))
        
        new_water = get_water_mask(compare_dates[1],
                                   (datetime.strptime(compare_dates[1], "%Y-%m-%d") + 
                                    timedelta(days=30)).strftime("%Y-%m-%d"))
        
        # Calculate change
        water_lost = old_water.And(new_water.Not())
        water_gained = old_water.Not().And(new_water)
        
        # Calculate area
        area_lost = water_lost.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region,
            scale=10
        ).getInfo()
        
        area_pixels = water_lost.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region,
            scale=10
        ).getInfo()
        
        return {
            'periods': {
                'baseline': compare_dates[0],
                'current': compare_dates[1]
            },
            'area_lost_sqm': area_lost.get('constant', 0),
            'area_lost_hectares': area_lost.get('constant', 0) / 10000,
            'encroachment_detected': area_lost.get('constant', 0) > 100,  # 100 sqm threshold
            'confidence': min(area_lost.get('constant', 0) / 1000, 0.99)  # Scale to 0-1
        }
    
    def download_image(self, lat: float, lon: float, date: str, filename: str):
        """Download satellite image for visualization"""
        
        region = ee.Geometry.Point([lon, lat]).buffer(500).bounds()
        
        image = (ee.ImageCollection('COPERNICUS/S2_SR')
                .filterBounds(region)
                .filterDate(date, (datetime.strptime(date, "%Y-%m-%d") + 
                                  timedelta(days=30)).strftime("%Y-%m-%d"))
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                .first())
        
        # RGB visualization
        rgb = image.select(['B4', 'B3', 'B2']).visualize(min=0, max=3000)
        
        # NDWI visualization
        ndwi = image.normalizedDifference(['B3', 'B8']).visualize(
            min=-0.5, max=0.5, 
            palette=['brown', 'white', 'blue']
        )
        
        # Get download URLs
        rgb_url = rgb.getDownloadUrl({
            'region': region,
            'scale': 10,
            'format': 'GEO_TIFF'
        })
        
        return {
            'rgb_url': rgb_url,
            'ndwi_url': ndwi.getDownloadUrl({
                'region': region,
                'scale': 10,
                'format': 'GEO_TIFF'
            }),
            'date': date,
            'cloud_cover': image.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        }
      
