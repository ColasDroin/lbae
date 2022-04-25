# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, functions used to handle the loading/dumping of the data used in the app 
(memmaps excluded), e.g. figures or masks, are defined. The storage relies on a shelve database."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import logging
import shelve
from modules.tools.misc import logmem

# ==================================================================================================
# --- Functions
# ==================================================================================================


def dump_shelved_object(data_folder, file_name, object):
    """This function dumps an object in a shelve database.

    Args:
        data_folder (str): The path of the folder in which the object must be 
            saved.
        file_name (str): The name of the file to save/load.
        object (object): The object to save.
    """

    # Get complete file name
    complete_file_name = data_folder + "/" + file_name

    # Dump in db
    with shelve.open("data/app_data/data.db") as db:
        db[complete_file_name] = object


def load_shelved_object(data_folder, file_name):
    """This function loads an object from a shelve database.

    Args:
        data_folder (str): The path of the folder in which the object must be 
            saved.
        file_name (str): The name of the file to save/load.
    """

    # Get complete file name
    complete_file_name = data_folder + "/" + file_name

    # Load from in db
    with shelve.open("data/app_data/data.db") as db:
        return db[complete_file_name]


def check_shelved_object(data_folder, file_name):
    """This function checks if an object is in a shelve database.

    Args:
        data_folder (str): The path of the folder in which the object must be 
            saved.
        file_name (str): The name of the file to save/load.
    """

    # Get complete file name
    complete_file_name = data_folder + "/" + file_name

    # Load from in db
    with shelve.open("data/app_data/data.db") as db:
        if complete_file_name in db:
            return True
        else:
            return False


def return_shelved_object(
    data_folder,
    file_name,
    force_update,
    compute_function,
    ignore_arguments_naming=False,
    **compute_function_args
):
    """This function checks if the result of the method or function compute_function has not been
    computed and saved already. If yes, it returns this result from the corresponding shelve.
    Else, it executes compute_function, saves the result in a shelve file, and returns the result.

    Args:
        data_folder (str): The path of the folder in which the result of compute_function must be 
            saved.
        file_name (str): The name of the object to save/load. Arguments will potentially be 
            contatenated to file_name depending on the value of ignore_arguments_naming.
        force_update (bool): If True, compute_function will be re-executed and saved despite the 
            file result already existing.
        compute_function (func): The function/method whose result must be loaded/saved.
        ignore_arguments_naming (bool, optional): If True, the arguments of compute_function won't
            be added to the filename of the result file. Defaults to False.
        **compute_function_args: Arguments of compute_function.

    Returns:
        The result of compute_function. Type may vary depending on compute_function.
    """
    # Define database path
    db_path = "data/app_data/data.db"

    # Get complete file name
    complete_file_name = data_folder + "/" + file_name

    # Complete filename with function arguments
    if not ignore_arguments_naming:
        for key, value in compute_function_args.items():
            complete_file_name += "_" + str(value)

    # Load the shelve
    db = shelve.open(db_path)
    # Check if the object is in the folder already and return it
    if complete_file_name in db and not force_update:
        logging.info("Returning " + complete_file_name + " from shelve file." + logmem())
        object = db[complete_file_name]
    else:
        logging.info(
            complete_file_name
            + " could not be found or force_update is True. "
            + "Computing the object and shelving it now."
        )

        # Close shelve to prevent nesting issues with compute function
        db.close()

        # Execute compute_function
        object = compute_function(**compute_function_args)

        # Reopen shelve
        db = shelve.open(db_path)

        # Save the result in a pickle file
        db[complete_file_name] = object
        logging.info(complete_file_name + " being returned now from computation.")

    # Close shelve for good this time
    db.close()
    return object


def empty_shelve():
    """This function erases all entries in the shelve database.
    """
    # Load from in db
    with shelve.open("data/app_data/data.db") as db:

        # Completely empty database
        for key in db:
            del db[key]

