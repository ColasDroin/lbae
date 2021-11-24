###### IMPORT MODULES ######

# Standard import
import logging
import pickle
import os
import numpy as np
from matplotlib import cm
import base64
from io import BytesIO
from PIL import Image

###### DEFINE MISC FUNCTIONS ######


def return_pickled_object(data_folder, file_name, force_update, compute_function, **compute_function_args):

    # Create folder containing the object if it doesn't already exist
    path_folder = "lbae/data/" + data_folder + "/"
    logging.info("The folder " + path_folder + " doesn't already exists, creating it now")
    os.makedirs(path_folder, exist_ok=True)

    # Complete filename with function arguments
    for key, value in compute_function_args.items():
        file_name += "_" + str(value)
    file_name += ".pickle"

    # Check if the object is in the folder already and return it
    if file_name in os.listdir(path_folder) and not force_update:
        logging.info("Returning " + file_name + " from pickled file.")
        with open(path_folder + file_name, "rb") as file:
            return pickle.load(file)
    else:
        logging.info(file_name + " could not be found. Computing the object and pickling it now.")
        object = compute_function(**compute_function_args)

        with open(path_folder + file_name, "wb") as file:
            pickle.dump(object, file)
        return object


def turn_image_into_base64_string(image, colormap=cm.viridis, reverse_colorscale=False):

    # Map image to a colormap and convert to uint8
    img = np.uint8(cm.viridis(image) * 255)

    if reverse_colorscale:
        img = 255 - img

    # Turn array into PIL image object
    pil_img = Image.fromarray(img)

    # Do the string conversion into base64 string
    return base_64_string_conversion(pil_img)

def turn_RGB_image_into_base64_string(image, colormap=cm.viridis):
    
    # Convert image to PIL image
    pil_img = Image.fromarray(image, "RGB")  # PIL image object
    x, y = pil_img.size

    # Decrease resolution to save space
    x2, y2 = int(round(x / 2)), int(round(y / 2))
    pil_img = pil_img.resize((x2, y2), Image.ANTIALIAS)

    # Do the string conversion into base64 string
    return base_64_string_conversion(pil_img)

def base_64_string_conversion(pil_img):
    # Convert to base64 string
    base64_string = None
    with BytesIO() as stream:
        # Optimize the quality as the figure will be pickled, so this line of code won't run live
        pil_img.save(stream, format="png", optimize=True, quality=85)
        base64_string = "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode("utf-8")
    return base64_string





