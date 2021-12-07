###### IMPORT MODULES ######

# Official modules
import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
import plotly.graph_objects as go
from bg_atlasapi import BrainGlobeAtlas
from PIL import Image
import base64
from io import BytesIO
from matplotlib import cm
import plotly.express as px
import skimage
import warnings
import logging
import io
from imageio import imread

# Homemade functions
from lbae.modules.tools.atlas import (
    project_atlas_mask,
    get_array_rows_from_atlas_mask,
    fill_array_projection,
    solve_plane_equation,
)
from lbae.modules.tools.spectra import compute_spectrum_per_row_selection
from lbae.modules.atlas_labels import Labels, LabelContours
from lbae.modules.tools.misc import return_pickled_object, convert_image_to_base64
from lbae.modules.tools.memuse import logmem

#! Overall, see if I can memmap all the objects in this class

###### Atlas Class ######
class Atlas:
    def __init__(self, maldi_data, resolution=25):

        logging.info("Initializing Atlas object" + logmem())

        # Resolution of the atlas, to be chosen among 10um, 25um or 100um
        if resolution in (10, 25, 100):
            self.resolution = resolution
        else:
            logging.warning("The resolution you chose is not available, using the default of 25um")
            self.resolution = 25

        self.data = maldi_data

        # Load or download the atlas if it's the first time
        brainglobe_dir = "lbae/data/atlas/brain_globe/"
        os.makedirs(brainglobe_dir, exist_ok=True)
        self.bg_atlas = BrainGlobeAtlas(
            "allen_mouse_" + str(resolution) + "um", brainglobe_dir=brainglobe_dir, check_latest=False
        )

        # When computing an array of figures with a slider to explore the atlas, subsample in the longitudinal
        # direction, otherwise it's too heavy
        self.subsampling_block = 20

        # Load string annotation for contour plot, for each voxel.
        # These objects are heavy as they force the loading of annotations from the core Atlas class. But they shouldn't
        # be memory-mapped as they are called when hovering and require very fast response from the server
        self.labels = Labels(self.bg_atlas, force_init=True)
        self._simplified_labels_int = None

        # Load array of coordinates for warped data (can't be pickled as used with hovering)
        self.array_coordinates_warped_data = np.array(
            skimage.io.imread("lbae/data/tiff_files/coordinates_warped_data.tif"), dtype=np.float32
        )

        # Record shape of the warped data
        self.image_shape = list(self.array_coordinates_warped_data.shape[1:-1])

        # Record dict that associate brain region to specific id, along with graph of structures
        self.l_nodes, self.l_parents, self.dic_name_id = return_pickled_object(
            "atlas/atlas_objects", "hierarchy", force_update=False, compute_function=self.compute_hierarchy_list
        )

    # Load arrays of images using atlas projection
    @property
    def array_projection_corrected(self):
        (array_projection_corrected, _, _,) = return_pickled_object(
            "atlas/atlas_objects",
            "arrays_projection_corrected",
            force_update=False,
            compute_function=self.compute_array_projection,
            nearest_neighbour_correction=True,
            atlas_correction=True,
        )
        return array_projection_corrected

    @property
    def array_projection_correspondence_corrected(self):
        (_, array_projection_correspondence_corrected, _,) = return_pickled_object(
            "atlas/atlas_objects",
            "arrays_projection_corrected",
            force_update=False,
            compute_function=self.compute_array_projection,
            nearest_neighbour_correction=True,
            atlas_correction=True,
        )
        return array_projection_correspondence_corrected

    @property
    def l_original_coor(self):
        (_, _, l_original_coor,) = return_pickled_object(
            "atlas/atlas_objects",
            "arrays_projection_corrected",
            force_update=False,
            compute_function=self.compute_array_projection,
            nearest_neighbour_correction=True,
            atlas_correction=True,
        )
        return l_original_coor

    # Compute the dictionnary of unique identifiers for the label only if needed
    @property
    def simplified_labels_int(self):
        if self._simplified_labels_int is None:
            self._simplified_labels_int = LabelContours(self.bg_atlas)
        return self._simplified_labels_int

    # Load array of projected atlas borders
    @property
    def list_projected_atlas_borders_arrays(self):
        return return_pickled_object(
            "atlas/atlas_objects",
            "list_projected_atlas_borders_arrays",
            force_update=False,
            compute_function=self.compute_list_projected_atlas_borders_figures,
        )

    def compute_hierarchy_list(self):

        # Create a list of parents for all ancestors
        l_nodes = []
        l_parents = []
        dic_name_id = {}
        idx = 0
        for x, v in self.bg_atlas.structures.items():
            if len(self.bg_atlas.get_structure_ancestors(v["acronym"])) > 0:
                ancestor_acronym = self.bg_atlas.get_structure_ancestors(v["acronym"])[-1]
                ancestor_name = self.bg_atlas.structures[ancestor_acronym]["name"]
            else:
                ancestor_name = ""
            current_name = self.bg_atlas.structures[x]["name"]

            l_nodes.append(current_name)
            l_parents.append(ancestor_name)
            dic_name_id[current_name] = v["acronym"]

        return l_nodes, l_parents, dic_name_id

    def compute_array_projection(self, nearest_neighbour_correction=False, atlas_correction=False):

        array_projection = np.zeros(self.array_coordinates_warped_data.shape[:-1], dtype=np.int16)
        array_projection_filling = np.zeros(array_projection.shape, dtype=np.int16)

        # This array makes the correspondence between the original data coordinates and the new ones
        array_projection_correspondence = np.zeros(array_projection.shape + (2,), dtype=np.int16)
        array_projection_correspondence.fill(-1)

        # list of orginal coordinates
        l_original_coor = []
        l_transform_parameters = return_pickled_object(
            "atlas/atlas_objects",
            "l_transform_parameters",
            force_update=False,
            compute_function=self.compute_projection_parameters,
        )
        for i in range(array_projection.shape[0]):
            # print("slice " + str(i) + " getting processed")
            a, u, v = l_transform_parameters[i]

            # load corresponding slice and coor
            path = "lbae/data/tiff_files/coordinates_original_data/"
            filename = path + [x for x in os.listdir(path) if str(i + 1) == x.split("slice_")[1].split(".tiff")[0]][0]
            original_coor = np.array(skimage.io.imread(filename), dtype=np.float32)
            l_original_coor.append(original_coor)

            path = "lbae/data/tiff_files/original_data/"
            filename = path + [x for x in os.listdir(path) if str(i + 1) == x.split("slice_")[1].split(".tiff")[0]][0]
            original_slice = np.array(skimage.io.imread(filename), dtype=np.int16)

            # map back the pixel from the atlas coordinates
            array_projection, array_projection_correspondence = fill_array_projection(
                i,
                array_projection,
                array_projection_filling,
                array_projection_correspondence,
                original_coor,
                self.resolution,
                a,
                u,
                v,
                original_slice,
                self.array_coordinates_warped_data,
                self.bg_atlas.annotation,
                nearest_neighbour_correction=nearest_neighbour_correction,
                atlas_correction=atlas_correction,
            )

        return array_projection, array_projection_correspondence, l_original_coor

    def compute_projection_parameters(self):
        l_transform_parameters = []
        for slice_index in range(self.array_coordinates_warped_data.shape[0]):
            a_atlas, u_atlas, v_atlas = solve_plane_equation(slice_index, self.array_coordinates_warped_data)
            l_transform_parameters.append((a_atlas, u_atlas, v_atlas))
        return l_transform_parameters

    def compute_list_projected_atlas_borders_figures(self):
        l_array_images = []
        # Load array of atlas images corresponding to our data and how it is projected
        array_projected_images_atlas, array_projected_simplified_id = return_pickled_object(
            "atlas/atlas_objects",
            "array_images_atlas",
            force_update=False,
            compute_function=self.compute_array_images_atlas,
        )

        for slice_index in range(array_projected_simplified_id.shape[0]):

            contours = (
                array_projected_simplified_id[slice_index, 1:, 1:]
                - array_projected_simplified_id[slice_index, :-1, :-1]
            )
            contours = np.clip(contours ** 2, 0, 1)
            contours = np.pad(contours, ((1, 0), (1, 0)))
            # do some cleaning on the sides
            contours[:, :10] = 0
            contours[:, -10:] = 0
            contours[:10, :] = 0
            contours[-10:, :] = 0

            fig = plt.figure(frameon=False)
            dpi = 100
            fig.set_size_inches(contours.shape[1] / dpi, contours.shape[0] / dpi)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis("off")
            prefix = "data:image/png;base64,"
            plt.contour(contours, colors="orange", antialiased=True, linewidths=0.2, origin="image")
            with BytesIO() as stream:
                plt.savefig(stream, format="png", dpi=dpi)
                plt.close()
                img = imread(io.BytesIO(stream.getvalue()))
                l_array_images.append(img)

        return l_array_images

    def compute_array_images_atlas(self):
        array_images = np.empty(self.array_coordinates_warped_data.shape[:-1], dtype=np.uint8)
        array_projected_simplified_id = np.full(
            array_images.shape, self.simplified_labels_int[0, 0, 0], dtype=np.int32
        )

        array_coor_rescaled = ((self.array_coordinates_warped_data * 1000 / self.resolution).round(0)).astype(np.int16)
        for x in range(array_images.shape[0]):
            for y in range(array_images.shape[1]):
                for z in range(array_images.shape[2]):
                    if (
                        min(array_coor_rescaled[x, y, z]) >= 0
                        and array_coor_rescaled[x, y, z][0] < self.bg_atlas.reference.shape[0]
                        and array_coor_rescaled[x, y, z][1] < self.bg_atlas.reference.shape[1]
                        and array_coor_rescaled[x, y, z][2] < self.bg_atlas.reference.shape[2]
                    ):
                        array_images[x, y, z] = self.bg_atlas.reference[tuple(array_coor_rescaled[x, y, z])]
                        array_projected_simplified_id[x, y, z] = self.simplified_labels_int[
                            tuple(array_coor_rescaled[x, y, z])
                        ]
                    else:
                        array_images[x, y, z] = 0
        return array_images, array_projected_simplified_id

    def get_atlas_mask(self, structure):

        structure_id = self.bg_atlas.structures[structure]["id"]
        descendants = self.bg_atlas.get_structure_descendants(structure)

        mask_stack = np.zeros(self.bg_atlas.shape, self.bg_atlas.annotation.dtype)
        mask_stack[self.bg_atlas.annotation == structure_id] = structure_id

        # for descendant in descendants:
        #    descendant_id = bg_atlas.structures[descendant]["id"]
        #    mask_stack[bg_atlas.annotation == descendant_id] = structure_id

        return mask_stack

    def compute_spectrum_data(self, slice_index, projected_mask=None, mask_name=None, slice_coor_rescaled=None):
        if projected_mask is None and mask_name is None:
            print("Either a mask or a mask name must be provided")
            return None
        elif mask_name is not None:
            if slice_coor_rescaled is None:
                slice_coor_rescaled = np.asarray(
                    (self.array_coordinates_warped_data[slice_index, :, :] * 1000 / self.resolution).round(0),
                    dtype=np.int16,
                )
            stack_mask = self.get_atlas_mask(self.dic_name_id[mask_name])
            projected_mask = project_atlas_mask(stack_mask, slice_coor_rescaled, self.bg_atlas.reference.shape)

        # get the list of rows containing the pixels to average
        original_shape = self.data.get_image_shape(slice_index + 1)
        mask_remapped = np.zeros(original_shape, dtype=np.uint8)
        list_index_bound_rows, list_index_bound_column_per_row = get_array_rows_from_atlas_mask(
            projected_mask, mask_remapped, self.array_projection_correspondence_corrected[slice_index],
        )
        if np.sum(list_index_bound_rows) == 0:
            print("No selection could be found for current mask")
            grah_scattergl_data = None
        else:
            # do the average
            grah_scattergl_data = compute_spectrum_per_row_selection(
                list_index_bound_rows,
                list_index_bound_column_per_row,
                self.data.get_array_spectra(slice_index + 1),
                self.data.get_array_lookup_pixels(slice_index + 1),
                original_shape,
                zeros_extend=False,
            )
        return grah_scattergl_data

    def compute_dic_projected_masks_and_spectra(self, slice_index):
        dic = {}
        slice_coor_rescaled = np.asarray(
            (self.array_coordinates_warped_data[slice_index, :, :] * 1000 / self.resolution).round(0), dtype=np.int16,
        )

        # Get hierarchical tree of brain structures -
        for mask_name, id_mask in self.dic_name_id.items():
            # get the array corresponding to the projected mask
            stack_mask = self.get_atlas_mask(id_mask)
            projected_mask = project_atlas_mask(stack_mask, slice_coor_rescaled, self.bg_atlas.reference.shape)
            if np.sum(projected_mask) == 0:
                continue

            # compute orange image
            normalized_projected_mask = projected_mask / np.max(projected_mask)
            # clean mask
            normalized_projected_mask[:, :10] = 0
            normalized_projected_mask[:, -10:] = 0
            normalized_projected_mask[:10, :] = 0
            normalized_projected_mask[-10:, :] = 0

            color_rgb = [255, 140, 0, 200]
            l_images = [normalized_projected_mask * color for c, color in zip(["r", "g", "b", "a"], color_rgb)]
            # Reoder axis to match plotly go.image requirements
            array_image = np.moveaxis(np.array(l_images, dtype=np.uint8), 0, 2)
            base64_string = convert_image_to_base64(array_image, optimize=True, quality=5, type="RGBA", format="gif")
            im = go.Image(visible=True, source=base64_string, hoverinfo="none")

            # compute spectrum
            grah_scattergl_data = self.compute_spectrum_data(slice_index, projected_mask)

            dic[mask_name] = (projected_mask, grah_scattergl_data, im)
        return dic

    """

   




    def return_3D_figure(self, structure=None, from_pickle=True, default_force_pickle=True):
        force_pickle = False
        # quick fix when no structure is provided
        if structure is None:
            path = "data/pickled_data/atlas_3D_data/figure_atlas_3D" + ".pickle"
        else:
            path = "data/pickled_data/atlas_3D_data/figure_atlas_3D_" + structure.replace("/", "-") + ".pickle"
        if from_pickle:
            try:
                with open(path, "rb",) as file:
                    return pickle.load(file)
            except:
                print("The file " + path + " could not be found. Rebuilding the 3D figure now.")
                if default_force_pickle:
                    print("The 3D figure will also be pickled.")
                force_pickle = True

        fig = self.compute_3D_figure(structure=structure, root_from_pickle=True)
        if force_pickle:
            print("Pickling the 3D figure now")
            with open(path, "wb") as file:
                pickle.dump(fig, file)
        return fig

    def pickle_all_3D_figures(self, force_recompute=False):
        path = "data/pickled_data/atlas_3D_data/"
        existing_figures = set([x.split("_")[-1].split(".pickle")[0].replace("-", "/") for x in os.listdir(path)])
        for v in self.bg_atlas.structures.values():
            acronym = v["acronym"]
            if (acronym in existing_figures and force_recompute) or (acronym not in existing_figures):
                try:
                    self.return_3D_figure(structure=acronym, from_pickle=True, default_force_pickle=True)
                except:
                    print("Structure " + acronym + " could not be computed")
            else:
                print(acronym + " has already been computed before. Skipping it.")
    """
