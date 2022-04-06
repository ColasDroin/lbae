# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains various functions used many times in different parts of the app."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import logging
import pickle
import os
import numpy as np
from matplotlib import cm
import base64
from io import BytesIO
from PIL import Image
import shutil
import psutil
from numba import njit
import transaction

# LBAE modules
from config import black_viridis
from db import root
from ZODB import blob

# ==================================================================================================
# --- Functions
# ==================================================================================================


def logmem():
    """This function returns a string representing the current amount of memory used by the program.
    It is almost instantaneous as it takes about 0.5ms to run.

    Returns:
        str: Amount of memory used by the program.
    """
    memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    memory_string = "MemTotal: " + str(memory)
    return "\t" + memory_string


def return_db_object(
    data_folder,
    file_name,
    force_update,
    compute_function,
    ignore_arguments_naming=False,
    **compute_function_args
):
    """This function checks if the result of the method or function compute_function has not been
    computed and saved already. If yes, it returns this result from the corresponding pickle file.
    Else, it executes compute_function, saves the result in a pickle file, and returns the result.

    Args:
        data_folder (str): The path of the folder in which the result of compute_function must be 
            saved.
        file_name (str): The name of the pickle file to save/load. Arguments will potentially be 
            contatenated to file_name depending on the value of ignore_arguments_naming.
        force_update (bool): If True, compute_function will be re-executed and saved despite the 
            file result already existing.
        compute_function (func): The function/method whose result must be loaded/saved.
        ignore_arguments_naming (bool, optional): If True, the arguments of compute_function won't
            be added to the filename of the result file. Defaults to False.
        **compute_function_args: Arguments of compute_function.

    Returns:
        The result of compute_function. Type may vary depending on compute_function.
    """
    # Create folder containing the object if it doesn't already exist
    path_folder = "data/" + data_folder + "/"
    os.makedirs(path_folder, exist_ok=True)

    # Complete filename with function arguments
    if not ignore_arguments_naming:
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
            file_name
            + " could not be found or force_update is True. "
            + "Computing the object and pickling it now."
        )

        # Execute compute_function
        object = compute_function(**compute_function_args)

        # Save the result in a pickle file
        with open(path_folder + file_name, "wb") as file:
            pickle.dump(object, file)
        logging.info(file_name + " being returned now from computation.")
        return object


def return_db_object(
    data_folder,
    file_name,
    force_update,
    compute_function,
    ignore_arguments_naming=False,
    **compute_function_args
):
    """This function checks if the result of the method or function compute_function has not been
    computed and saved already. If yes, it returns this result from the corresponding ZODB file.
    Else, it executes compute_function, saves the result in the ZODB file, and returns the result.

    Args:
        data_folder (str): The path of the folder in which the result of compute_function must be 
            saved.
        file_name (str): The name of the pickle file to save/load. Arguments will potentially be 
            contatenated to file_name depending on the value of ignore_arguments_naming.
        force_update (bool): If True, compute_function will be re-executed and saved despite the 
            file result already existing.
        compute_function (func): The function/method whose result must be loaded/saved.
        ignore_arguments_naming (bool, optional): If True, the arguments of compute_function won't
            be added to the filename of the result file. Defaults to False.
        **compute_function_args: Arguments of compute_function.

    Returns:
        The result of compute_function. Type may vary depending on compute_function.
    """
    # Get path filename
    complete_file_name = data_folder + "/" + file_name + "/"

    # Complete filename with function arguments
    if not ignore_arguments_naming:
        for key, value in compute_function_args.items():
            complete_file_name += "_" + str(value)

    # Check if the object is in the folder already and return it
    if complete_file_name in root.data and not force_update:
        logging.info("Returning " + file_name + " from ZODB database." + logmem())
        return root.data[complete_file_name]
    else:
        logging.info(
            file_name
            + " could not be found or force_update is True. "
            + "Computing the object and storing it now."
        )

        # Execute compute_function
        object = compute_function(**compute_function_args)

        # Save the result in a pickle file
        root.data[complete_file_name] = blob.Blob(object)
        transaction.commit()
        logging.info(file_name + " being returned now from computation.")
        return object


def black_to_transparency(img):
    """This function takes a PIL image and convert the zero-valued pixels to transparent ones in the
    most efficient way possible.

    Args:
        img (PIL.Image): The image for which the pixels must be made transparent.

    Returns:
        PIL.Image: The image with transparent pixels.
    """
    # Need to copy as PIL arrays are read-only
    x = np.asarray(img.convert("RGBA")).copy()
    x[:, :, 3] = (255 * (x[:, :, :3] != 0).any(axis=2)).astype(np.uint8)
    return Image.fromarray(x)


def convert_image_to_base64(
    image_array,
    optimize=True,
    quality=85,
    colormap=black_viridis,
    type=None,
    format="png",
    overlay=None,
    decrease_resolution_factor=1,
    binary=False,
    transparent_zeros=False,
):
    """This functions allows for the conversion of a numpy array into a bytestring image using PIL. 
    All images are paletted so save space.

    Args:
        image_array (np.ndarray): The array containing the image. May be 1D of 3D or 4D. The type 
            argument must match with the dimensionality.
        optimize (bool, optional): If True, PIL will try to optimize the image size, at the expense 
            of a longer computation time. This is not available with all image formats (check PIL 
            documentation). Defaults to True.
        quality (int, optional): Image quality, from 0 to 100, used by PIL for compression. Defaults 
            to 85.
        colormap (cm colormap, optional): The colormap used to map 1D uint8 image to colors. 
            Defaults to cm.viridis.
        type (str, optional): The type of the image. If image_array is in 3D, type must be RGB. If 
            4D, type must be RGBA. Defaults to None.
        format (str, optional): The output format for the bytestring image. Defaults to "png". 
            "webp", "gif", "jpeg" also available.
        overlay (np.ndarray, optional): Another image array to overlay with image_array. Defaults to 
            None.
        decrease_resolution_factor (int, optional): Used to divide the resolution of the initial 
            array, to output a smaller image. Defaults to 1.
        binary (bool, optional): Used to convert the output image to binary format ("LA", in PIL), 
            to save a lot of space for greyscales images. 
            Defaults to False.

    Returns:
        str: The base 64 image encoded in a string.
    """
    logging.info("Entering string conversion function")

    # Convert 1D array into a PIL image
    if type is None:
        # Map image to a colormap and convert to uint8
        img = np.uint8(colormap(image_array) * 255)

        # Turn array into PIL image object
        pil_img = Image.fromarray(img)

    # Convert 3D or 4D array into a PIL image
    elif type == "RGB" or type == "RGBA":
        pil_img = Image.fromarray(image_array, type)

    logging.info("Image has been converted from array to PIL image")

    # Overlay is transparent, therefore initial image must be converted to RGBA
    if overlay is not None:
        if type != "RGBA":
            pil_img = pil_img.convert("RGBA")
        overlay_img = Image.fromarray(overlay, "RGBA")
        pil_img.paste(overlay_img, (0, 0), overlay_img)
        logging.info("Overlay has been added to the image")

    # If we want to decrease resolution to save space
    if decrease_resolution_factor > 1:
        x, y = pil_img.size
        x2, y2 = (
            int(round(x / decrease_resolution_factor)),
            int(round(y / decrease_resolution_factor)),
        )
        pil_img = pil_img.resize((x2, y2), Image.ANTIALIAS)
        logging.info("Resolution has been decreased")

    if transparent_zeros:
        # Takes ~5 ms but makes output much nicer
        pil_img = black_to_transparency(pil_img)
        logging.info("Empty pixels are now transparent")

    # Convert to base64
    base64_string = None
    with BytesIO() as stream:
        # Handle image format

        if format == "webp":
            logging.info("Webp mode selected, binary or paletted modes are not supported")
            pil_img.save(
                stream, format=format, optimize=optimize, quality=quality, method=6, lossless=False
            )

        elif format == "gif":
            # Convert to paletted image to save space
            pil_img = pil_img.convert("P")
            logging.info("gif mode selected, quality argument is not supported")
            pil_img.save(stream, format=format, optimize=optimize, transparency=255)

        elif format == "jpeg":
            # Convert to paletted image to save space
            pil_img = pil_img.convert("P")
            pil_img.save(stream, format=format, optimize=optimize, quality=quality)

        else:
            # Convert to paletted image to save space
            if binary:
                pil_img = pil_img.convert("LA")
            else:
                pil_img = pil_img.convert("P")
            logging.info("png mode selected, quality argument is not supported")
            pil_img.save(stream, format=format, optimize=optimize, bits=9)

        # Encode final image
        base64_string = (
            "data:image/"
            + format
            + ";base64,"
            + base64.b64encode(stream.getvalue()).decode("utf-8")
        )
    logging.info("Image has been converted to base64. Returning it now.")
    return base64_string


def delete_all_files_in_folder(input_folder):
    """This function deletes all files and folder preset in the diretory input_folder

    Args:
        input_folder (str): Path of the input folder to clean.
    """
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        try:
            # Delete wether directory or file
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))


# ! To update when code is more stable
def delete_all_pickle_files(path_data_folder="data/"):
    """This function deletes all the files saved as part of the app normal functioning, to allow for
    a clean reset. Note that it actually deletes more than just pickle files.

    Args:
        path_data_folder (str, optional): Path of the data folder, in which temporary files will be 
        cleaned. Defaults to "data/".
    """
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
