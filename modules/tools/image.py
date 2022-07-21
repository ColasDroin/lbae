# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains functions used to convert arrays to Pillow images, possibly as b64 
strings."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import logging
import numpy as np
import base64
from io import BytesIO
from PIL import Image

# LBAE imports
from config import black_viridis

# ==================================================================================================
# --- Functions
# ==================================================================================================


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
                stream, format=format, optimize=optimize, quality=quality, method=3, lossless=False
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
