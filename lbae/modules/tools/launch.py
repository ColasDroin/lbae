# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains functions used to do check and run all precomputation at first app launch."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import logging
import shelve

# ==================================================================================================
# --- Functions
# ==================================================================================================


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

