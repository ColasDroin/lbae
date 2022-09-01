# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, functions linking the MALDI data to the CCFv3 (e.g. getting mask or resolution 
change) are defined.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard import
import logging
import numpy as np
from numba import njit

# ==================================================================================================
# --- Functions
# ==================================================================================================


@njit
def project_image(slice_index, original_image, array_projection_correspondence):
    """This function is used to project the original maldi acquisition (low-resolution, possibly
    tilted, and) into a warped and higher resolution, indexed with the Allen Mouse Brain Common
    Coordinate Framework (ccfv3).

    Args:
        slice_index (int): Index of the slice to project.
        original_image (np.ndarray): A two-dimensional array representing the MADI data of the
            current slice (e.g. for a given lipid selection).
        array_projection_correspondence (np.ndarray): A three-dimensional array which associates, to
            each triplet of coordinates of the original acquisition (slice_index, row_index,
            column_index), a tuple of coordinates corresponding to the row_index and column_index of
            the warped higher-resolution image.

    Returns:
        (np.ndarray): A warped, high-resolution image, corresponding to the clean, registered version,
            of our acquisition.
    """
    # Correct index as slice names start at 1
    slice_index -= 1

    # Define empty array for the high-resolution image
    new_image = np.zeros(array_projection_correspondence.shape[1:-1], dtype=original_image.dtype)

    # Exclude the borders of the image to gain some time
    for i in range(50, array_projection_correspondence[slice_index].shape[0] - 50):
        for j in range(50, array_projection_correspondence[slice_index].shape[1] - 50):
            # Maps the original coordinates to the new one, with coordinate -1 corresponding
            # to unassigned
            if array_projection_correspondence[slice_index, i, j, 0] != -1:
                x, y = array_projection_correspondence[slice_index, i, j]
                new_image[i, j] = original_image[x, y]

    return new_image


@njit
def project_atlas_mask(stack_mask, slice_coordinates_rescaled, shape_atlas):
    """This function projects a mask array_annotation (obtained from the atlas, sliced from a
    3-dimensional object) on our two-dimensional, high-resolution warped data, for a given slice.

    Args:
        stack_mask (np.ndarray): A three-dimensional array indexed with the ccfv3. It contains a
            zero if the selected coordinate is outside the mask array_annotation, and 1 otherwise.
        slice_coordinates_rescaled (np.ndarray): A two-dimensional array mapping our slice
            coordinate (rescaled and discretized) to the ccfv3.
        shape_atlas (tuple(int)): A tuple of three integers representing the shape of the
            ccfv3-indexed atlas.

    Returns:
        (np.ndarray): A two-dimensional array representing the projected mask on the requested slice.
    """
    # Define empty array for the projected mask, with the same dimension as the current slice
    # ! Delete this comment if everything is working, else switch back to int16 or int32
    projected_mask = np.full(
        slice_coordinates_rescaled.shape[:-1], stack_mask[0, 0, 0], dtype=np.uint8
    )
    for x in range(slice_coordinates_rescaled.shape[0]):
        for y in range(slice_coordinates_rescaled.shape[1]):
            current_coor_rescaled = slice_coordinates_rescaled[x, y]
            # If the current slice coordinate actually exists in the atlas, maps it to the
            # corresponding mask value
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
def get_array_rows_from_atlas_mask(mask, mask_remapped, array_projection_correspondence_sliced):
    """This function is similar to spectra.sample_rows_from_path(), in that it returns the lower and
    upper indexes of the rows belonging to the current mask (instead of path), as well as the
    corresponding column boundaries for each row.

    Args:
        mask (np.ndarray): A two-dimensional array representing the (high-resolution, warped) mask
            projected on the requested slice.
        mask_remapped (np.ndarray): An empty two-dimensional array of the shape of the original
            acquisition, passed a parameter as numba won't allow for np.uint8 creation inside of the
            scope of the function. It is initially filled with the high-resolution warped mask
            values, whose coordinates have been mapped back to the original data.
        array_projection_correspondence_sliced (np.ndarray): A two-dimensional array which
            associates, to each couple of coordinates of the original acquisition (row_index,
            column_index), a tuple of coordinates corresponding to the row_index and column_index of
            the warped higher-resolution image.

    Returns:
        (np.ndarray, np.ndarray): The first array contains the lower and upper indexes of the rows
            belonging to the mask. The second array contains, for each row, the corresponding column
            boundaries of the mask (there can be more than 2 for non-convex shapes).
    """
    # Map back the mask coordinates to original data
    for x in range(mask.shape[0]):
        for y in range(mask.shape[1]):
            x_original, y_original = array_projection_correspondence_sliced[x, y]
            if (
                x_original >= 0
                and x_original < mask_remapped.shape[0]
                and y_original >= 0
                and y_original < mask_remapped.shape[0]
            ):
                mask_remapped[x_original, y_original] = mask[x, y]

    # Then compute the column boundaries for each row
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
                # Correct for bug due to mask assignment with different resolution
                if np.max(mask_remapped[x, y : y + 5]) != 0:
                    continue
                else:
                    ymax = y
                    first = False
                    l_rows.extend([ymin, ymax - 1])

        # If two boundaries have been obtained, add them to the list
        if len(l_rows) > 1:
            ll_rows.append(l_rows)

    # Get the indices of the first and last rows
    if len(ll_rows) > 0:
        xmin = ll_rows[0][0]
        xmax = ll_rows[-1][0]
        max_len = max([len(l_rows) - 1 for l_rows in ll_rows])
    else:
        xmax = 0
        xmin = 0
        max_len = 0

    # Convert list of np.array to np array padded with zeros (for numba compatibility)
    array_index_bound_column_per_row = np.zeros((xmax - xmin + 1, max_len), dtype=np.int32)
    for i, l_rows in enumerate(ll_rows):
        array_index_bound_column_per_row[i, : len(l_rows) - 1] = l_rows[1:]

    return np.array([xmin, xmax], dtype=np.int32), array_index_bound_column_per_row


@njit
def solve_plane_equation(
    array_coordinates_high_res_slice,
    point_1=(50, 51),
    point_2=(200, 200),
    point_3=(100, 101),
):
    """This function defines and solves a system of linear equations for three points of the plane
    (which corresponds to a slice in the ccfv3). The vectors returned by the function enable to
    index the 2D slice in the 3D atlas space (ccfv3), cf. slice_to_atlas_transform(). Note that the
    three points can not be taken at the extremities of the slice, as the registration made with
    ABBA is buggued and the origin doesn't linearly maps to the 3D plane.

    Args:
        array_coordinates_high_res_slice (np.ndarray): A two-dimensional array which maps the
            high-dimensional warped data to the atlas coordinate system. That is, for each 2-D
            coordinate (x,y), it associates a 3D coordinate (i,j,k) in the ccfv3.
        point_1 (tuple, optional): Couple of coordinates corresponding to the first point indexed on
            the 3D plane. Defaults to (50, 51).
        point_2 (tuple, optional): Couple of coordinates corresponding to the first point indexed on
            the 3D plane. Defaults to (400, 200).
        point_3 (tuple, optional): Couple of coordinates corresponding to the first point indexed on
            the 3D plane. Defaults to (100, 101).

    Returns:
        (tuple(float), tuple(float), tuple(float)): Three vectors allowing to parametrize the
            coordinate of our slice in the ccfv3.
    """
    # Define empty array for the linear system of equations
    A = np.zeros((9, 9), dtype=np.float32)
    b = np.zeros((9,), dtype=np.float32)

    # Fill the matrices, such that Ax=b, where A represents the projection from 2D coordinates (x)
    # to the ccfv3 (b)
    A[0] = [point_1[0], 0, 0, point_1[1], 0, 0, 1, 0, 0]
    A[1] = [0, point_1[0], 0, 0, point_1[1], 0, 0, 1, 0]
    A[2] = [0, 0, point_1[0], 0, 0, point_1[1], 0, 0, 1]
    A[3] = [point_2[0], 0, 0, point_2[1], 0, 0, 1, 0, 0]
    A[4] = [0, point_2[0], 0, 0, point_2[1], 0, 0, 1, 0]
    A[5] = [0, 0, point_2[0], 0, 0, point_2[1], 0, 0, 1]
    A[6] = [point_3[0], 0, 0, point_3[1], 0, 0, 1, 0, 0]
    A[7] = [0, point_3[0], 0, 0, point_3[1], 0, 0, 1, 0]
    A[8] = [0, 0, point_3[0], 0, 0, point_3[1], 0, 0, 1]

    b[0] = array_coordinates_high_res_slice[point_1[0], point_1[1], 0]
    b[1] = array_coordinates_high_res_slice[point_1[0], point_1[1], 1]
    b[2] = array_coordinates_high_res_slice[point_1[0], point_1[1], 2]
    b[3] = array_coordinates_high_res_slice[point_2[0], point_2[1], 0]
    b[4] = array_coordinates_high_res_slice[point_2[0], point_2[1], 1]
    b[5] = array_coordinates_high_res_slice[point_2[0], point_2[1], 2]
    b[6] = array_coordinates_high_res_slice[point_3[0], point_3[1], 0]
    b[7] = array_coordinates_high_res_slice[point_3[0], point_3[1], 1]
    b[8] = array_coordinates_high_res_slice[point_3[0], point_3[1], 2]

    # Invert the system of equation
    u1, u2, u3, v1, v2, v3, a1, a2, a3 = np.linalg.solve(A, b)
    u_atlas = (u1, u2, u3)
    v_atlas = (v1, v2, v3)
    a_atlas = (a1, a2, a3)
    return a_atlas, u_atlas, v_atlas


@njit
def slice_to_atlas_transform(a, u, v, lambd, mu):
    """This function returns a 3D coordinate (in the ccfv3) from a 2D slice coordinate, using the
    parameters obtained from the inversion made in solve_plane_equation().

    Args:
        a (tuple(float)): The first of the three vectors used to parametrize the plane is space.
        u (tuple(float)): The second of the three vectors used to parametrize the plane in space.
        v (tuple(float)): The third of the three vectors used to parametrize the plane in space.
        lambd (int): The first coordinate of our slice (height of the required point).
        mu (int): The second coordinate of our slice (width of the required point).

    Returns:
        (int, int, int): A 3D coordinate in the ccfv3, mapping our flat (2D) data to the atlas
            coordinate system.
    """
    # Equation of a plan in space
    x_atlas = a[0] + lambd * u[0] + mu * v[0]
    y_atlas = a[1] + lambd * u[1] + mu * v[1]
    z_atlas = a[2] + lambd * u[2] + mu * v[2]
    return x_atlas, y_atlas, z_atlas


@njit
def fill_array_projection(
    slice_index,
    array_projection,
    array_projection_filling,
    array_projection_correspondence,
    original_coor,
    atlas_resolution,
    a,
    u,
    v,
    original_slice,
    array_coordinates_high_res_slice,
    array_annotation,
    nearest_neighbour_correction=False,
    atlas_correction=False,
    sample_data=False,
):
    """This function computes the correspondance between our initial, low-resolution, data from the
    MALDI imaging, to the high-resolution space in which the registered data lives. To that end, it
    computes and returns two arrays (which are passed as imputs, although empty, since numba won't
    accept to create them in the scope of the function) : array_projection, which is the
    high-resolution version of our initial data, in which each individual pixel has been mapped
    according to the second array, array_projection_correspondence.

    Args:
        slice_index (int): Index of the slice to parametrize in space.
        array_projection (np.ndarray): An empty, high-resolution, three-dimensional array which, at
            the end of the function, should contain the data (one integer per coordinate,
            corresponding to a pixel intensity) from our original acquisition. Note that, if no
            correction is applied, since the original acquisition has a way lower resolution than
            array_projection, the latter may be quite sparse.
        array_projection_filling (np.ndarray): An empty, high-resolution, three-dimensional array
            which is used to keep track of the state of array_projection; that is, which elements
            have already been filled.
        array_projection_correspondence (np.ndarray): An empty three-dimensional array which, at the
            end of the function, associates, to each tripled of coordinates of the original
            acquisition (slice_index, row_index, column_index), a tuple of coordinates corresponding
            to the row_index and column_index of the warped higher-resolution image.
        original_coor (np.ndarray): A two-dimensional array which maps our initial (low-resolution)
            data to the atlas coordinate system. That is, for each 2-D coordinate (x,y), it
            associates a 3D coordinate (i,j,k) in the ccfv3.
        atlas_resolution (int): The resolution used for the atlas, in um.
        a (tuple(float)): The first of the three vectors used to parametrize the plane is space.
        u (tuple(float)): The second of the three vectors used to parametrize the plane in space.
        v (tuple(float)): The third of the three vectors used to parametrize the plane in space.
        original_slice (np.ndarray): A two-dimensional array representing an image of the MALDI
            acquisition.
        array_coordinates_high_res_slice (np.ndarray): A two-dimensional array which maps the
            high-dimensional warped data to the atlas coordinate system. That is, for each 2-D
            coordinate (x,y), it associates a 3D coordinate (i,j,k) in the ccfv3.
        array_annotation (np.ndarray): A three-dimensional array containing the atlas annotation,
            used to filter out the regions of our data which are outside the annotated brain, if
            atlas_correction is True.
        nearest_neighbour_correction (bool, optional): If True, applies a neared-neighbour
            correction, that is, for every empty pixel far from the image boundaries, it looks for
            neighbours that are filled in a close window, and used the most represented value to
            fill the empty pixel. Defaults to False.
        atlas_correction (bool, optional): If True, filters out pixels that are not annotated in the
            ccfv3. Defaults to False.
        sample_data (bool, optional): If True, the function will use the sampled version of the
            slice data for the computations. Defaults to False.

    Returns:
        (np.ndarray, np.ndarray): The first array is a high-resolution version of our initial data, in
            which each individual pixel has been mapped according to the second array, which acts as
            a mapping table.
    """

    # Start by inverting a simple system of linear equations for each coordinate in the initial data
    # to find the corresponding coordinate in the high-resolution space (this is not a trivial
    # problem as slices can be tilted)
    A = np.empty((2, 2), dtype=np.float64)
    A[0] = [u[1], v[1]]
    A[1] = [u[2], v[2]]
    A += np.random.normal(
        0, 0.000000001, (2, 2)
    )  # add small noise to solve singularity issues when inversion

    for i_original_slice in range(original_coor.shape[0]):
        for j_original_slice in range(original_coor.shape[1]):
            x_atlas, y_atlas, z_atlas = original_coor[i_original_slice, j_original_slice]

            # Solve the system of linear equations
            b = np.array([y_atlas - a[1], z_atlas - a[2]], dtype=np.float64)
            i, j = np.linalg.solve(A, b)

            # Ugly but numba won't accept any other way
            i = int(round(i))
            j = int(round(j))

            # If the high-resolution coordinate found be inversion exists, fill array_projection
            if i < array_projection.shape[1] and j < array_projection.shape[2] and i > 0 and j > 0:
                try:
                    array_projection[slice_index, i, j] = original_slice[
                        i_original_slice, j_original_slice
                    ]
                    array_projection_filling[slice_index, i, j] = 1
                    array_projection_correspondence[slice_index, i, j] = [
                        i_original_slice,
                        j_original_slice,
                    ]
                except:
                    print(
                        i,
                        j,
                        array_projection.shape,
                        i_original_slice,
                        j_original_slice,
                        original_slice.shape,
                    )
                    raise ValueError

    # Apply potential corrections
    if nearest_neighbour_correction or atlas_correction:
        for i in range(array_projection.shape[1]):
            for j in range(array_projection.shape[2]):
                # Look for the 3D atlas coordinate of out data
                x_atlas, y_atlas, z_atlas = (
                    array_coordinates_high_res_slice[i, j] * 1000 / atlas_resolution
                )

                # Ugly again, but numba doesn't support np.round
                x_atlas = int(round(x_atlas))
                y_atlas = int(round(y_atlas))
                z_atlas = int(round(z_atlas))

                # If the current coordinate is contained in the ccfv3, proceed
                if (
                    x_atlas < array_annotation.shape[0]
                    and x_atlas >= 0
                    and y_atlas < array_annotation.shape[1]
                    and y_atlas >= 0
                    and z_atlas < array_annotation.shape[2]
                    and z_atlas >= 0
                ):
                    # If the current annotation in the ccfv3 maps to an existing structure
                    if array_annotation[x_atlas, y_atlas, z_atlas] != 0:
                        # Nearest neighbour correction to fill most of the empty pixels in the
                        # high-resolution image
                        if nearest_neighbour_correction:
                            # If the pixel hasn't already been dealt with before (because of the
                            # way the projection is done and warping, this may happen)
                            if array_projection_filling[slice_index, i, j] == 0:
                                # Only fill missing areas if far from the sides
                                if (
                                    i > 20
                                    and i < array_projection.shape[1] - 20
                                    and j > 20
                                    and j < array_projection.shape[2] - 20
                                ):
                                    # Look for neighbours that are filled in a close window
                                    radius = 3
                                    array_window = np.empty(
                                        (2 * radius + 1, 2 * radius + 1), dtype=np.float32
                                    )

                                    # Temporary fill the window not to modify the value as they are
                                    # browsed and end up having an incremental nearest neighbor
                                    # correction
                                    for x in range(-radius, radius + 1):
                                        for y in range(-radius, radius + 1):
                                            if (
                                                i + x > 0
                                                and i + x < array_projection.shape[1]
                                                and j + x > 0
                                                and j + y < array_projection.shape[2]
                                            ):
                                                if (
                                                    array_projection_filling[
                                                        slice_index, i + x, j + y
                                                    ]
                                                    == 0
                                                ):
                                                    array_window[x + radius, y + radius] = np.nan
                                                else:
                                                    array_window[
                                                        x + radius, y + radius
                                                    ] = array_projection[slice_index, i + x, j + y]
                                    avg = np.nanmean(array_window)
                                    if np.isnan(avg):
                                        continue
                                    clean_window = np.abs(array_window - avg)
                                    # Numba doesn't support nanargmin, so I have to implement it
                                    # myself...
                                    mini = 10000
                                    selected_pixel_x = 0
                                    selected_pixel_y = 0
                                    for x in range(2 * radius + 1):
                                        for y in range(2 * radius + 1):
                                            if clean_window[x, y] < mini:
                                                mini = clean_window[x, y]
                                                selected_pixel_x = x
                                                selected_pixel_y = y

                                    # Fill the pixel in array projection with the most represented
                                    # value in the window
                                    array_projection[slice_index, i, j] = array_window[
                                        selected_pixel_x, selected_pixel_y
                                    ]
                                    array_projection_correspondence[
                                        slice_index, i, j
                                    ] = array_projection_correspondence[
                                        slice_index,
                                        i + selected_pixel_x - radius,
                                        j + selected_pixel_y - radius,
                                    ]
                    # Wipe the pixels values that are not annotated in the atlas
                    elif atlas_correction:
                        array_projection[slice_index, i, j] = 0
                        array_projection_filling[slice_index, i, j] = 1
                        array_projection_correspondence[slice_index, i, j] = [-1, -1]

                # Wipe the pixels values that are not in the ccfv3
                elif atlas_correction:
                    array_projection[slice_index, i, j] = 0
                    array_projection_filling[slice_index, i, j] = 1
                    array_projection_correspondence[slice_index, i, j] = [-1, -1]

    return array_projection, array_projection_correspondence


@njit
def compute_simplified_atlas_annotation(atlas_annotation):
    """This function is used to map the array of annotations (which can initially be very large
    integers) to an array of annotations of similar size, but with annotations ranging from 0 to the
    number of structures in the atlas.

    Args:
        atlas_annotation (np.ndarray): Initial 3D array of annotations.

    Returns:
        (np.ndarray): Simplified 3D array of annotations.
    """
    # Compute an array which map labels ids to increasing integers
    unique_id_dic = {ni: indi for indi, ni in enumerate(set(atlas_annotation.flatten()))}

    simplified_atlas_annotation = np.zeros(atlas_annotation.shape, dtype=np.int32)
    for x in range(atlas_annotation.shape[0]):
        for y in range(atlas_annotation.shape[1]):
            for z in range(atlas_annotation.shape[2]):
                simplified_atlas_annotation[x, y, z] = unique_id_dic[atlas_annotation[x, y, z]]

    return simplified_atlas_annotation


@njit
def compute_array_images_atlas(
    array_coordinates_warped_data,
    simplified_atlas_annotation,
    atlas_reference,
    resolution,
    zero_out_of_annotation=False,
):
    """This function is used to build a list of atlas images corresponding to the slices acquired
    during the MALDI acquisition.

    Args:
        array_coordinates_warped_data (np.ndarray): Array of coordinates of the warped,
            high-resolution slices.
        simplified_atlas_annotation (np.ndarray): Simplified 3D array of annotations.
        atlas_reference (np.ndarray): 3D array of the atlas data.
        resolution (int): Resolution of the atlas.
        zero_out_of_annotation (bool, optional): If True, the produced set of images is such that
            all the data that doesn't belong to a given structure is zeroed-out. Defaults to False.

    Returns:
        (np.ndarray, np.ndarray): The first array is basically a list of atlas images corresponding
            to the slices acquired during the MALDI acquisition. The second array is the
            corresponding set of annotations.
    """
    array_images = np.zeros(array_coordinates_warped_data.shape[:-1], dtype=np.uint8)
    array_projected_simplified_id = np.full(
        array_images.shape, simplified_atlas_annotation[0, 0, 0], dtype=np.int32
    )

    array_coor_rescaled = np.empty_like(array_coordinates_warped_data, dtype=np.int16)
    # Inplace rounding for numba
    np.round_(array_coordinates_warped_data * 1000 / resolution, 0, array_coor_rescaled)
    for x in range(array_images.shape[0]):
        for y in range(array_images.shape[1]):
            for z in range(array_images.shape[2]):
                if (
                    min(array_coor_rescaled[x, y, z]) >= 0
                    and array_coor_rescaled[x, y, z][0] < atlas_reference.shape[0]
                    and array_coor_rescaled[x, y, z][1] < atlas_reference.shape[1]
                    and array_coor_rescaled[x, y, z][2] < atlas_reference.shape[2]
                ):
                    l, m, n = array_coor_rescaled[x, y, z]
                    array_projected_simplified_id[x, y, z] = simplified_atlas_annotation[l, m, n]
                    if array_projected_simplified_id[x, y, z] == 0 and zero_out_of_annotation:
                        continue
                    else:
                        array_images[x, y, z] = atlas_reference[l, m, n]
                else:
                    array_images[x, y, z] = 0

    # Correct for bug on inferior right margin
    array_images[:, :, :10] = 0

    return array_images, array_projected_simplified_id
