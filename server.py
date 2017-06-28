#!/usr/bin/env python
"""A simple example of connecting to Earth Engine using App Engine."""

import os

import config
import ee
import jinja2
import webapp2

# added
import json
import math
import random

import ast



# ------------------------------------------------------------------------------------ #
# Initialization
# ------------------------------------------------------------------------------------ #

# Memcache is used to avoid exceeding our EE quota. Entries in the cache expire
# 24 hours after they are added. See:
# https://cloud.google.com/appengine/docs/python/memcache/
MEMCACHE_EXPIRATION = 60 * 60 * 24


# The URL fetch timeout time (seconds).
URL_FETCH_TIMEOUT = 60

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

ee.Initialize(config.EE_CREDENTIALS)

# define inputs

# define land-use map
landusemap = ee.ImageCollection("projects/servir-mekong/Assemblage/RegionalLC")

# primitives
P_barren = ee.ImageCollection("projects/servir-mekong/Primitives/P_barren")
P_builtup = ee.ImageCollection("projects/servir-mekong/Primitives/P_builtup")
P_canopy = ee.ImageCollection("projects/servir-mekong/Primitives/P_canopy")
P_cropland = ee.ImageCollection("projects/servir-mekong/Primitives/P_cropland")
P_deciduous = ee.ImageCollection("projects/servir-mekong/Primitives/P_deciduous")
P_ephemeral_water = ee.ImageCollection("projects/servir-mekong/Primitives/P_ephemeral_water")
P_evergreen = ee.ImageCollection("projects/servir-mekong/Primitives/P_evergreen")
P_forest_cover = ee.ImageCollection("projects/servir-mekong/Primitives/P_forest_cover")
P_grass = ee.ImageCollection("projects/servir-mekong/Primitives/P_grass")
P_mangrove = ee.ImageCollection("projects/servir-mekong/Primitives/P_mangrove")
P_mixed_forest = ee.ImageCollection("projects/servir-mekong/Primitives/P_mixed_forest")
P_rice = ee.ImageCollection("projects/servir-mekong/Primitives/P_rice")
P_shrub = ee.ImageCollection("projects/servir-mekong/Primitives/P_shrub")
P_snow_ice = ee.ImageCollection("projects/servir-mekong/Primitives/P_snow_ice")
P_surface_water = ee.ImageCollection("projects/servir-mekong/Primitives/P_surface_water")
P_tree_height = ee.ImageCollection("projects/servir-mekong/Primitives/P_tree_height")


primitiveList = [P_barren,P_builtup,P_canopy,P_cropland,P_deciduous,P_ephemeral_water,P_evergreen,P_forest_cover,P_grass,P_mangrove,P_mixed_forest,P_rice,P_shrub,P_snow_ice,P_surface_water,P_tree_height]


countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw');
country_names = ['Myanmar (Burma)','Thailand','Laos','Vietnam','Cambodia']; # Specify name of country. Ignored if "use_uploaded_fusion_table" == y
mekongCountries = countries.filter(ee.Filter.inList('Country', country_names));

class MainPage(webapp2.RequestHandler):

  def get(self):                             # pylint: disable=g-bad-name
    """Request an image from Earth Engine and render it to a web page."""
    
    # get the assemble landuse map
    lcover = ee.Image('projects/servir-mekong/Assemblage/MekongAssemblage_MaxProb_Mode_2015')
    
    currentMap = lcover

	# PALETTE = [
	#    '6f6f6f', // unknown
	#    'aec3d4', // water
	#    '111149', // mangrove
	#    '387242', // tree (other)
	#    'f4a460', // grass
	#    '800080', // shrub
	#    'cc0013', // built-up
	#    '8dc33b', // crop
	#    'ffff00', // rice
	#    'c3aa69', // plantation
	#    '152106', // tree (deciduous)
	#    '115420', // tree (evergreen)
	#];


    PALETTE_list = '6f6f6f,aec3d4,111149,387242,f4a460,800080,cc0013,8dc33b,ffff00,c3aa69,152106,115420'

    lc_mapid = lcover.getMapId({'min': 0, 'max': 11, 'palette': PALETTE_list}) #'6f6f6f, aec3d4, 111149, 247400, 247400, 247400, 55ff00, 55ff00, a9ff00, a9ff00, a9ff00, 006fff, ffff00, ff0000, ffff00, 74ffe0, e074ff, e074ff'})
    

    # These could be put directly into template.render, but it
    # helps make the script more readable to pull them out here, especially
    # if this is expanded to include more variables.
    template_values = {
        'mapid': lc_mapid['mapid'],
        'token': lc_mapid['token']
    }
    
    
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))


# Class to update the land cover map
class updateLandCover(webapp2.RequestHandler):

  def get(self):
	  
    counter =1  
    
    # get the array with boxes that are checked
    mylegend = self.request.get('lc')
    
    # strip the unicode and put it into an array
    mylegend = mylegend.encode('ascii','ignore').strip("[").strip("]").split(",")
  
    year = self.request.get('year')
    start = year + '-01-01'
    end = year + '-12-31'
    
    print start, end
    # load the landcover map
    lcover = ee.Image(landusemap.filterDate(start,end).mean())
    
  # PALETTE = [
	#    '6f6f6f', // unknown
	#    'aec3d4', // water
	#    '111149', // mangrove
	#    '387242', // tree (other)
	#    'f4a460', // grass
	#    '800080', // shrub
	#    'cc0013', // built-up
	#    '8dc33b', // crop
	#    'ffff00', // rice
	#    'c3aa69', // plantation
	#    '152106', // tree (deciduous)
	#    '115420', // tree (evergreen)
	#];


    PALETTE_list = '6f6f6f,aec3d4,111149,387242,f4a460,800080,cc0013,8dc33b,ffff00,c3aa69,152106,115420'

    # create a map with only 0
    mymask = lcover.eq(ee.Number(100))
    
    # enable all checked boxes
    for value in mylegend:
		tempmask = lcover.eq(ee.Number(int(value)))
		mymask = mymask.add(tempmask)
	
    # mask values not in list
    lcover = lcover.updateMask(mymask)

    # get the map id
    lc_mapid = lcover.getMapId({'min': 0, 'max': 11, 'palette': PALETTE_list}) #'6f6f6f, aec3d4, 111149, 247400, 247400, 247400, 55ff00, 55ff00, a9ff00, a9ff00, a9ff00, 006fff, ffff00, ff0000, ffff00, 74ffe0, e074ff, e074ff'})
    
    # set the template as library
    template_values = {
       'eeMapId': lc_mapid['mapid'],
       'eeToken': lc_mapid['token']
    }
    
    # send the result back
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(template_values))    
   


# Class to update the land cover map
class updatePrimitives(webapp2.RequestHandler):

  def get(self):
    
    # get the array with boxes that are checked
    mylegend = self.request.get('lc')
    
    if mylegend == "":
		mylegend = 1
    
    year = int(self.request.get('year'))
    
    # get the primitive
    primitive =  primitiveList[int(mylegend)-1]
    
    myMap = primitive.filter(ee.Filter.calendarRange(year, year, 'year')).mean()
    
    myMap = ee.Image(myMap).unmask(1).clip(mekongCountries)
    
    #PALETTE_list = gen_hex_colour_code()
    PALETTE_list = 'ffffff,0f0000'

    
    lc_mapid = myMap.getMapId({'min': 0, 'max': 1, 'palette': PALETTE_list})
    
    # set the template as library
    template_values = {
       'eeMapId': lc_mapid['mapid'],
       'eeToken': lc_mapid['token']
    }
    
    # send the result back
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(template_values))


# function to download the map
# returns a download url
class downloadMapLuse(webapp2.RequestHandler):

  def get(self):
	  
    coords = []
    
    # get the array with boxes that are checked
    mylegend = self.request.get('lc')
   		
    poly = json.loads(unicode(self.request.get('coords')))
    
    for items in poly:
      coords.append([items[0],items[1]])    
    
    year = int(self.request.get('year'))
        
    lcover = ee.Image(landusemap.filter(ee.Filter.calendarRange(year, year, 'year')).mean())
        
    URL = lcover.getDownloadURL({
     		'scale': 100,
    		'crs': 'EPSG:4326',
    		'region': coords
    		});
    
    content = json.dumps(URL) 
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(content)


app = webapp2.WSGIApplication([('/', MainPage),
							   ('/updateLandCover',updateLandCover),
							   ('/downloadMapLuse',downloadMapLuse),
							   ('/updatePrimitives',updatePrimitives)], debug=True)





# function to download the map
# returns a download url
class downloadMapPrimitives(webapp2.RequestHandler):

  def get(self):
	
    coords = []
		
    poly = json.loads(unicode(self.request.get('coords')))
    
    for items in poly:
      coords.append([items[0],items[1]])    
    
        
    year = int(self.request.get('year'))
    
    # get the array with boxes that are checked
    mylegend = self.request.get('lc')
    
    # get the primitive
    primitive =  primitiveList[int(mylegend)-1]
       
    myMap = primitive.filter(ee.Filter.calendarRange(year, year, 'year')).mean()
    
    myMap = ee.Image(myMap).unmask(1).clip(mekongCountries)
           
    URL = myMap.getDownloadURL({
     		'scale': 100,
    		'crs': 'EPSG:4326',
    		'region': coords
    		});
    
    
    print URL
    
    content = json.dumps(URL) 
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(content)


app = webapp2.WSGIApplication([('/', MainPage),
							   ('/updateLandCover',updateLandCover),
							   ('/downloadMapLuse',downloadMapLuse),
							   ('/downloadMapPrimitives',downloadMapPrimitives),
							   ('/updatePrimitives',updatePrimitives)], debug=True)


###############################################################################
#                           Useful Functions                                  #
###############################################################################

def gen_hex_colour_code():
   return ''.join([random.choice('0123456789ABCDEF') for x in range(6)])


