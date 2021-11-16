###### IMPORT MODULES ######
import numpy as np
from numba import njit

###### UTILITY FUNCTIONS WITH NUMBA ######


@njit
def project_image(index_slice, original_image, array_projection_correspondence):
    # correct index
    index_slice -= 1

    new_image = np.zeros(array_projection_correspondence.shape[1:-1], dtype=original_image.dtype)
    # exclude the borders of the image to gain some time
    for i in range(50, array_projection_correspondence[index_slice].shape[0] - 50):
        for j in range(50, array_projection_correspondence[index_slice].shape[1] - 50):
            # coordinate -1 corresponds to unassigned
            if array_projection_correspondence[index_slice, i, j, 0] != -1:
                x, y = array_projection_correspondence[index_slice, i, j]
                new_image[i, j] = original_image[x, y]

    return new_image


@njit
def get_projected_atlas_mask(stack_mask, slice_coordinates, shape_atlas):

    projected_mask = np.full(slice_coordinates.shape[:-1], stack_mask[0, 0, 0], dtype=np.int32)
    for x in range(slice_coordinates.shape[0]):
        for y in range(slice_coordinates.shape[1]):
            current_coor_rescaled = slice_coordinates[x, y]
            if (
                min(current_coor_rescaled) >= 0
                and current_coor_rescaled[0] < shape_atlas[0]
                and current_coor_rescaled[1] < shape_atlas[1]
                and current_coor_rescaled[2] < shape_atlas[2]
            ):
                projected_mask[x, y] = stack_mask[
                    current_coor_rescaled[0], current_coor_rescaled[1], current_coor_rescaled[2]
                ]
    return projected_mask


@njit
def get_array_rows_from_atlas_mask(mask, mask_remapped, array_projection_correspondence):
    # map back the mask coordinates to original data
    for x in range(mask.shape[0]):
        for y in range(mask.shape[1]):
            x_original, y_original = array_projection_correspondence[x, y]
            if (
                x_original >= 0
                and x_original < mask_remapped.shape[0]
                and y_original >= 0
                and y_original < mask_remapped.shape[0]
            ):
                mask_remapped[x_original, y_original] = mask[x, y]

    # then compute the rows
    ll_rows = []
    for x in range(mask_remapped.shape[0]):
        first = False
        ymin = -1
        ymax = -1
        l_rows = [x]
        for y in range(mask_remapped.shape[1]):
            if mask_remapped[x, y] != 0 and not first:
                ymin = y
                first = True
            elif mask_remapped[x, y] == 0 and first:

                # correct for bug due to mask assignment with different resolution
                if np.max(mask_remapped[x, y : y + 5]) != 0:
                    continue
                else:
                    ymax = y
                    first = False
                    l_rows.extend([ymin, ymax - 1])
        if len(l_rows) > 1:
            ll_rows.append(l_rows)

    if len(ll_rows) > 0:
        xmin = ll_rows[0][0]
        xmax = ll_rows[-1][0]
        max_len = max([len(l_rows) - 1 for l_rows in ll_rows])
    else:
        xmax = 0
        xmin = 0
        max_len = 0
    # Convert list of np.array to np array padded with zeros (for numba compatibility...)
    array_index_bound_column_per_row = np.zeros((xmax - xmin + 1, max_len), dtype=np.int32)
    for i, l_rows in enumerate(ll_rows):
        array_index_bound_column_per_row[i, : len(l_rows) - 1] = l_rows[1:]

    return np.array([xmin, xmax], dtype=np.int32), array_index_bound_column_per_row

