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


def convert_image_to_base64(
    image_array,
    optimize=True,
    quality=85,
    colormap=cm.viridis,
    type=None,
    format="png",
    overlay=None,
    decrease_resolution_factor=1,
):

    # Convert 1D array into a PIL image
    if type is None:
        # Map image to a colormap and convert to uint8
        img = np.uint8(colormap(image_array) * 255)

        # Turn array into PIL image object
        pil_img = Image.fromarray(img)

    # Convert 3D or 4D array into a PIL image
    elif type == "RGB" or type == "RGBA":
        pil_img = Image.fromarray(image_array, type)

    # Overlay is transparent, therefore initial image must be converted to RGBA
    if overlay is not None:
        if type != "RGBA":
            pil_img = pil_img.convert("RGBA")
        overlay_img = Image.fromarray(overlay, "RGBA")
        pil_img.paste(overlay_img, (0, 0), overlay_img)

    # If we want to decrease resolution to save space
    if decrease_resolution_factor > 1:
        x, y = pil_img.size
        x2, y2 = int(round(x / decrease_resolution_factor)), int(round(y / decrease_resolution_factor))
        pil_img = pil_img.resize((x2, y2), Image.ANTIALIAS)

    # Convert to base64
    base64_string = None
    with BytesIO() as stream:
        if format == "webp":
            # Optimize the quality as the figure will be pickled, so this line of code won't run live
            pil_img.save(stream, format=format, optimize=optimize, quality=quality, method=6, lossless=False)
        elif format == "gif":
            # Convert to paletted image to save space
            pil_img = pil_img.convert("P")
            # Optimize the quality as the figure will be pickled, so this line of code won't run live
            pil_img.save(stream, format=format, optimize=optimize, transparency=255)
        else:
            # ? Caution, palette-based may not work or cause bug
            # Convert to paletted image to save space
            pil_img = pil_img.convert("P")
            # Optimize the quality as the figure will be pickled, so this line of code won't run live
            pil_img.save(stream, format=format, optimize=optimize, quality=quality)
        base64_string = "data:image/" + format + ";base64," + base64.b64encode(stream.getvalue()).decode("utf-8")

    # Commented code for e.g. conversion with jpeg
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


# ! To update when code is more stable
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
