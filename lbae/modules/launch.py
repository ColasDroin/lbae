# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains a class with functions used to do check and run all precomputation at first 
app launch."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import logging
import shelve

# ==================================================================================================
# --- Class
# ==================================================================================================


class Launch:
    """ Class used to precompute and shelve objects at app launch.
    
    Attributes:
    # ! TODO
    
    Methods:
    
    """

    def __init__(self, data, atlas, figures):
        """Initialize the class Launch.

        Args:
            data (MaldiData): MaldiData object, used to manipulate the raw MALDI data.
            atlas (Atlas): Atlas object, used to manipulate the objects coming from the Allen Brain 
                Atlas.
            figures (Figures): Figures object, used to build the figures of the app.
            # ! Complete
        """

        # App main objects
        self.data = data
        self.atlas = atlas
        self.figures = figures

        # Objects to shelve in the Atlas class. Everything in this list is shelved at
        # initialization of Atlas and Figures objects. The computations described are the ones done
        # at startup.
        self.atlas_objects_at_init = [
            # Computed in Atlas.__init__() as an argument of Atlas. Corresponds to the object
            # returned by Atlas.compute_dic_acronym_children_id()
            "atlas/atlas_objects/dic_acronym_children_id",
            #
            # Computed in Atlas.__init__() as an argument of Atlas. Corresponds to the object
            # returned by Atlas.compute_hierarchy_list()
            "atlas/atlas_objects/hierarchy",
            #
            # Computed in Atlas.__init__() as an argument of Atlas. Corresponds to the object
            # returned by Atlas.compute_array_projection(True, True)
            "atlas/atlas_objects/arrays_projection_corrected_True_True",
            #
            # Computed in Atlas.__init__(), calling Atlas.compute_array_projection() when
            # computing arrays_projection_corrected_True_True. Corresponds to the object returned by
            # Atlas.compute_projection_parameters()
            "atlas/atlas_objects/l_transform_parameters",
            #
            # Computed in Atlas.__init__(), calling Atlas.save_all_projected_masks_and_spectra(),
            # but it doesn't correpond to an object returned by a specific function.
            # All the masks and spectra are also computed and saved in the shelve database with the
            # following ids:
            # "atlas/atlas_objects/mask_and_spectrum_$slice_index$_$id_mask$",
            # "atlas/atlas_objects/mask_and_spectrum_MAIA_corrected_$slice_index$_$id_mask$"
            # (not explicitely in this list as there are too many, and they are necessarily computed
            # along with dic_existing_masks).
            #  * This a very long computation, the longest in the app. *
            "atlas/atlas_objects/dic_existing_masks",
            #
            # Computed when needed, as a property of Atlas. Corresponds to the object returned by
            # Atlas.compute_list_projected_atlas_borders_figures(). In practice, this function is
            # called at startup, when calling Figures.compute_dic_fig_contours() in
            # Figures.__init()__, through the computation of compute_figure_basic_image (with
            # plot_atlas_contours set to True).
            "atlas/atlas_objects/list_projected_atlas_borders_arrays",
            #
            # Computed at startup through calling
            # Atlas.compute_list_projected_atlas_borders_figures() (see comment just above).
            # Corresponds to the object returned by atlas.compute_array_images_atlas().
            "atlas/atlas_objects/array_images_atlas",
            #
        ]

        # Objects to shelve in the Figures class. Everything in this list is shelved at
        # initialization of the Figure object. The computations described are the ones done at
        # startup.
        self.figures_objects_at_init = (
            [
                # Computed in Figures.__init__() as an argument of Figures. Corresponds to the
                # object returned by Figures.compute_dic_fig_contours()
                "figures/region_analysis/dic_fig_contours",
            ]
            + [
                # Computed in compute_dic_fig_contours(), itself computed in Figures.__init__().
                # Corresponds to the object returned by
                # Figures.compute_figure_basic_image(type_figure=None, index_image=slice_index,
                #                                   plot_atlas_contours=True, only_contours=True)
                "figures/load_page/figure_basic_image_None_" + str(slice_index) + "_True_True"
                for slice_index in range(self.data.get_slice_number())
            ]
            + [
                # Computed in Figures.__init__() as an argument of Figures. Corresponds to the
                # object returned by
                # Figures.compute_normalization_factor_across_slices(cache_flask=None)
                "figures/lipid_selection/dic_normalization_factors_None",
                #
                # Computed in Figures.__init(), calling Figures.shelve_all_l_array_2D(), but it
                # doesn't correpond to an object returned by a specific function.
                # All the list of 2D slices of expression object are computed and saved in the
                # shelve database with the following ids:
                # "figures/3D_page/arrays_expression_$name_lipid$__",
                # (not explicitely in this list as there are too many).
                #  * This a very long computation.
                "figures/3D_page/arrays_expression_computed",
                #
                # Computed in Figures.__init(), calling Figures.shelve_all_arrays_borders(), but it
                # doesn't correpond to an object returned by a specific function.
                # All the arrays of borders object are computed and saved in the
                # shelve database with the following ids:
                # "figures/3D_page/arrays_borders_$id_region$_$decrease_dimensionality_factor$",
                # (not explicitely in this list as there are too many.
                # decrease_dimensionality_factor is 6 by defaults).
                #  * This a very long computation.
                "figures/3D_page/arrays_borders_computed"
                #
                # Computed in Figures.shelve_all_arrays_borders(), itself called in
                # Figures.__init__(). Corresponds to the object returned by
                # Figures.get_array_of_annotations(decrease_dimensionality_factor), with
                # decrease_dimensionality_factor=6 by defaults.
                "figures/3D_page/arrays_annotation_6",
            ]
        )

        # Objects to shelve in the Figures class. Objects in the list are not automatically shelved
        # at startup.
        self.figures_objects_to_compute = [
            # Computed in compute_figure_basic_image() only, which is called in load_slice and
            # region_analysis pages. Corresponds to the object returned by
            # figures.compute_array_basic_images(type_figure), with type_figure having the following
            # values: "original_data", "warped_data", "projection_corrected", "atlas"
            "figures/load_page/array_basic_image_original_data",
            "figures/load_page/array_basic_image_warped_data",
            "figures/load_page/array_basic_image_projection_corrected",
            "figures/load_page/array_basic_image_atlas",
            #
            # Computed when loading the threeD_exploration page. Corresponds to the object returned
            # by Figures.compute_treemaps_figure().
            "figures/atlas_page/3D/treemaps",
            #
            # Computed in compute_3D_volume_figure(). Corresponds to the object returned by
            # Figures.compute_3D_root_volume().
            "figures/3D_page/volume_root",
        ]

        # Objects to shelve not belonging to a specific class. Objects in the list are not
        # automatically shelved at startup.
        self.other_objects_to_compute = [
            # Computed when loading the lipid_selection page. Corresponds to the object returned by
            # return_lipid_options().
            "annotations/lipid_options",
        ]

    def check_missing_db_entries(l_db_entries):
        """This function checks if all the entries in l_db_entries are in the shelve database. It then 
        returns a list containing the missing entries.

        Args:
            l_db_entries (list): List of entries in the shelve database to check.
        """

        # Define database path
        db_path = "data/app_data/data.db"

        # Get database
        db = shelve.open(db_path)

        # Build a set of missing entries
        l_missing_entries = list(set(l_db_entries) - set(db.keys()))

        # Find out if there are entries in the databse and not in the list of entries to check
        l_unexpected_entries = list(set(db.keys()) - set(l_db_entries))

        if len(l_unexpected_entries) > 0:
            logging.warning(
                "WARNING: unexpected entries in shelve database: " + str(l_unexpected_entries)
            )

        # Close database
        db.close()

        return l_missing_entries

    def compute_and_fill_entries(l_entries):
        """This function precompute all the entries in l_entries and fill them in the shelve database.
        """

        # Define database path
        db_path = "data/app_data/data.db"

        # Get database
        db = shelve.open(db_path)

        # Compute missing entries
        for entry in l_entries:
            pass
            # TODO

        # Close database
        db.close()

    def erase_all_entries():
        """This function erases all entries in the shelve database.
        """

        # Define database path
        db_path = "data/app_data/data.db"

        # Get database
        db = shelve.open(db_path)

        # Completely empty database
        for key in db:
            del db[key]

        # Close database
        db.close()

    def first_launch(erase_db=False):
        """This function must be used at the very first execution of the app. It will take care of 
        cleaning the shelve database, run compiled functions once, and precompute all the figures that 
        can be precomputed.
        """
        pass
        # TODO

