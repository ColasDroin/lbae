# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This class is used to compare the data coming from acquisitions (MALDI), and the molecular atlas 
data (scRNAseq). See https://molecularatlas.org/ for more information."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import numpy as np
import logging
from sklearn import linear_model

# LBAE imports
from modules.tools.misc import logmem


# ==================================================================================================
# --- Class
# ==================================================================================================


class ScRNAseq:
    """Class used to compare the data coming from acquisitions (MALDI), and the molecular atlas
    data (scRNAseq).

        Attributes:
            array_exp_lipids (np.ndarray): Matrix of lipids expression, whose rows correspond to
                acquired spots and columns to lipids.
            array_exp_genes (np.ndarray): Matrix of genes expression, whose rows correspond to
                acquired spots and columns to genes.
            l_name_lipids (list(str)): List of lipids names.
            l_genes (list(str)): List of genes names.
            xmol (np.ndarray): Array of x coordinates of the acquired spots.
            ymol (np.ndarray): Array of y coordinates of the acquired spots.
            zmol (np.ndarray): Array of z coordinates of the acquired spots.
            array_coef (np.ndarray): Array of coefficients for the LASSO regression explaining
                lipid expression in terms of gene expression (lipids are rows, genes are columns).
            l_score (list(float)): List of scores for the LASSO regression.


        Methods:
            __init__(maldi_data, resolution=25, sample=False): Initialize the scRNAseq class.
            compute_dic_acronym_children_id(): Recursively compute a dictionnary that associates brain
                structures to the set of their children.


    """

    # ==============================================================================================
    # --- Constructor
    # ==============================================================================================

    def __init__(self, path_scRNAseq="data/scRNAseq/", brain_1=False):
        """Initialize the class ScRNAseq.

        Args:
            path (str): Path of the scRNAseq data.
        """

        logging.info("Initializing ScRNAseq object" + logmem())

        # Load the array of lipids and genes and corresponding names
        self.array_exp_lipids = np.load(path_scRNAseq + "array_exp_lipids_" + str(brain_1) + ".npy")
        self.l_name_lipids = np.load(
            path_scRNAseq + "array_name_lipids_" + str(brain_1) + ".npy"
        ).tolist()
        self.array_exp_genes = np.load(path_scRNAseq + "array_exp_genes_" + str(brain_1) + ".npy")
        self.l_genes = np.load(path_scRNAseq + "array_name_genes_" + str(brain_1) + ".npy").tolist()
        self.array_coef = np.load(path_scRNAseq + "array_coef_" + str(brain_1) + ".npy")
        self.l_score = np.load(path_scRNAseq + "array_score_" + str(brain_1) + ".npy").tolist()

        # Load the array of coordinates
        self.xmol, self.ymol, self.zmol = np.load(path_scRNAseq + "array_coordinates.npy")

        logging.info("ScRNAseq object instantiated" + logmem())

    # ==============================================================================================
    # --- Methods
    # ==============================================================================================
