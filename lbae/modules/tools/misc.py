# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains various functions which would not belong to any other class."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import os
import shutil
import psutil

# ==================================================================================================
# --- Functions
# ==================================================================================================


def logmem():
    """This function returns a string representing the current amount of memory used by the program.
    It is almost instantaneous as it takes about 0.5ms to run.

    Returns:
        str: Amount of memory used by the program.
    """
    memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    memory_string = "MemTotal: " + str(memory)
    return "\t" + memory_string


def delete_all_files_in_folder(input_folder):
    """This function deletes all files and folder preset in the directory input_folder

    Args:
        input_folder (str): Path of the input folder to clean.
    """
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        try:
            # Delete wether directory or file
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))

