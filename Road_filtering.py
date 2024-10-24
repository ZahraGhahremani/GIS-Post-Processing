import geopandas as gpd
import rasterio
from shapely.geometry import box
from rasterio.features import rasterize
import numpy as np
import os

def process_rasters(raster_dir, shapefile_path, output_dir, buffer_distance=3, pixel_size=2):
    """
    This fucntion clips a vector by a raster, buffers the vector, rasterizes it, inverts the raster,
    and multiplies it by another raster to remove road areas from a wetland area.

    Parameters:
    - raster_dir: Directory containing input rasters.
    - shapefile_path: Path to the shapefile containing roads.
    - output_dir: Directory to save the output rasters.
    - buffer_distance: Distance for buffering the vector geometries (default: 3).
    - pixel_size: Pixel resolution for rasterizing the buffered geometries (default: 2).
    """
    # List all TIFF files in the directory
    raster_files = [f for f in os.listdir(raster_dir) if f.endswith('.tif')]

    # Load the shapefile once
    gdf = gpd.read_file(shapefile_path)

    # Process each raster file
    for raster_file in raster_files:
        raster_path = os.path.join(raster_dir, raster_file)
        output_multiplied_raster_path = os.path.join(output_dir, f"RF_{raster_file}")

        #  Load the raster to get its extent, CRS, and profile
        with rasterio.open(raster_path) as src:
            raster_bounds = src.bounds
            crs = src.crs
            transform = src.transform
            raster = src.read(1)
            profile = src.profile

        # Clip the vector by the raster's extent
        # Convert the raster bounds to a shapely box (geometry)
        raster_bbox = box(raster_bounds.left, raster_bounds.bottom, raster_bounds.right, raster_bounds.top)

        # Create a GeoDataFrame from the raster's bounding box
        bbox_gdf = gpd.GeoDataFrame({'geometry': [raster_bbox]}, crs=gdf.crs)

        clipped_gdf = gpd.clip(gdf, bbox_gdf)

        # Rasterize the clipped vector with buffering
        # Create a buffer
        buffered_gdf = clipped_gdf.copy()
        buffered_gdf['geometry'] = buffered_gdf.geometry.buffer(buffer_distance)

        # Calculate raster dimensions from bounding box
        minx, miny, maxx, maxy = raster_bounds
        width = int((maxx - minx) / pixel_size)
        height = int((maxy - miny) / pixel_size)
        transform = rasterio.transform.from_origin(minx, maxy, pixel_size, pixel_size)

        # Rasterize the buffered geometries
        buffered_raster = rasterize(
            [(geom, 1) for geom in buffered_gdf.geometry],
            out_shape=(height, width),
            transform=transform,
            fill=0,
            dtype='uint8'
        )

        # Invert the raster values (swap 0 and 1)
        inverted_raster = 1 - buffered_raster

        # Multiply the inverted raster with the original raster
        multiplied_raster = inverted_raster * raster

        # Save the multiplied raster to a new file
        profile.update(dtype=multiplied_raster.dtype, count=1)

        with rasterio.open(output_multiplied_raster_path, 'w', **profile) as dst:
            dst.write(multiplied_raster, 1)

        print(f"Processed and saved multiplied raster to {output_multiplied_raster_path}")

# Example usage:
# process_rasters('/path/to/rasters/Directory', '/path/to/the /road/shapefile/CO_TIGER_road.shp', '/path/to/the/output/Directory')
