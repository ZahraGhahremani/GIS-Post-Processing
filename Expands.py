import rasterio
from rasterio import features
from rasterio.warp import calculate_default_transform
from rasterio.transform import from_bounds
import geopandas as gpd
import numpy as np

def expand_raster_to_shapefile(raster_path, shapefile_path, output_raster_path):
    """
    Expands a raster to the extent of a given shapefile and saves it as a new raster.

    Parameters:
    - raster_path (str): Path to the input raster file.
    - shapefile_path (str): Path to the shapefile to which the raster will be expanded.
    - output_raster_path (str): Path to save the expanded raster.
    """
    # Load the shapefile using GeoPandas and get its extent
    gdf = gpd.read_file(shapefile_path)
    minx, miny, maxx, maxy = gdf.total_bounds  # This gives the extent of the shapefile

    # Open the raster
    with rasterio.open(raster_path) as src:
        # Read the original raster data
        original_data = src.read(1)
        original_transform = src.transform
        original_crs = src.crs
        original_dtype = src.dtypes[0]
        original_width = src.width
        original_height = src.height
        
        # Get the pixel size
        pixel_size_x = original_transform[0]
        pixel_size_y = -original_transform[4]
        
        # Calculate the new dimensions based on the shapefile's extent
        new_width = int((maxx - minx) / pixel_size_x)
        new_height = int((maxy - miny) / pixel_size_y)
        
        # Create a new transform for the expanded raster
        new_transform = from_bounds(minx, miny, maxx, maxy, new_width, new_height)

    # Create an empty array with zeros for the extended raster
    new_data = np.zeros((new_height, new_width), dtype=original_dtype)

    # Calculate the offset to place the original raster inside the new extended raster
    offset_x = int((original_transform[2] - minx) / pixel_size_x)
    offset_y = int((maxy - original_transform[5]) / pixel_size_y)

    # Insert the original raster data into the new extended array at the correct location
    new_data[offset_y:offset_y + original_height, offset_x:offset_x + original_width] = original_data

    # Write the extended raster with the new dimensions and transform
    with rasterio.open(
            output_raster_path, 'w',
            driver='GTiff',
            height=new_height, width=new_width,
            count=1, dtype=original_dtype,
            crs=original_crs,
            transform=new_transform) as dst:
        dst.write(new_data, 1)

    print(f"Extended raster saved to {output_raster_path}")

# Example usage
raster_path = "/Path/to/the/input/raster/file/raster.tif"
shapefile_path = "/Path/to/the/input/shape/file/shapefile.shp"
output_raster_path = "/Path/to/the/input/raster/file/output.tif"

expand_raster_to_shapefile(raster_path, shapefile_path, output_raster_path)