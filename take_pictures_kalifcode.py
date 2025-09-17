from core.auto_operate_microscope import *
from core.kalifcode import *

locations_dict = memorize_locations()
callback_map = {'twenty ten': lambda: take_all_images(magnification=10, side=2422, locations_dict=locations_dict),
                'twenty twenty': lambda: take_all_images(magnification=20, side=2422, locations_dict=locations_dict),
                'five ten': lambda: take_all_images(magnification=10, side=549, locations_dict=locations_dict),
                'five twenty': lambda: take_all_images(magnification=20, side=549, locations_dict=locations_dict),
                'convex five': lambda: take_all_images(magnification=5, side='Convex', locations_dict=locations_dict),
                'convex ten': lambda: take_all_images(magnification=10, side='Convex', locations_dict=locations_dict),
                'convex twenty': lambda: take_all_images(magnification=20, side='Convex', locations_dict=locations_dict),
                'concave five': lambda: take_all_images(magnification=5, side='Concave', locations_dict=locations_dict),
                'concave ten': lambda: take_all_images(magnification=10, side='Concave', locations_dict=locations_dict),
                'concave twenty': lambda: take_all_images(magnification=20, side='Concave', locations_dict=locations_dict),
                'six five': lambda: take_all_images(magnification=5, side='Upper', locations_dict=locations_dict),
                'six ten': lambda: take_all_images(magnification=10, side='Upper', locations_dict=locations_dict),
                'six twenty': lambda: take_all_images(magnification=20, side='Upper', locations_dict=locations_dict),
                'one five': lambda: take_all_images(magnification=5, side='Lower', locations_dict=locations_dict),
                'one ten': lambda: take_all_images(magnification=10, side='Lower', locations_dict=locations_dict),
                'one twenty': lambda: take_all_images(magnification=20, side='Lower', locations_dict=locations_dict),
                'change window': lambda: alt_tab,
                'zoom in': lambda: zoom_in(3),
                'zoom out': lambda: zoom_in(-3),
                'exposure one': lambda: insert_exposure_time(1, 0, 0, locations_dict=locations_dict),
                'exposure two': lambda: insert_exposure_time(2, 0, 0, locations_dict=locations_dict),
                'exposure to': lambda: insert_exposure_time(2, 0, 0, locations_dict=locations_dict),
                'exposure five': lambda: insert_exposure_time(5, 0, 0, locations_dict=locations_dict),
                'exposure four': lambda: insert_exposure_time(5, 0, 0, locations_dict=locations_dict),
                'exposure three': lambda: insert_exposure_time(3, 0, 0, locations_dict=locations_dict)}

start_voice_listener(command_map=callback_map)