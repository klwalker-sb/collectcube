#!/usr/bin/env python
# coding: utf-8

import os
import sys
import random
from pathlib import Path
import osgeo  #Needed for use on Windows only
import shapely
from osgeo import gdal
from shapely.geometry import Point, Polygon, box
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio as rio
from rasterio import plot
from rasterio.plot import show
import sqlite3
import sqlalchemy as sa
import matplotlib.pyplot as plt

def get_sample_in_poly(aoi_in, sampsize, subpoly=None):
    '''
    returns geodataframe with n (=sampsize) randomly sampled points within an aoi
    If aoi has multiple polygons, can sample from full extent or a selected polygon
    out crs will be the same as in crs
    '''
    gdf = gpd.read_file(aoi_in)
    print('aoi file has crs:{}'.format(gdf.crs))

    if subpoly is not None:
        #bounds = gdf.query(f'UNQ == {subpoly}').geometry.total_bounds
        geosub = gdf.iloc[subpoly]
        bounds = geosub.geometry.bounds
    else:
        bounds = gdf.geometry.total_bounds
    
    xmin, ymin, xmax, ymax = bounds

    xext = xmax - xmin
    yext = ymax - ymin

    points = []
    while len(points) < sampsize:
        # generate a random x and y
        x = xmin + random.random() * xext
        y = ymin + random.random() * yext                                 
        p = Point(x, y)
        if subpoly is not None:
            if geosub.geometry.contains(p):  # check if point is inside geometry
                points.append(p)
        else:
            if gdf.geometry.contains(p).any():  # check if point is inside geometry
                points.append(p)
    
    #gs = gpd.GeoSeries(points)
    ptgdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(points), crs=gdf.crs)
    return ptgdf

def move_points_to_pixel_centroids(ptgdf, ref_ras, write_pts=False, ptsout=None):
    '''
    returns geodataframe identical to input points (ptgdf), but slightly shifted to align with centroids of 
    gridcells in reference raster (ref_ras). 
    out crs will be the same as reference raster
    '''

    '''
    ## With GDAL only:
    driver = gdal.GetDriverByName('GTiff')
    ds = gdal.Open(ref_ras)
    transform = ref_ras.GetGeoTransform()
    x_origin = transform[0]
    y_origin = transform[3]
    pixel_width = transform[1]
    pixel_height = -transform[5]
    crs = ref_ras.GetProjection()
    print('ref_ras has crs:{}'.format(crs))
    print(transform)
    # e.g: (3158725.0, 10.0, 0.0, -3159495.0, 0.0, -10.0)
    '''
    
    with rio.open(ref_ras) as src:
        img = src.read()
    x_origin = src.transform[2]
    y_origin = src.transform[5]
    pixel_width = src.transform[0]
    pixel_height = -src.transform[4]
    print('ref_ras has crs:{}'.format(src.crs))
    #print(src.transform)
    shifted_pts = []
    
    if ptgdf.crs != src.crs:
        ptgdf = ptgdf.to_crs(src.crs)
        
    for index,row in ptgdf.iterrows():
        point = (row.geometry.x, row.geometry.y)
        col = int((point[0] - x_origin) / pixel_width)
        row = int((y_origin - point[1] ) / pixel_height)
        pixel_centroid = Point(x_origin + (pixel_width*col) + (pixel_width/2), y_origin - (pixel_height*row) - (pixel_height/2))
        shifted_pts.append(pixel_centroid)
        
    #gs_shift = gpd.GeoSeries(shifted_pts)
    ptgdf_shift = gpd.GeoDataFrame(geometry=gpd.GeoSeries(shifted_pts),crs=src.crs)

    if write_pts==True:
        ptgdf_shift.to_file(ptsout, driver='ESRI Shapefile')
        
    return ptgdf_shift

def find_poly_on_image(zoom_poly, img, poly_file):
    '''
    Plots a polygon file {'poly_file'} on top of a .tiff image {'img'}
    and zooms to a selected poly {'zoom_poly'}
    '''
    
    with rio.open(img) as src:
        img2 = src.read()
        b = src.bounds
    ## box(minx, miny, maxx, maxy, ccw=True)
    img_box  = box(b[0],b[1],b[2],b[3])
    img_bounds = gpd.GeoDataFrame(gpd.GeoSeries(img_box), columns=['geometry'], crs=src.crs)
    
    if isinstance(poly_file, gpd.GeoDataFrame):
        polys = poly_file
    else:
        polys = gpd.read_file(poly_file)
    ## Get bounds to zoom into polygon specified in arguments
    polys_in_img = gpd.overlay(img_bounds, polys, how='intersection')
    polybds = polys_in_img.bounds.iloc[zoom_poly]
    
    fig, ax = plt.subplots(figsize=(8,8))
    plot.show(img2, ax=ax, transform=src.transform)    
    polys_in_img.plot(ax=ax, facecolor='none', edgecolor='orangered')
    focus_area = [polybds.minx -100, polybds.maxx +100, polybds.miny -100, polybds.maxy +100]
    plt.axis(focus_area)
    
    print('polys overlapping image: \n',polys_in_img)
    
def get_full_point_file(pts_in, pt_file_out, res):
    if isinstance(pts_in, gpd.GeoDataFrame):
        pts = pts_in
    else:
        pts = gpd.read_file(pts_in)
        
    pts['PID'] = pts.apply(lambda x: f'{int(x.name)+1:07d}_0', axis=1)
    pts['Center'] = 1
    newdfs=[]
    for index,row in pts.iterrows():
        pt = (row.geometry.x, row.geometry.y)
        pid = row['PID'].split('_')[0]
        pt1 = Point(pt[0]-res, pt[1]+res)
        pt2 = Point(pt[0], pt[1]+res)
        pt3 = Point(pt[0]+res, pt[1]+res)
        pt4 = Point(pt[0]-res, pt[1])
        pt5 = Point(pt[0]+res, pt[1])
        pt6 = Point(pt[0]-res, pt[1]-res)
        pt7 = Point(pt[0], pt[1]-res)
        pt8 = Point(pt[0]+res, pt[1]-res)
        neighbor_pts = [pt1,pt2,pt3,pt4,pt5,pt6,pt7,pt8]
        ptgdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(neighbor_pts), crs=pts.crs)
        ptgdf['Center'] = 0
        ptgdf['PID'] = ptgdf.apply(lambda x: f'{pid}_{int(x.name) + 1}', axis=1)
        newdfs.append(ptgdf)

    neighbor_df = pd.concat(newdfs)
    print(type(ptgdf))
    print('there are {} neighbor pixels'.format(len(neighbor_df)))
    full_df = pd.concat([pts,neighbor_df])
    
    print('there are {} total pixels'.format(len(full_df)))
    full_df.to_file(pt_file_out, driver='ESRI Shapefile')
    return full_df

def make_pixel_boxes_from_pts(pts_in, poly_file_out,res):
    if isinstance(pts_in, gpd.GeoDataFrame):
        pts = pts_in
    else:
        pts = gpd.read_file(pts_in)
    
    boxes = []
    for index,row in pts.iterrows():
        pt = (row.geometry.x, row.geometry.y)
        tl = (pt[0]-res/2, pt[1]+res/2)
        tr = (pt[0]+res/2, pt[1]+res/2)
        bl = (pt[0]-res/2, pt[1]-res/2)
        br = (pt[0]+res/2, pt[1]-res/2)
        box = [br,tr,tl,bl]
        boxes.append(box)
    
    df = pd.DataFrame({'geometry': boxes})
    df['geometry'] = df['geometry'].apply(shapely.geometry.Polygon)
    gdf = gpd.GeoDataFrame(df, crs=pts.crs, geometry=df['geometry'])
    gdf.to_file(poly_file_out, driver='ESRI Shapefile')
    return gdf

def make_pixel_table(pts_in):
    if isinstance(pts_in, gpd.GeoDataFrame):
        pts = pts_in
    else:
        pts = gpd.read_file(pts_in)
    
    ptsll = pts.to_crs(4326)
    ptsll['cent_lat'] = ptsll['geometry'].y
    ptsll['cent_long'] = ptsll['geometry'].x
    
    pts2 = pd.merge(pts,ptsll[['PID','cent_lat', 'cent_long']],on='PID', how='left')
    
    pts2['cent_X'] = pts2['geometry'].x
    pts2['cent_Y'] = pts2['geometry'].y
    pts2['ransamp'] = 1
    
    ptdf = pd.DataFrame(pts2.drop(columns='geometry'))
    
    return(ptdf)

def make_pixel_table_in_db(pixdf, local_db_path, treat_existing):
    engine = sa.create_engine(local_db_path, echo=False)
    pixdf.to_sql('pixels', con=engine, if_exists=treat_existing, index = False, dtype={'PID': sa.types.Text(),
                                                              'Center' : sa.types.Integer(),
                                                              'cent_lat' : sa.types.Float(precision=6, asdecimal=True),
                                                              'cent_lon' : sa.types.Float(precision=6, asdecimal=True),
                                                              'cent_X' : sa.types.Float(precision=2, asdecimal=True), 
                                                              'cent_Y' : sa.types.Float(precision=2, asdecimal=True),
                                                              'ransamp' : sa.types.Integer()})