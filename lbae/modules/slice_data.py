###### IMPORT MODULES ######

# Official modules
import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
import gc
import time


###### DEFINE SliceData CLASS ######


class SliceData:
    def __init__(self, slice_limit=3, slice_index=None):

        # list to keep track of the order in which the slices have been added
        self.list_order = []
        # total number of slices allowed in the dict
        self.slice_limit = slice_limit
        # dictionnary of slices, in which each slice object is indexed by the slice index
        self.dictionnary = {}
        self.locked = False

        if slice_index is not None:
            self.addSliceFromIndex(slice_index)

    def addSlice(self, slice_object):

        if slice_object.slice_index not in self.dictionnary:

            # wait for the other workers to free the dictionnary before modifying it
            while self.locked == True:
                time.sleep(0.05)

            # lock it
            self.locked = True

            if len(self.dictionnary) >= self.slice_limit:
                print(
                    "Slices "
                    + str(self.list_order)
                    + " are already recorded, slice "
                    + str(self.list_order[0])
                    + " will be deleted to free some memory."
                )

                self.removeOldestSlice(already_locked=True)

            # add the new slice
            self.dictionnary[slice_object.slice_index] = slice_object
            self.list_order.append(slice_object.slice_index)

            # free the dictionnary
            self.locked = False

    def removeOldestSlice(self, already_locked):
        # ensure the dictionnary is locked for the current worker
        if not already_locked:
            while self.locked == True:
                time.sleep(0.05)
            self.locked = True

        del self.dictionnary[self.list_order[0]]
        del self.list_order[0]

        # if the dictionnary won't be released in another function
        if not already_locked:
            self.locked = False

        gc.collect()

    def getSlice(self, slice_index, add_slice_if_not_present=True, return_slice=True):

        # check is slice is stored in memory
        if slice_index in self.dictionnary:
            print(slice_index, " was loaded from memory")
            return self.dictionnary[slice_index]

        # if not, try loading from pickle
        else:
            print(slice_index, " was not stored in memory, it is going to be loaded from disk")
            path = "data/pickled_data/raw_data/"
            name_fig = "data_slice_" + str(slice_index) + ".pickle"
            if name_fig in os.listdir(path):
                with open(path + name_fig, "rb") as slice_file:
                    slice = pickle.load(slice_file)
            else:
                # if not possible, load from npz file
                print(slice_index, " could not be loaded from pickle file. Loading from npz file now (slower option)")
                # try:
                slice = SliceData(slice_index)
                # except:
                #    print(
                #        slice_index,
                #        " could not be loaded from pickle or npz file. Check that the data files are present.",
                #    )
                #    return None

            # add slice to memory if asked
            if add_slice_if_not_present:
                self.addSlice(slice)

            if return_slice:
                return slice

    def addSliceFromIndex(self, slice_index):
        self.getSlice(slice_index, add_slice_if_not_present=True, return_slice=False)

    @staticmethod
    def pickleAllSlices():
        l_index = [int(x.split("_")[1]) for x in os.listdir("data/npz_slices/") if x[-3:] == "npz"]
        for slice_index in l_index:
            with open("data/pickled_data/raw_data/data_slice_" + str(slice_index) + ".pickle", "wb") as slice_file:
                pickle.dump(SliceData(slice_index), slice_file)

