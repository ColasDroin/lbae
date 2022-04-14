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
        """

        # App main objects
        self.data = data
        self.atlas = atlas
        self.figures = figures

        # Objects to shelve in the Atlas class. Everything in this list is shelved at
        # initialization of Atlas and Figures objects.
        self.atlas_objects = [
            # Computed in Atlas.__init__() as an argument of Atlas,
            # calling Atlas.compute_dic_acronym_children_id()
            "atlas/atlas_objects/dic_acronym_children_id",
            #
            # Computed in Atlas.__init__() as an argument of Atlas,
            # calling Atlas.compute_hierarchy_list()
            "atlas/atlas_objects/hierarchy",
            #
            # Computed in Atlas.__init__() as an argument of Atlas,
            # calling Atlas.compute_array_projection()
            "atlas/atlas_objects/arrays_projection_corrected_True_True",
            #
            # Computed in Atlas.__init__(), calling Atlas.compute_array_projection() when
            # computing arrays_projection_corrected_True_True.
            "atlas/atlas_objects/l_transform_parameters",
            #
            # Computed in Atlas.__init__(), calling Atlas.save_all_projected_masks_and_spectra()
            # This a very long computation.
            "atlas/atlas_objects/dic_existing_masks",
            #
            # Computed when needed, as a property of Atlas, calling
            # Atlas.compute_list_projected_atlas_borders_figures(). In practice, this is computed
            # at startup when calling Figures.compute_dic_fig_contours() in Figures.__init()__,
            # through the computation of compute_figure_basic_image with plot_atlas_contours set
            # to True.
            "atlas/atlas_objects/list_projected_atlas_borders_arrays",
            #
            # Computed calling atlas.compute_array_images_atlas(). In practice, this is done at
            # startup through calling Atlas.compute_list_projected_atlas_borders_figures()
            # (see comment just above).
            "atlas/atlas_objects/array_images_atlas",
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

