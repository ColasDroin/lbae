# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This class contains functions used to do check and run all precomputation at first app 
launch."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import logging
import shelve
import sys

# LBAE functions
from modules.tools.storage import check_shelved_object, dump_shelved_object

# ==================================================================================================
# --- Class
# ==================================================================================================


class Launch:
    """ Class used to precompute and shelve objects at app launch.
    
    Attributes:
        data (MaldiData): MaldiData object, used to manipulate the raw MALDI data.
        atlas (Atlas): Atlas object, used to manipulate the objects coming from the Allen Brain 
            Atlas.
        figures (Figures): Figures object, used to build the figures of the app.
        path (str): Path to the shelve database.
        l_atlas_objects_at_init (list): List of atlas objects normally computed at app startup 
            if not already in shelve database.
        l_figures_objects_at_init (list): List of figures objects normally computed at app 
            startup if not already in shelve database.
        l_other_objects_to_compute (list): List of other objects which must be computed to 
            prevent slowing down the app during normal use.
        l_db_entries (list): List of all entries in the shelve database (i.e. concatenation of the 
            3 previous lists).
        l_entries_to_ignore (list): List of entries to ignore when checking if they are in the 
            shelve database.
            
    Methods:
        __init__(data, atlas, figures, path): Initialize the Launch class.
        check_missing_db_entries(): Check if all the entries in l_db_entries are in the shelve db.
        compute_and_fill_entries(l_missing_entries): Precompute all the entries in l_missing_entries 
            and fill them in the shelve database.
        launch(force_exit_if_first_launch=True): Launch the checks and precomputations at app 
            startup.
    """

    def __init__(self, data, atlas, figures, path="data/app_data/data.db"):
        """Initialize the class Launch.

        Args:
            data (MaldiData): MaldiData object, used to manipulate the raw MALDI data.
            atlas (Atlas): Atlas object, used to manipulate the objects coming from the Allen Brain 
                Atlas.
            figures (Figures): Figures object, used to build the figures of the app.
            path (str): Path to the shelve database. Defaults to "data/app_data/data.db".
        """

        # App main objects
        self.data = data
        self.atlas = atlas
        self.figures = figures

        # Database path
        self.db_path = path

        # Objects to shelve in the Atlas class. Everything in this list is shelved at
        # initialization of Atlas and Figures objects. The computations described are the ones done
        # at startup.
        self.l_atlas_objects_at_init = [
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
            # * This computation takes ~20s
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
            # Corresponds to the object returned by atlas.prepare_and_compute_array_images_atlas().
            "atlas/atlas_objects/array_images_atlas_True",
            #
        ]

        # Objects to shelve in the Figures class. Everything in this list is shelved at
        # initialization of the Figure object. The computations described are the ones done at
        # startup.
        self.l_figures_objects_at_init = (
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
                # Computed in Figures.__init__(). Corresponds to the object returned
                # by Figures.compute_treemaps_figure().
                "figures/atlas_page/3D/treemaps",
                #
                # Computed in Figures.__init__(). Corresponds to the object returned by
                # Figures.compute_figure_slices_3D().
                "figures/3D_page/slices_3D",
                #
                # Computed in Figures.__init__(). Corresponds to the object returned by
                # Figures.compute_3D_root_volume().
                "figures/3D_page/volume_root",
                #
                # Computed in Figures.__init(), calling Figures.shelve_arrays_basic_figures(), but
                # it doesn't correpond to an object returned by a specific function.
                # All figures are computed and saved in the shelve database with the following ids:
                # "figures/load_page/figure_basic_image_$type_figure$_$idx_slice$_$display_annotations",
                # (not explicitely in this list as there are too many).
                #  * This a long computation.
                "figures/load_page/arrays_basic_figures_computed",
                #
                # Computed in compute_figure_basic_image() only, which is called in
                # Figures.shelve_arrays_basic_figures(), itself called in Figures.__init__().
                # Corresponds to the object returned by
                # figures.compute_array_basic_images(type_figure), with type_figure having the
                # following values: "original_data", "warped_data", "projection_corrected", "atlas"
                "figures/load_page/array_basic_images_original_data",
                "figures/load_page/array_basic_images_warped_data",
                "figures/load_page/array_basic_images_projection_corrected",
                "figures/load_page/array_basic_images_atlas",
                #
                # Computed in Figures.__init(), calling Figures.shelve_all_l_array_2D(), but it
                # doesn't correspond to an object returned by a specific function.
                # All the list of 2D slices of expression objects are computed and saved in the
                # shelve database with the following ids:
                # "figures/3D_page/arrays_expression_$name_lipid$__",
                # (not explicitely in this list as there are too many).
                #  * This a very long computation.
                "figures/3D_page/arrays_expression_computed",
                #
                # Computed in in Figures.__init(), calling Figures.shelve_all_arrays_annotation(),
                # but it doesn't correspond to an object returned by a specific function. The
                # corresponding objects saved in Figures.shelve_all_arrays_annotation() are in the
                # comment below.
                "figures/3D_page/arrays_annotation_computed",
            ]
            + [
                # Computed in in Figures.__init(), calling Figures.shelve_all_arrays_annotation().
                # Corresponds to the object returned by
                # Figures.get_array_of_annotations(decrease_dimensionality_factor), with
                # decrease_dimensionality_factor ranging from 2 to 11.
                "figures/3D_page/arrays_annotation_" + str(decrease_dimensionality_factor)
                for decrease_dimensionality_factor in range(2, 13)
            ]
        )

        # Objects to shelve not belonging to a specific class. Objects in the list are not
        # automatically shelved at startup.
        self.l_other_objects_to_compute = [
            # Computed when loading the lipid_selection page. Corresponds to the object returned by
            # return_lipid_options().
            "annotations/lipid_options",
        ]

        # List of all db entries
        self.l_db_entries = (
            self.l_atlas_objects_at_init
            + self.l_figures_objects_at_init
            + self.l_other_objects_to_compute
        )

        self.l_entries_to_ignore = [
            "figures/3D_page/arrays_expression_",
            "figures/load_page/figure_basic_image_",
            "atlas/atlas_objects/mask_and_spectrum_",
            "atlas/atlas_objects/dic_processed_temp",
            "launch/first_launch",
        ]

    def check_missing_db_entries(self):
        """This function checks if all the entries in self.l_db_entries are in the shelve database. 
        It then returns a list containing the missing entries.
        """

        # Get database
        db = shelve.open(self.db_path)

        # Build a set of missing entries
        l_missing_entries = list(set(self.l_db_entries) - set(db.keys()))

        if len(l_missing_entries) > 0:
            logging.info("Missing entries found in the shelve database:" + str(l_missing_entries))

        # Find out if there are entries in the databse and not in the list of entries to check
        l_unexpected_entries = list(set(db.keys()) - set(self.l_db_entries))

        # Remove entries that are not in the initial list but are in the database, i.e all 2D lipid
        # slices, all brain regions, all figures in the load_slice page, and all atlas masks.
        l_unexpected_entries = [
            x
            for x in l_unexpected_entries
            if [entry not in x for entry in self.l_entries_to_ignore].count(True) == 0
        ]

        if len(l_unexpected_entries) > 0:
            logging.warning(
                "WARNING: unexpected entries found in the shelve database: "
                + str(l_unexpected_entries)
            )

        # Close database
        db.close()

        return l_missing_entries

    def compute_and_fill_entries(self, l_missing_entries):
        """This function precompute all the entries in l_missing_entries and fill them in the shelve 
        database.

        Args:
            l_missing_entries (list): list of entries to compute and insert in the shelve database.
        """

        # Get database
        db = shelve.open(self.db_path)

        # Compute missing entries if possible
        for entry in l_missing_entries:

            if entry in self.l_atlas_objects_at_init:
                logging.warning(
                    "This entry should not be missing,"
                    + " as it is computed during Atlas initialization: "
                    + entry
                    + " . Please rebuild the atlas variable"
                )

            elif entry in self.l_figures_objects_at_init:
                logging.warning(
                    "This entry should not be missing,"
                    + " as it is computed during Figures initialization: "
                    + entry
                    + " . Please rebuild the figures variable"
                )

            elif entry in self.l_other_objects_to_compute:
                logging.info("Entry: " + entry + " is missing. Computing now.")
                if entry == "annotations/lipid_options":
                    db[entry] = self.data.return_lipid_options()
                else:
                    logging.warning(
                        "Entry " + entry + " not found in the list of entries to compute."
                    )

        # Close database
        db.close()

    def launch(self, force_exit_if_first_launch=True):
        """This function is used at the execution of the app. It will take care of checking/cleaning
        the database entries, run compiled functions once, and precompute all the objects that can 
        be precomputed. At the very first launch, the app can be greedy in memory, reason for 
        which the user can choose to force the exit of the app, to start with a lighter process.

        Args:
            force_exit_if_first_launch (bool): if True, the app will force exit if it is the first 
                launch.
        """

        # Check for missing entries
        l_missing_entries = self.check_missing_db_entries()

        # Compute missing entries
        self.compute_and_fill_entries(l_missing_entries)

        # Check if the app has been run before, and potentially force exit if not
        if not check_shelved_object("launch", "first_launch"):
            dump_shelved_object("launch", "first_launch", True)
            if force_exit_if_first_launch:
                sys.exit(
                    "The app has been exited now that everything has been precomputed."
                    + "Please launch the app again."
                )
