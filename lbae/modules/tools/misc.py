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
import shutil

###### DEFINE MISC FUNCTIONS ######
from lbae.modules.tools.memuse import logmem


def return_pickled_object(data_folder, file_name, force_update, compute_function, **compute_function_args):

    # Create folder containing the object if it doesn't already exist
    path_folder = "lbae/data/" + data_folder + "/"
    os.makedirs(path_folder, exist_ok=True)

    # Complete filename with function arguments
    for key, value in compute_function_args.items():
        file_name += "_" + str(value)
    file_name += ".pickle"

    # Check if the object is in the folder already and return it
    if file_name in os.listdir(path_folder) and not force_update:
        logging.info("Returning " + file_name + " from pickled file." + logmem())
        with open(path_folder + file_name, "rb") as file:
            return pickle.load(file)
    else:
        logging.info(
            file_name + " could not be found or force_update is True. Computing the object and pickling it now."
        )
        object = compute_function(**compute_function_args)

        with open(path_folder + file_name, "wb") as file:
            pickle.dump(object, file)
        return object


def turn_image_into_base64_string(
    image, colormap=cm.viridis, reverse_colorscale=False, overlay=None, optimize=True, quality=85
):

    # Map image to a colormap and convert to uint8
    img = np.uint8(colormap(image) * 255)
    if reverse_colorscale:
        img = 255 - img

    # Turn array into PIL image object
    pil_img = Image.fromarray(img)

    if overlay is not None:
        pil_img = pil_img.convert("RGBA")
        overlay_img = Image.fromarray(overlay, "RGBA")
        pil_img.paste(overlay_img, (0, 0), overlay_img)

    # Do the string conversion into base64 string
    return base_64_string_conversion(pil_img, optimize=optimize, quality=quality)


def turn_RGB_image_into_base64_string(image, optimize=True, quality=85, RGBA=False):

    # Convert image to PIL image
    if RGBA:
        pil_img = Image.fromarray(image, "RGBA")  # PIL image object

    else:
        # ! find out when this part of the code is used
        pil_img = Image.fromarray(image, "RGB")  # PIL image object
        x, y = pil_img.size

        # Decrease resolution to save space
        x2, y2 = int(round(x / 2)), int(round(y / 2))
        pil_img = pil_img.resize((x2, y2), Image.ANTIALIAS)

    # Do the string conversion into base64 string
    return base_64_string_conversion(pil_img, optimize=optimize, quality=quality)


def base_64_string_conversion(pil_img, optimize, quality, convert_to_RGB=True):
    # Convert image from RGBA to RGB if needed
    # ! Commented out but maybe needed, caution
    # if convert_to_RGB:
    #    pil_img = pil_img.convert("RGB")

    # Convert to base64 string with webp
    base64_string = None
    with BytesIO() as stream:
        # Optimize the quality as the figure will be pickled, so this line of code won't run live
        pil_img.save(stream, format="webp", optimize=optimize, quality=quality, method=6, lossless=False)
        base64_string = "data:image/webp;base64," + base64.b64encode(stream.getvalue()).decode("utf-8")

    # Commented code for conversion with jpeg
    # with BytesIO() as stream:
    #    # Optimize the quality as the figure will be pickled, so this line of code won't run live
    #    pil_img.save(stream, format="jpeg", optimize=optimize, quality=40)
    #    base64_string = "data:image/jpeg;base64," + base64.b64encode(stream.getvalue()).decode("utf-8")

    return base64_string


def delete_all_files_in_folder(input_folder):
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))


def delete_all_pickle_files(path_data_folder="lbae/data/"):

    # Delete all pickled atlas files
    path_atlas_object = "atlas/atlas_objects/"
    delete_all_files_in_folder(path_data_folder + path_atlas_object)

    # Delete all pickled figures from the 3D page
    path_atlas_object = "figures/3D_page/"
    delete_all_files_in_folder(path_data_folder + path_atlas_object)

    # Delete all pickled figures from the lipid selection page
    path_atlas_object = "figures/lipid_selection_page/"
    delete_all_files_in_folder(path_data_folder + path_atlas_object)

    # Delete all pickled figures from the load page
    path_atlas_object = "figures/load_page/"
    delete_all_files_in_folder(path_data_folder + path_atlas_object)
