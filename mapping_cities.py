import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import numpy as np
import shapefile as shp
import os,rasterio
from osgeo import gdal,ogr,osr

# reading shapefile to set boundaries
shapefile_folder = './500Cities_City_11082016/' # path to folder with city shapefile
shapefile_name = ((os.listdir(shapefile_folder)[0]).split('.')[0]).split('_correct_CRS')[0]
drv    = ogr.GetDriverByName('ESRI Shapefile') # define shapefile driver
ds_in  = drv.Open(shapefile_folder+shapefile_name+'.shp',0) #open shapefile
lyr_in = ds_in.GetLayer() # grab layer
sourceprj = (lyr_in.GetSpatialRef()) # input projection
sourceprj.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

targetprj = osr.SpatialReference()
targetprj.ImportFromEPSG(4326) # wanted projection
targetprj.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

transform = osr.CoordinateTransformation(sourceprj, targetprj)
shp = lyr_in.GetExtent()
ll_x,ll_y,_ = transform.TransformPoint(shp[0],shp[2]) # reprojected bounds for city
ur_x,ur_y,_ = transform.TransformPoint(shp[1],shp[3]) # reprojected bounds for city
bbox = [ll_x,ll_y,ur_x,ur_y] # bounding box

# reproject shapefile (if correct projection, the same is return; if incorrect
# it will reproject to WGS84)
outputShapefile = shapefile_folder+shapefile_name+'_correct_CRS.shp'
if os.path.exists(outputShapefile):
    drv.DeleteDataSource(outputShapefile)
outDataSet = drv.CreateDataSource(outputShapefile)
outLayer = outDataSet.CreateLayer("correct_CRS", geom_type=ogr.wkbMultiPolygon)

# add fields
inLayerDefn = lyr_in.GetLayerDefn()
for i in range(0, inLayerDefn.GetFieldCount()):
    fieldDefn = inLayerDefn.GetFieldDefn(i)
    outLayer.CreateField(fieldDefn)

# get the output layer's feature definition
outLayerDefn = outLayer.GetLayerDefn()

inFeature = lyr_in.GetNextFeature()
CONUS_bounds = [-124.7844079,-66.9513812,24.7433195,49.3457868]
while inFeature:
    # get the input geometry
    geom = inFeature.GetGeometryRef()
    # reproject the geometry
    geom.Transform(transform)
    c1 = geom.Centroid()
    
    if c1.GetX()<CONUS_bounds[0] or c1.GetY()<CONUS_bounds[1] or\
    c1.GetX()>CONUS_bounds[2] or c1.GetY()>CONUS_bounds[3]:
        continue
    
    # create a new feature
    outFeature = ogr.Feature(outLayerDefn)
    # set the geometry and attribute
    outFeature.SetGeometry(geom)
    for i in range(0, outLayerDefn.GetFieldCount()):
        outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
    # add the feature to the shapefile
    outLayer.CreateFeature(outFeature)
    # dereference the features and get the next input feature
    outFeature = None
    inFeature = lyr_in.GetNextFeature()
    # Save and close the shapefiles
inDataSet = None
outDataSet = None
#
#################################
# plotting city shapefile
#################################
#
fig,ax = plt.subplots(figsize=(14,8))
m = Basemap(llcrnrlon=CONUS_bounds[0],llcrnrlat=CONUS_bounds[2],urcrnrlon=CONUS_bounds[1],
           urcrnrlat=CONUS_bounds[3],resolution='l', projection='cyl')
shpe = m.readshapefile(shapefile_folder+shapefile_name+'_correct_CRS',
               'curr_shapefile')
m.drawmapboundary(fill_color=plt.cm.Paired(0))
parallels = np.linspace(CONUS_bounds[2],CONUS_bounds[3],5) # latitudes
m.drawparallels(parallels,labels=[True,False,False,False],fontsize=12)
meridians = np.linspace(CONUS_bounds[0],CONUS_bounds[1],5) # longitudes
m.drawmeridians(meridians,labels=[False,False,False,True],fontsize=12)
# m.drawcounties()
m.drawcountries(color='k')
m.fillcontinents(color=plt.cm.tab20c(20), lake_color=plt.cm.Paired(0))
m.drawstates(color='k')
m.drawcoastlines(color='k')

patches   = []
for info, shape in zip(m.curr_shapefile_info, m.curr_shapefile):
   patches.append( Polygon(np.array(shape), True, color='r') )

pc = PatchCollection(patches, match_original=True, edgecolor='r', linewidths=1., zorder=2)
ax.add_collection(pc)
