import dask, rasterio, shapely, sys

import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd

from shapely.validation import make_valid
from shapely.geometry import Point, box
from itertools import product
from shapely.ops import unary_union
from rasterio.windows import from_bounds

path_to_era5 = '/home/abhis/india_power/data/era5/'
path_to_data = '/home/abhis/india_power/gridpath_india_viz/data/'

path_to_images = '/home/gterren/india_power/gridpath_india_viz/images/'
path_to_input  = '/home/gterren/india_power/input_data/'
path_to_scens  = '/home/gterren/india_power/scenarios/cost/'
path_to_zones  = '/home/gterren/india_power/data/vre-climate-data/selected-zones/'
path_to_mapre  = '/home/gterren/india_power/data/mapre/'

path_to_local_data = '/home/gterren/india_power/gridpath_india_viz/data/'

# Remove Dec 31 from leap years
def _drop_leap_day(df_):
    # Function to detect leap year
    def __is_leap_year(year):
        return (year % 4 == 0) and (year % 100 != 0 or year % 400 == 0)

    # Extract time coordinate
    time = df_['valid_time'].to_index()

    # Find indices for Dec 31 in leap years
    remove_indices = [
        i for i, t in enumerate(time)
        if t.month == 12 and t.day == 31 and __is_leap_year(t.year)
    ]
    # Drop those time steps
    df_ = df_.drop_isel(valid_time=remove_indices)

    # Create a new no-leap time index
    new_time_ = pd.date_range(
        start=df_.valid_time.values[0].astype('M8[m]').astype('datetime64[h]'),
        end=df_.valid_time.values[-1].astype('M8[m]').astype('datetime64[h]'),
        freq='1h'
    )

    new_time_ = new_time_[~((new_time_.month == 2) & (new_time_.day == 29))]  # Remove Feb 29
    
    # Replace the time coordinate
    return df_.assign_coords(valid_time=new_time_)

def _india_timezone(df_):

    # Create new hourly time coordinate (rounded to the hour)
    new_time_ = pd.date_range(
        start=df_.valid_time.values[0].astype('M8[m]').astype('datetime64[h]'),
        end=df_.valid_time.values[-1].astype('M8[m]').astype('datetime64[h]'),
        freq='1h'
    )

    # Convert 'valid_time' to Delhi timezone and remove timezone info
    # This preserves local time (Asia/Kolkata), as a naive datetime64
    delhi_time_ = (
        pd.to_datetime(df_['valid_time'].values)        # Convert to pandas datetime
        .tz_localize('UTC')                             # Localize as UTC
        .tz_convert('Asia/Kolkata')                     # Convert to Asia/Kolkata
        .tz_localize(None)                              # Remove timezone
        .to_numpy(dtype='datetime64[ns]')               # Convert to numpy datetime64
    )

    # Assign back to the xarray DataArray as new coordinate
    df_ = df_.assign_coords(valid_time=delhi_time_)

    return df_.interp(valid_time=new_time_)
    #return df_.assign_coords(valid_time=new_time_)

# # Map timepoints to Indian fiscal year and weather interarions 
# def _map_timepoints_to_iterations(ds_, timepoints_mapping_):

#     # Convert to pandas datetime series
#     df_ = pd.DataFrame({'datetime': ds_["valid_time"].values})
#     df_ = pd.to_datetime(df_['datetime'])

#     # Extract components
#     df_.name = 'datetime'
#     df_      = df_.to_frame()

#     df_['year']  = df_['datetime'].dt.year
#     df_['month'] = df_['datetime'].dt.month
#     df_['day']   = df_['datetime'].dt.day
#     df_['hour']  = df_['datetime'].dt.hour
#     df_['index'] = df_.index

#     df_['FY']        = pd.NA
#     df_['iteration'] = pd.NA

#     for i in range(timepoints_mapping_.shape[0]):
#         year  = timepoints_mapping_.loc[i, 'year']
#         month = timepoints_mapping_.loc[i, 'month']
#         fy    = timepoints_mapping_.loc[i, 'FY']
#         iter  = timepoints_mapping_.loc[i, 'iteration']
#         #print(year, month, fy, iter)

#         idx_                       = (df_['year'] == year) & (df_['month'] == month) 
#         df_.loc[idx_, 'FY']        = fy
#         df_.loc[idx_, 'iteration'] = iter

#     idx_ = df_['FY'].isna() & df_['iteration'].isna()
#     df_  = df_.loc[~idx_].reset_index(drop = True)

#     return ds_.isel(valid_time=df_.index)

# Load ERA5 weather feature datasets
def _load_and_professing_ERA5_weather_feature(timepoints_mapping_, variable, file_name, path):
    
    print(file_name)
    ds_ = xr.open_dataset(path + file_name, engine = "netcdf4", chunks={"valid_time": 1000})
    ds_ = _india_timezone(ds_)
    ds_ = _drop_leap_day(ds_)
    #ds_ = _map_timepoints_to_iterations(ds_, timepoints_mapping_)

    return ds_, ds_[variable].load()

def _get_grid(lat_, lon_):

    # Compute edges by midpoint differences
    lat_edges = np.zeros(lat_.size + 1)
    lon_edges = np.zeros(lon_.size + 1)

    lat_edges[1:-1] = 0.5 * (lat_[:-1] + lat_[1:])
    lon_edges[1:-1] = 0.5 * (lon_[:-1] + lon_[1:])

    # Extrapolate outer edges
    lat_edges[0]  = lat_[0] - 0.5 * (lat_[1] - lat_[0])
    lat_edges[-1] = lat_[-1] + 0.5 * (lat_[-1] - lat_[-2])
    lon_edges[0]  = lon_[0] - 0.5 * (lon_[1] - lon_[0])
    lon_edges[-1] = lon_[-1] + 0.5 * (lon_[-1] - lon_[-2])

    return lon_edges, lat_edges[::-1]

def _redistribute_project_capacity(gdf_, grid_, projects_, technology):

    gdf_ = gdf_.reset_index(drop = False)
    crs  = gdf_.crs
    z_   = np.zeros((len(grid_),))

    for i in range(len(gdf_)):
        project = gdf_.loc[i, 'project']

        geo_ = gpd.GeoDataFrame(geometry = [gdf_.loc[i, 'geometry']], 
                                crs = crs).to_crs(epsg = 4326)
        
        area = geo_.to_crs(epsg = 3857).area.to_numpy()[0]

        inter_    = gpd.overlay(grid_, geo_, how = "intersection").to_crs(epsg=3857)
        inter_idx = gpd.sjoin(grid_, geo_, how = "inner", predicate = "intersects").index

        try:
            B = projects_.loc[projects_['project'].str.fullmatch(f'{technology}_{project}', case = True), 'capacity_mw'].to_numpy()[0]
        except:
            B = 0.
        try:
            C = projects_.loc[projects_['project'].str.fullmatch(f'{technology}_{project}_new', case = True), 'capacity_mw'].to_numpy()[0]
        except:
            C = 0.

        for j in range(len(inter_)):
            z_[inter_idx[j]] += ((B + C) * inter_.loc[j, 'geometry'].area)/area

    return z_


def _extract_and_aggregate(raster_path,
                           lat_min, 
                           lat_max,
                           lon_min, 
                           lon_max,
                           new_lat_res, 
                           new_lon_res):
    
    # Step 1: Open raster
    with rasterio.open(raster_path) as src:
        # Step 2: Get window for bounding box
        window = from_bounds(
            lon_min,
            lat_min,
            lon_max,
            lat_max,
            src.transform
        )

        # Read data in the window
        data = src.read(1, window=window, masked=True)
        transform = src.window_transform(window)

        # Get pixel size (in degrees)
        pixel_size_x = transform.a
        pixel_size_y = -transform.e  # usually negative

        # Step 3: Calculate aggregation factor
        factor_x = int(round(new_lon_res / pixel_size_x))
        factor_y = int(round(new_lat_res / pixel_size_y))

        # Ensure divisible shape
        new_rows = (data.shape[0] // factor_y) * factor_y
        new_cols = (data.shape[1] // factor_x) * factor_x
        data_cropped = data[:new_rows, :new_cols]

        # Step 4: Reshape and aggregate using sum
        reshaped = data_cropped.reshape(
            new_rows // factor_y, factor_y,
            new_cols // factor_x, factor_x
        )

        aggregated = np.sum(reshaped, axis=(1, 3))

        return aggregated
    

def _weighted_weather_features(_india, _grid, Z_, W_, lon_, lat_, time_, feature):

    M, N = Z_.shape
    z_   = Z_.flatten()

    dfs_ = []

    # Combine all geometries into one single geometry (MultiPolygon or Polygon)
    _geo       = gpd.GeoDataFrame(geometry = [unary_union(_india.geometry)], crs = "EPSG:4326")
    idx_inter_ = gpd.sjoin(_grid, _geo, how = "inner", predicate = "intersects").index

    # Check which points are inside the geometry
    m_era5_             = np.zeros(z_.shape, dtype = bool)
    m_era5_[idx_inter_] = True
    M_era5_             = m_era5_.reshape(N, M)[:, ::-1].T
    m_era5_             = M_era5_.flatten()

    # Get the matching population and normalized it
    z_norm_ = z_[m_era5_]/z_[m_era5_].sum()
    print(z_norm_.shape, z_norm_.sum())

    w_era5_in_ = W_[:, M_era5_]
    w_era5_in_ = np.average(w_era5_in_, 
                            axis = 1, 
                            weights = z_norm_)

    df_              = pd.DataFrame(w_era5_in_, columns = [feature])
    df_              = pd.concat([time_, df_], axis = 1)
    df_['load_zone'] = 'India'

    dfs_.append(df_)

    for i in range(_india.shape[0]):

        # From state to load_zone
        state     = _india.loc[i, 'state']
        load_zone = state.replace(' ', '_').replace('_and_', '_')

        _geo       = gpd.GeoDataFrame(geometry = [_india.loc[i, 'geometry']], crs = "EPSG:4326")
        idx_inter_ = gpd.sjoin(_grid, _geo, how = "inner", predicate = "intersects").index

        # Check which points are inside the geometry
        m_era5_             = np.zeros(z_.shape, dtype = bool)
        m_era5_[idx_inter_] = True
        M_era5_             = m_era5_.reshape(N, M)[:, ::-1].T
        m_era5_             = M_era5_.flatten()

        # Get the matching population and normalized it
        z_reg_  = z_[m_era5_] + 1e-3
        z_norm_ = z_reg_/z_reg_.sum()
        print(load_zone, z_norm_.shape, z_norm_.sum())

        w_era5_in_ = W_[:, M_era5_]
        w_era5_in_ = np.average(w_era5_in_, 
                                axis = 1, 
                                weights = z_norm_)
    
        df_ = pd.DataFrame(w_era5_in_, columns = [feature])
        df_ = pd.concat([time_, df_], axis = 1)
        df_['load_zone'] = load_zone

        dfs_.append(df_)

    dfs_          = pd.concat(dfs_, axis = 0).reset_index(drop = True)
    dfs_[feature] = dfs_[feature].bfill()

    return dfs_
    
scen = 'VREmid_STmid_CONVmid_H2_RES_8PRM_CC_50RPS_90CAP_500GW_PIERmid'
print(scen)

feature = sys.argv[1]
print(feature)

# Assuming your GeoDataFrame is named 'gdf' and the geometry column is 'geometry'
_india             = gpd.read_file(path_to_data + r"map/india/india-polygon.shp").to_crs("epsg:4326")
_india['geometry'] = _india['geometry'].apply(lambda geom: make_valid(geom) if geom else None)

_india = _india.dropna(subset = ['geometry'])  # Remove rows with None geometry
_india = _india.drop([0, 15, 36])
_india = _india.drop(columns = ['id']).rename(columns = {'st_nm': 'state'})
_india = _india.reset_index(drop = True)

# -----------------------

# Match timepoints to Indian fiscal year and weather interarions 
timepoints_mapping_ = pd.read_csv(path_to_local_data + 'period_to_FY.csv')
timepoints_mapping_ = timepoints_mapping_.loc[~timepoints_mapping_['iteration'].isna()].reset_index(drop = True)

if feature == "wnd10m":
    ds_, X_ = _load_and_professing_ERA5_weather_feature(timepoints_mapping_, 
                                                        "wnd10m", 
                                                        "India_2000-2020_era5_wind10m.nc", 
                                                        path_to_era5)

    lat_era5_  = ds_['latitude'].to_numpy()
    lon_era5_  = ds_['longitude'].to_numpy()
    time_era5_ = ds_["valid_time"].to_numpy()  # 1D datetime array
    
    # from m/s to km/h
    X_ *= 3.6

    del ds_
    print(time_era5_.shape, lat_era5_.shape, lon_era5_.shape, X_.shape)

if feature == "wnd100m":
    ds_, X_ = _load_and_professing_ERA5_weather_feature(timepoints_mapping_, 
                                                        "wnd100m", 
                                                        "India_2000-2020_era5_wind100m.nc", 
                                                        path_to_era5)

    lat_era5_  = ds_['latitude'].to_numpy()
    lon_era5_  = ds_['longitude'].to_numpy()
    time_era5_ = ds_["valid_time"].to_numpy()  # 1D datetime array

    # from m/s to km/h
    X_ *= 3.6

    del ds_
    print(time_era5_.shape, lat_era5_.shape, lon_era5_.shape, X_.shape)

if feature == "tp":
    ds_, X_ = _load_and_professing_ERA5_weather_feature(timepoints_mapping_, 
                                                        "tp",
                                                        "India_2000-2020_era5_precipitation.nc", 
                                                        path_to_era5)

    lat_era5_  = ds_['latitude'].to_numpy()
    lon_era5_  = ds_['longitude'].to_numpy()
    time_era5_ = ds_["valid_time"].to_numpy()  # 1D datetime array

    #  From m to mm
    X_ *= 1000

    del ds_
    print(time_era5_.shape, lat_era5_.shape, lon_era5_.shape, X_.shape)

if feature == "tcc":
    ds_, X_ = _load_and_professing_ERA5_weather_feature(timepoints_mapping_, 
                                                        "tcc", 
                                                        "India_2000-2020_era5_cloud.nc", 
                                                        path_to_era5)

    lat_era5_  = ds_['latitude'].to_numpy()
    lon_era5_  = ds_['longitude'].to_numpy()
    time_era5_ = ds_["valid_time"].to_numpy()  # 1D datetime array

    # from fraction to percentage
    X_ *= 100

    del ds_
    print(time_era5_.shape, lat_era5_.shape, lon_era5_.shape, X_.shape)

if feature == "ghi":
    ds_, X_ = _load_and_professing_ERA5_weather_feature(timepoints_mapping_,
                                                        "ssrd",
                                                        "India_2000-2020_era5_ghi.nc", 
                                                        path_to_era5)

    lat_era5_  = ds_['latitude'].to_numpy()
    lon_era5_  = ds_['longitude'].to_numpy()
    time_era5_ = ds_["valid_time"].to_numpy()  # 1D datetime array

    # from J/m2 to W/m2
    X_ /= 3600

    del ds_
    print(time_era5_.shape, lat_era5_.shape, lon_era5_.shape, X_.shape)

if feature == "cs":
    ds_, X_ = _load_and_professing_ERA5_weather_feature(timepoints_mapping_, 
                                                        "ssrdc", 
                                                        "India_2000-2020_era5_clear_sky.nc", 
                                                        path_to_era5)

    lat_era5_  = ds_['latitude'].to_numpy()
    lon_era5_  = ds_['longitude'].to_numpy()
    time_era5_ = ds_["valid_time"].to_numpy()  # 1D datetime array

    # from J/m2 to W/m2
    X_ /= 3600

    del ds_
    print(time_era5_.shape, lat_era5_.shape, lon_era5_.shape, X_.shape)

if feature == "t2m":
    ds_, X_ = _load_and_professing_ERA5_weather_feature(timepoints_mapping_, 
                                                            "t2m", 
                                                            "India_2000-2020_era5_temp.nc", 
                                                            path_to_era5)

    lat_era5_  = ds_['latitude'].to_numpy()
    lon_era5_  = ds_['longitude'].to_numpy()
    time_era5_ = ds_["valid_time"].to_numpy()  # 1D datetime array

    # from kelvin to celsius
    X_ -= 273.15

    del ds_
    print(time_era5_.shape, lat_era5_.shape, lon_era5_.shape, X_.shape)

idx_iter_ = pd.read_csv(path_to_local_data + 'period_to_FY.csv', index_col = 0)
idx_iter_ = idx_iter_.loc[~idx_iter_['iteration'].isna()].reset_index()

time_era5_          = pd.DataFrame({'datetime': pd.to_datetime(time_era5_)})
time_era5_['year']  = time_era5_['datetime'].dt.year
time_era5_['month'] = time_era5_['datetime'].dt.month

idx_       = time_era5_['year'].isin(idx_iter_['year'].unique())
X_         = X_[idx_, ...].values
time_era5_ = time_era5_.loc[idx_].reset_index(drop = True)

time_era5_merged_              = time_era5_.merge(idx_iter_, on = ['year', 'month'], how='left')
time_era5_merged_['iteration'] = time_era5_merged_['iteration'].astype(int)

# -----------------------

projects_ = pd.read_csv(path_to_scens + scen + '/results/project_period.csv', low_memory = False)

wind_ = gpd.read_file(path_to_mapre + 'base2022_wind.gdb', 
                      driver          = 'fileGDB', 
                      layer           = 'india_zones_combined_100km', 
                      ignore_geometry = False)[['state_zone', 
                                                'geometry']].rename(columns = {'state_zone': 'project'}).set_index('project')

solar_ = gpd.read_file(path_to_mapre + 'base2022_solar.gdb', 
                       driver          = 'fileGDB', 
                       layer           = 'india_zones_combined_100km', 
                       ignore_geometry = False)[['state_zone', 
                                                 'geometry']].rename(columns = {'state_zone': 'project'}).set_index('project')

# Build polygons for each grid cell
x_, y_ = _get_grid(lat_era5_, lon_era5_)

grid_ = []
for i, j in product(range(len(x_) - 1), range(len(y_) - 1)):
    grid_.append(box(x_[i], y_[j], x_[i + 1], y_[j + 1]))
grid_ = gpd.GeoDataFrame({"geometry": grid_}).set_crs("EPSG:4326")

dfs_ = {}

period      = 2040
technology  = 'SolarPV_single'
projects_p_ = projects_.loc[projects_['period'] == period].reset_index(drop = True).copy()
projects_p_ = projects_p_.loc[projects_p_['technology'] == technology].reset_index(drop = True)
projects_p_ = projects_p_[['project', 'technology', 'capacity_mw']]
print(projects_p_.groupby(['technology']).agg({'capacity_mw': 'sum'}))

dfs_['SolarPV_single'] = _redistribute_project_capacity(solar_, grid_, projects_p_, technology = 'solarPV_single').reshape((x_.shape[0] - 1, y_.shape[0] - 1))[:, ::-1].T
print(dfs_['SolarPV_single'].sum())

period      = 2040
technology  = 'SolarPV_tilt'
projects_p_ = projects_.loc[projects_['period'] == period].reset_index(drop = True).copy()
projects_p_ = projects_p_.loc[projects_p_['technology'] == technology].reset_index(drop = True)
projects_p_ = projects_p_[['project', 'technology', 'capacity_mw']]
print(projects_p_.groupby(['technology']).agg({'capacity_mw': 'sum'}))

dfs_['SolarPV_tilt'] = _redistribute_project_capacity(solar_, grid_, projects_p_, technology = 'solarPV_tilt').reshape((x_.shape[0] - 1, y_.shape[0] - 1))[:, ::-1].T
print(dfs_['SolarPV_tilt'].sum())

period      = 2040
technology  = 'Wind'
projects_p_ = projects_.loc[projects_['period'] == period].reset_index(drop = True).copy()
projects_p_ = projects_p_.loc[projects_p_['technology'] == technology].reset_index(drop = True)
projects_p_ = projects_p_[['project', 'technology', 'capacity_mw']]
print(projects_p_.groupby(['technology']).agg({'capacity_mw': 'sum'}))

dfs_['Wind'] = _redistribute_project_capacity(wind_, grid_, projects_p_, technology = 'wind').reshape((x_.shape[0] - 1, y_.shape[0] - 1))[:, ::-1].T
print(dfs_['Wind'].sum())

# -----------------------

rooftop_zones_ = pd.read_csv(path_to_zones + 'rooftop_base_project_capacity_2025.csv')
rooftop_zones_ = rooftop_zones_.loc[~(rooftop_zones_['state_abbrv'] == 'BH')].reset_index(drop = True)
#print(rooftop_zones_.shape)

period      = 2040
technology  = 'SolarPV_roof'
projects_p_ = projects_.loc[projects_['period'] == period].reset_index(drop = True).copy()
projects_p_ = projects_p_.loc[projects_p_['technology'] == technology].reset_index(drop = True)
projects_p_ = projects_p_[['project', 'technology', 'capacity_mw']]
print(projects_p_.groupby(['technology']).agg({'capacity_mw': 'sum'}))
#print(projects_p_)

technology = 'solarPV_roof'

z_ = np.zeros((len(grid_),))
for i in range(len(rooftop_zones_)):
    project = rooftop_zones_.loc[i, 'project']
    lat     = rooftop_zones_.loc[i, 'lat']
    lon     = rooftop_zones_.loc[i, 'lon']
    B       = projects_p_.loc[projects_p_['project'].str.fullmatch(f'{technology}_{project}_new', case = True), 'capacity_mw'].to_numpy()[0]
    #print(project, lat, lon, B)

    # Create a Point object
    z_[grid_.index[grid_.contains(Point(lon, lat))][0]] += B

dfs_['SolarPV_roof'] = z_.reshape((x_.shape[0] - 1, y_.shape[0] - 1))[:, ::-1].T
print(dfs_['SolarPV_roof'].sum())

# -----------------------

period      = 2040
technology  = 'Offshore'
projects_p_ = projects_.loc[projects_['period'] == period].reset_index(drop = True).copy()
projects_p_ = projects_p_.loc[projects_p_['technology'] == technology].reset_index(drop = True)
projects_p_ = projects_p_[['project', 'technology', 'capacity_mw']]
print(projects_p_.groupby(['technology']).agg({'capacity_mw': 'sum'}))

offshore_ = pd.read_csv(path_to_zones + 'offshore_base_project_capacity_2025-2.csv')

# Put it in a GeoDataFrame with CRS = EPSG:4326 (degrees)
for i in range(offshore_.shape[0]):
    offshore_.loc[i, 'geometry'] = shapely.wkt.loads(offshore_.loc[i, 'geometry'])
gdf_ = gpd.GeoDataFrame(geometry=offshore_['geometry'], crs="EPSG:4326")

technology = 'offshore'

z_ = np.zeros((len(grid_),))
for i in range(len(gdf_)):
    project   = offshore_.loc[i, 'project']
    geo_      = gpd.GeoDataFrame(geometry=[gdf_.loc[i, 'geometry']], crs="EPSG:4326")
    inter_    = gpd.overlay(grid_, geo_, how = "intersection").to_crs(epsg=3857)
    inter_idx = gpd.sjoin(grid_, geo_, how = "inner", predicate = "intersects").index

    A = geo_.to_crs(epsg = 3857).area.to_numpy()[0]
    B = projects_.loc[projects_['project'].str.fullmatch(f'{technology}_{project}_new', case = True), 'capacity_mw'].to_numpy()[0]

    for j in range(len(inter_)):
        z_[inter_idx[j]] += (B * inter_.loc[j, 'geometry'].area)/A

dfs_['Offshore'] = z_.reshape((x_.shape[0] - 1, y_.shape[0] - 1))[:, ::-1].T
print(dfs_['Offshore'].sum())

# -----------------------

# Patch location (e.g., around a city or region)
lat_min = lat_era5_.min() - 0.75/4.
lat_max = lat_era5_.max() + 0.75/4.
lon_min = lon_era5_.min() - 0.75/4.
lon_max = lon_era5_.max() + 0.75/4.

# New desired resolution (e.g., 0.05° = ~5.5km)
new_lat_res = 0.25
new_lon_res = 0.25

pow_ = _extract_and_aggregate(path_to_local_data + 'population/gpw_v4_population_count_rev11_2020_2pt5_min.asc',
                              lat_min, 
                              lat_max,
                              lon_min, 
                              lon_max,
                              new_lat_res, 
                              new_lon_res).filled(0)

solar_   = dfs_['SolarPV_single'] + dfs_['SolarPV_tilt'] + dfs_['SolarPV_roof']
wind_    = dfs_['Wind'] + dfs_['Offshore'] 
uniform_ = np.ones(pow_.shape)

# -----------------------

df_       = _weighted_weather_features(_india, grid_, uniform_, X_, lon_era5_, lat_era5_, time_era5_merged_, feature)
df_pow_   = _weighted_weather_features(_india, grid_, pow_, X_, lon_era5_, lat_era5_, time_era5_merged_, feature)
df_solar_ = _weighted_weather_features(_india, grid_, solar_, X_, lon_era5_, lat_era5_, time_era5_merged_, feature)
df_wind_  = _weighted_weather_features(_india, grid_, wind_, X_, lon_era5_, lat_era5_, time_era5_merged_, feature)
#print(df_pow_)

df_pow_.rename(columns = {feature: feature + '_pow'}, inplace=True)
df_solar_.rename(columns = {feature: feature + '_solar'}, inplace=True)
df_wind_.rename(columns = {feature: feature + '_wind'}, inplace=True)
#print(df_pow_)

df_ = df_.merge(df_pow_, on = ['datetime', 'year', 'month', 'FY', 'iteration', 'load_zone'])
df_ = df_.merge(df_solar_, on = ['datetime', 'year', 'month', 'FY', 'iteration', 'load_zone'])
df_ = df_.merge(df_wind_, on = ['datetime', 'year', 'month', 'FY', 'iteration', 'load_zone'])
#print(df_)

df_.to_csv(path_to_local_data + f'avg_{feature}.csv', index = False)
