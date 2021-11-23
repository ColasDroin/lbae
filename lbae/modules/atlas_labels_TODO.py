###### IMPORT MODULES ######

# Standard imports
import numpy as np

#! These classes were previously implemented with zarr, need to understand why

###### Labels Class ######
class Labels:
    """ Class used to access labels data without having to create new arrays"""

    def __init__(self, bg_atlas):
        self.bg_atlas = bg_atlas

    def __getitem__(self, key):
        x = self.bg_atlas.annotation[key]
        if isinstance(x, np.uint32):
            if x != 0:
                return self.bg_atlas.structures[x]["name"]
            else:
                return "undefined"

        # an array slice have been provided
        else:
            return np.reshape(
                [self.bg_atlas.structures[i]["name"] if i != 0 else "undefined" for i in x.flatten()], x.shape
            )


###### LabelContours Class ######
class LabelContours:
    """ Class used to map labels to increasing integers"""

    def __init__(self, bg_atlas):
        self.bg_atlas = bg_atlas
        self.unique_id = {ni: indi for indi, ni in enumerate(set(self.bg_atlas.annotation.flatten()))}

    def __getitem__(self, key):
        x = self.bg_atlas.annotation[key]
        if isinstance(x, np.uint32):
            return self.unique_id[x]
        else:
            array = np.reshape([self.unique_id[i] for i in x.flatten()], x.shape)
            return array

