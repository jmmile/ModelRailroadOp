"""Passenger picture collection using the shared equipment image safeguards."""

from functools import partial

from modelrailroadops.services import locomotive_image_service as managed_images
from modelrailroadops.services.image_storage import PASSENGER_IMAGES

image_directory = partial(managed_images.image_directory, collection=PASSENGER_IMAGES)
image_key = partial(managed_images.image_key, collection=PASSENGER_IMAGES)
find_image = partial(managed_images.find_image, collection=PASSENGER_IMAGES)
picture_change = partial(managed_images.picture_change, collection=PASSENGER_IMAGES)
import_picture = managed_images.import_picture
