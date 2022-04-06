# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, the ZODB database is instantiated.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import ZODB, ZODB.FileStorage
import BTrees.OOBTree

# ==================================================================================================
# --- Instantiate ZODB database
# ==================================================================================================
import os

# Filesystem database (ZODB) initialization
print(os.getcwd())
storage = ZODB.FileStorage.FileStorage("data/app_data/app_data.fs")  # , blob_dir="data/app_data/")
db = ZODB.DB(storage)
connection = db.open()
root = connection.root

# Check if the app folder in the database already exists, otherwise create it
if hasattr(root, "data") is False:
    root.data = BTrees.OOBTree.BTree()
