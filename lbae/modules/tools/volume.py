# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, functions used to handle 3D graphing (e.g. voxel filtering, interpolations, etc) 
are defined.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import numpy as np
from numba import njit

# ==================================================================================================
# --- Functions
# ==================================================================================================


@njit
def filter_voxels(
    array_data_stripped,
    coordinates_stripped,
    array_annotations,
    percentile,
    array_x,
    array_y,
    array_z,
    array_c,
    total_index,
    reference_shape,
    resolution,
):
    """This function takes a given array of coordinates 'coordinates_stripped' and checks if it
    corresponds to a given annotation in the atlas. If so, the coordinates are added to the arrays
    'array_x', 'array_y', 'array_z' to be used for the 3D graphing. Else, it's filtered out.

    Args:
        array_data_stripped (np.ndarray): A 2-dimensional array of voxel intensity for the current 
            slice, stripped of zero values.
        coordinates_stripped (np.ndarray): A 2-dimensional array of voxel coordinates for the current 
            slice, stripped of zero values.
        array_annotations (np.ndarray): The 3-dimensional array of annotation coming from the Allen 
            Brain Atlas.
        percentile (float): The value above which the voxels are considered for the graphing.
        array_x (np.ndarray): A flat array of x coordinates for the 3D graphing.
        array_y (np.ndarray): A flat array of y coordinates for the 3D graphing.
        array_z (np.ndarray): A flat array of z coordinates for the 3D graphing.
        array_c (np.ndarray): A flat array of color values (float) for the 3D graphing.
        total_index (int): An integer used to keep track of the array indexing outside of this 
            function.
        reference_shape (np.ndarray): Array containing the reference atlas shape.
        resolution (int): Integer representing the resolution of the atlas.

    Returns:
        (np.ndarray, np.ndarray, np.ndarray, np.ndarray, int): The filled arrays of coordinates or 
            color for the current slice, and the updated total_index.
    """
    # Keep track of the array indexing even outside of this function
    total_index_temp = 0
    for i in range(array_data_stripped.shape[0]):
        x_atlas, y_atlas, z_atlas = coordinates_stripped[i] / 1000

        # Filter out voxels that are not in the atlas
        x_temp = int(round(x_atlas * 1000000 / resolution))
        y_temp = int(round(y_atlas * 1000000 / resolution))
        z_temp = int(round(z_atlas * 1000000 / resolution))

        # Voxels not even in the atlas array
        if x_temp < 0 or x_temp >= reference_shape[0]:
            continue
        if y_temp < 0 or y_temp >= reference_shape[1]:
            continue
        if z_temp < 0 or z_temp >= reference_shape[2]:
            continue

        # Voxels in the atlas but which don't correspond to a structure
        if array_annotations[x_temp, y_temp, z_temp] == 0:
            continue

        if array_data_stripped[i] >= percentile:
            # * careful, x,y,z are switched
            array_x[total_index + total_index_temp] = z_atlas
            array_y[total_index + total_index_temp] = x_atlas
            array_z[total_index + total_index_temp] = y_atlas
            array_c[total_index + total_index_temp] = array_data_stripped[i]
            total_index_temp += 1

    total_index += total_index_temp
    return array_x, array_y, array_z, array_c, total_index


# * This function could be optimized by turning keep_structure_id into a set
@njit
def fill_array_borders(
    array_annotation, differentiate_borders=False, color_near_borders=False, keep_structure_id=None
):
    """This function takes the Allen Brain atlas array of annotation and returns an array 
    representing the borders of the atlas, to be used later for the volume plot. Values in the array
    are as follows:
    -2 is outside brain
    -0.1 is border
    -0.01 is inside brain/structure
    NB: the -0.01 values get changed after assignment to lipid expression, later on in 
    fill_array_interpolation.

    Args:
        array_annotation (np.ndarray): Three-dimensional array of annotation coming from the Allen 
            Brain Atlas.
        differentiate_borders (bool, optional): If True, represent the brain border with a different 
            value. Defaults to False.
        color_near_borders (bool, optional): If True, the region surrounding the brain border is 
            also filled. Defaults to False.
        keep_structure_id (np.ndarray, optional): Array containing the id of the brain regions whose 
            border must be annotated. Defaults to None.

    Returns:
        np.ndarray: A numpy array representing the borders of the atlas.
    """
    array_atlas_borders = np.full_like(array_annotation, -2.0, dtype=np.float32)
    for x in range(1, array_annotation.shape[0] - 1):
        for y in range(1, array_annotation.shape[1] - 1):
            for z in range(1, array_annotation.shape[2] - 1):
                if array_annotation[x, y, z] > 0:
                    if keep_structure_id is not None:
                        if array_annotation[x, y, z] not in keep_structure_id:
                            continue

                    # If we want to plot the brain border with a different shade
                    if differentiate_borders:
                        # check if border in a cube of size 2
                        found = False
                        for xt in range(x - 1, x + 2):
                            for yt in range(y - 1, y + 2):
                                for zt in range(z - 1, z + 2):
                                    # two cases in which there's a border around, depending if
                                    # keep_structure_id is defined
                                    if keep_structure_id is None:
                                        if array_annotation[xt, yt, zt] == 0:
                                            found = True
                                    else:
                                        if array_annotation[xt, yt, zt] not in keep_structure_id:
                                            found = True
                        if found:
                            array_atlas_borders[x, y, z] = -0.1
                        # inside the brain/structure but not a border
                        else:
                            array_atlas_borders[x, y, z] = -0.01
                    else:
                        array_atlas_borders[x, y, z] = -0.01

    # Also color the region surrounding the border
    if color_near_borders:
        for x in range(1, array_annotation.shape[0] - 1):
            for y in range(1, array_annotation.shape[1] - 1):
                for z in range(1, array_annotation.shape[2] - 1):
                    if np.abs(array_atlas_borders[x, y, z] - (-0.1)) < 10 ** -4:
                        for xt in range(x - 1, x + 2):
                            for yt in range(y - 1, y + 2):
                                for zt in range(z - 1, z + 2):
                                    # not on the border
                                    if np.abs(array_atlas_borders[xt, yt, zt] - (-0.1)) > 10 ** -4:
                                        array_atlas_borders[xt, yt, zt] = -0.2

    return array_atlas_borders


# Do interpolation between the slices
@njit
def fill_array_interpolation(array_annotation, array_slices, divider_radius=5):
    """This function is used to fill the empty space (unassigned voxels) between the slices with 
    interpolated values.

    Args:
        array_annotation (np.ndarray): Three-dimensional array of annotation coming from the Allen 
            Brain Atlas.
        array_slices (np.ndarray): Three-dimensional array containing the lipid intensity values 
            from the MALDI experiments (with many unassigned voxels).
        divider_radius (int, optional): Divides the radius of the region used for interpolation 
            (the bigger, the lower the number of voxels used). Defaults to 5.

    Returns:
        np.ndarray: A three-dimensional array containing the interpolated lipid intensity values.
    """
    array_interpolated = np.copy(array_slices)
    for x in range(0, array_annotation.shape[0]):
        for y in range(0, array_annotation.shape[1]):
            for z in range(0, array_annotation.shape[2]):
                # If we are in a unfilled region of the brain or just inside the brain
                if (np.abs(array_slices[x, y, z] - (-0.01)) < 10 ** -4) or array_slices[
                    x, y, z
                ] >= 0:
                    # Check all datapoints in the same structure, and do a distance-weighted average
                    value_voxel = 0
                    sum_weights = 0
                    size_radius = int(array_annotation.shape[0] / divider_radius)
                    for xt in range(
                        max(0, x - size_radius), min(array_annotation.shape[0], x + size_radius + 1)
                    ):
                        for yt in range(
                            max(0, y - size_radius),
                            min(array_annotation.shape[1], y + size_radius + 1),
                        ):
                            for zt in range(
                                max(0, z - size_radius),
                                min(array_annotation.shape[2], z + size_radius + 1),
                            ):
                                # If we are inside of the shere of radius size_radius
                                if (
                                    np.sqrt((x - xt) ** 2 + (y - yt) ** 2 + (z - zt) ** 2)
                                    <= size_radius
                                ):
                                    # The voxel has data
                                    if array_slices[xt, yt, zt] >= 0:
                                        # The structure is identical
                                        if (
                                            np.abs(
                                                array_annotation[x, y, z]
                                                - array_annotation[xt, yt, zt]
                                            )
                                            < 10 ** -4
                                        ):
                                            d = np.sqrt(
                                                (x - xt) ** 2 + (y - yt) ** 2 + (z - zt) ** 2
                                            )
                                            value_voxel += np.exp(-d) * array_slices[xt, yt, zt]
                                            sum_weights += np.exp(-d)
                    if sum_weights == 0:
                        pass
                        # print("No other voxel found for structure ", array_annotation[x, y, z])
                    else:
                        # print('Voxel found for structure', array_annotation[x, y, z])
                        value_voxel = value_voxel / sum_weights
                        array_interpolated[x, y, z] = value_voxel

    return array_interpolated
