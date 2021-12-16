# from numpy.lib.shape_base import tile
# import labelbox
# from labelbox.data.annotation_types.geometry import point
# from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter, LBV1Label
# from labelbox.data.annotation_types import (LabelList, ImageData, MaskData,
#                                             Rectangle, ObjectAnnotation,
#                                             ClassificationAnnotation, Point,
#                                             ClassificationAnswer, Radio, Mask,
#                                             Label, annotation)
# from labelbox import User, Project

# import json
# from labelbox.data.annotation_types.data.tiled_image import EPSG, EPSGTransformer, TileLayer, TiledBounds, TiledImageData
# from PIL import Image
# from typing import Union
# from enum import Enum

# from labelbox import Client
# from shapely.geometry import Polygon, box
# import cv2
# import numpy as np

# import requests
# import os

# # from labelbox.schema.labelbox_event import LabelboxEvent

# os.system('clear')

# # apikey = os.environ.get('apikey')
# # client = Client(apikey)

# epsg4326 = EPSG.EPSG4326
# epsg3857 = EPSG.EPSG3857
# epsgsimple = EPSG.SIMPLEPIXEL

# # # top_left_bound = Point(x=37.87488726890353, y=-122.32488870620728)
# # top_left_bound = Point(x=-122.32488870620728, y=37.87488726890353)
# # # bottom_right_bound = Point(x=37.87280390440759, y=-122.32154130935669)
# # bottom_right_bound = Point(x=-122.32154130935669, y=37.87280390440759)

# top_left_bound = Point(x=0, y=0)
# bottom_right_bound = Point(x=256, y=256)

# bounds_simple = TiledBounds(epsg=EPSG.SIMPLEPIXEL,
#                             bounds=[top_left_bound, bottom_right_bound])

# bounds_3857 = TiledBounds(epsg=EPSG.EPSG3857,
#                           bounds=[
#                               Point(x=-104.150390625, y=30.789036751261136),
#                               Point(x=-81.8701171875, y=45.920587344733654)
#                           ])
# bounds_4326 = TiledBounds(epsg=EPSG.EPSG4326,
#                           bounds=[
#                               Point(x=-104.150390625, y=30.789036751261136),
#                               Point(x=-81.8701171875, y=45.920587344733654)
#                           ])

# # layer = TileLayer(
# #     url="https://labelbox.s3-us-west-2.amazonaws.com/pathology/{z}/{x}/{y}.png",
# #     name="slippy map tile")

# # tiled_image_data = TiledImageData(tile_layer=layer,
# #                                   tile_bounds=bounds_simple,
# #                                   zoom_levels=[1, 23],
# #                                   version=2)
# # tiled_image_data.multithread = True
# # # print(tiled_image_data.as_raster_data(zoom=0))
# # image_array = tiled_image_data.as_raster_data(zoom=2)
# # image_array_value = tiled_image_data.value
# # im = Image.fromarray(image_array_value)
# # im.show()

# # #____________________________________________________________________________________________________
# # GEO TO PIXEL
# # print(f"\n")
# # transformer = EPSGTransformer()
# # transformer.geo_and_pixel(src_epsg=epsg3857,
# #                           pixel_bounds=bounds_simple,
# #                           geo_bounds=bounds_3857,
# #                           zoom=0)
# # point_3857 = Point(x=-11016716.012685884, y=5312679.21393289)
# # point_simple = transformer(point=point_3857)
# # print(f"initial 3857 point...{point_3857}")
# # print(f"geo 3857 to pixel...{point_simple}")

# # #____________________________________________________________________________________________________
# # print(f"\n")
# # # PIXEL TO GEO
# # transformer = EPSGTransformer()
# # transformer.geo_and_pixel(src_epsg=epsgsimple,
# #                           pixel_bounds=bounds_simple,
# #                           geo_bounds=bounds_3857,
# #                           zoom=0)
# # # point_simple = Point(x=154, y=130)
# # point_3857 = transformer(point=point_simple)
# # print(f"initial pixel point...{point_simple}")
# # print(f"pixel to geo...{point_3857}")
# # #____________________________________________________________________________________________________
# print(f"\n")
# #GEO TO GEO
# transformer = EPSGTransformer()
# transformer.geo_and_geo(EPSG.EPSG4326, EPSG.EPSG3857)

# point_4326 = Point(x=-98.96484375, y=43.004647127794435)
# point_3857 = transformer(point=point_4326)
# print(f"initial 4326 point...{point_4326}")
# print(f"geo 4326 to geo 3857...{point_3857}")

# # #____________________________________________________________________________________________________
# print(f"\n")
# #GEO TO GEO
# transformer = EPSGTransformer()
# transformer.geo_and_geo(EPSG.EPSG3857, EPSG.EPSG4326)

# # point_3857 = Point(x=1000, y=1000)
# point_4326 = transformer(point=point_3857)
# print(f"initial 3857 point...{point_3857}")
# print(f"geo 3857 to geo 4326...{point_4326}")

# zoom = 4
# #____________________________________________________________________________________________________
# # GEO TO PIXEL
# print(f"\n")
# transformer = EPSGTransformer()
# transformer.geo_and_pixel(src_epsg=epsg4326,
#                           pixel_bounds=bounds_simple,
#                           geo_bounds=bounds_4326,
#                           zoom=zoom)
# point_4326 = Point(x=-98.96484375, y=43.004647127794435)
# point_simple = transformer(point=point_4326)
# print(f"initial 4326 point...{point_4326}")
# print(f"geo 4326 to pixel...{point_simple}")

# #____________________________________________________________________________________________________
# # print(f"\n")
# # # PIXEL TO GEO
# transformer = EPSGTransformer()
# transformer.geo_and_pixel(src_epsg=epsgsimple,
#                           pixel_bounds=bounds_simple,
#                           geo_bounds=bounds_4326,
#                           zoom=zoom)

# point_4326 = transformer(point=point_simple)
# print(f"initial pixel point...{point_simple}")
# print(f"pixel to geo 4326...{point_4326}")

# print(f"\n")
# # PIXEL TO GEO
# transformer = EPSGTransformer()
# transformer.geo_and_pixel(src_epsg=epsgsimple,
#                           pixel_bounds=bounds_simple,
#                           geo_bounds=bounds_3857,
#                           zoom=zoom)

# point_3857 = transformer(point=point_simple)
# print(f"initial pixel point...{point_simple}")
# print(f"pixel to geo 3857...{point_3857}")

# transformer = EPSGTransformer()
# transformer.geo_and_geo(src_epsg=epsg3857, tgt_epsg=epsg4326)
# point_4326 = transformer(point=point_3857)
# print(f"3857 to 4326...{point_4326}")

# #____________________________________________________________________________________________________
# #assumptions:
# #bounds will always be in 4326 as that is what leaflet assumes


def hello_world():
    print("hello world")







    if 5 == 5: print("goodbye world")
