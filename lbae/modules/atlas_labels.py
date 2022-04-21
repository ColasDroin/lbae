# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, two classes are implemented to handle the Allen Brain Atlas annotations without
loading the full arrays of annotations in memory.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard modules
import numpy as np

# ! Investigate the usefulness of this class
# ! Rewrite the comments with attributes methods in the header of the class, not in init
# ==================================================================================================
# --- Classes
# ==================================================================================================
class Labels:
    """ Class used to access labels data without having to create new arrays."""

    def __init__(self, bg_atlas, force_init=True):
        """Initialize the class Labels.

        Args:
            bg_atlas (BrainGlobeAtlas): BrainGlobeAtlas object, used to query the atlas.
            force_init (bool, optional): If True, the arrays of annotations and structures in 
                BrainGlobeAtlas are loaded in memory (this avoids to have them during the first 
                query, but rather when the app is initialized). Defaults to True.
        Attributes:
            bg_atlas (BrainGlobeAtlas): BrainGlobeAtlas object, used to query the atlas.
        """
        self.bg_atlas = bg_atlas
        if force_init:
            _ = self.bg_atlas.annotation
            _ = self.bg_atlas.structures

    def __getitem__(self, key):
        """Getter for the curent class. For every coordinate (key) passed as a parameter, the 
        corresponding label is returned. Arrays of keys are also compatible.
        
        Args:
            key (tuple): Coordinates of the voxel to query.
        
        Returns:
            str: Label of the voxel in the Allen Brain Atlas. 
            """
        x = self.bg_atlas.annotation[key]
        if isinstance(x, np.uint32):
            if x != 0:
                return self.bg_atlas.structures[x]["name"]
            else:
                return "undefined"

        # an array slice have been provided
        else:
            return np.reshape(
                [
                    self.bg_atlas.structures[i]["name"] if i != 0 else "undefined"
                    for i in x.flatten()
                ],
                x.shape,
            )
