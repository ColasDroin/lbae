###### IMPORT MODULES ######

# Standard modules
import numpy as np
from numba import njit
import logging

# TODO : do docstrings of the functions here

###### FUNCTIONS USED IN 3D GRAPHING ######

# Define a numba function to accelerate the loop in which the ccfv3 coordinates are computed and the final
# arrays are filled
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

        # if array_data_stripped[i] >= percentile:
        if True:
            # * careful, x,y,z are switched
            array_x[total_index + total_index_temp] = z_atlas
            array_y[total_index + total_index_temp] = x_atlas
            array_z[total_index + total_index_temp] = y_atlas
            array_c[total_index + total_index_temp] = array_data_stripped[i]
            total_index_temp += 1

    total_index += total_index_temp
    return array_x, array_y, array_z, array_c, total_index


# Compute an array of boundaries for volume plot
# -2 is outside brain
# -0.1 is border
# -0.01 is inside brain/structure
# the -0.01 numbers get changed after assignment to lipid expression

# ! need to opitmize by turning keep_structure_id into a set
@njit
def fill_array_borders(
    array_annotation, differentiate_borders=False, color_near_borders=False, keep_structure_id=None
):
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
                                    # two cases in which there's a border around, depending if keep_structure_id is defined
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

    # if color_near_borders:
    #     for x in range(1, array_annotation.shape[0] - 1):
    #         for y in range(1, array_annotation.shape[1] - 1):
    #             for z in range(1, array_annotation.shape[2] - 1):
    #                 if np.abs(array_atlas_borders[x, y, z] - (-0.1)) < 10 ** -4:
    #                     for xt in range(x - 1, x + 2):
    #                         for yt in range(y - 1, y + 2):
    #                             for zt in range(z - 1, z + 2):
    #                                 # not on the border
    #                                 if np.abs(array_atlas_borders[xt, yt, zt] - (-0.1)) > 10 ** -4:
    #                                     array_atlas_borders[xt, yt, zt] = -0.2

    return array_atlas_borders


# Do interpolation between the slices
@njit
def fill_array_interpolation(array_annotation, array_slices, divider_radius=5):
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
                        # print("No other voxel was found for structure ", array_annotation[x, y, z])
                    else:
                        # print('Voxel found for structure', array_annotation[x, y, z])
                        value_voxel = value_voxel / sum_weights
                        array_interpolated[x, y, z] = value_voxel

    return array_interpolated
