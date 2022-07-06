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

# LBAE imports
from modules.tools.misc import logmem


# ==================================================================================================
# --- Class
# ==================================================================================================


class ScRNAseq:
    """Class used to compare the data coming from acquisitions (MALDI), and the molecular atlas
    data (scRNAseq).

        Attributes:
            array_exp_lipids_brain_1 (np.ndarray): Matrix of lipids expression for brain 1, whose
                rows correspond to acquired spots and columns to lipids.
            array_exp_lipids_brain_2 (np.ndarray): Same as for array_exp_lipids_brain_1, but with
                the data from brain 2.
            array_exp_genes_brain_1 (np.ndarray): Matrix of genes expression for brain 1, whose rows
                correspond to acquired spots and columns to genes.
            array_exp_genes_brain_2 (np.ndarray): Same as for array_exp_genes_brain_1, but with
                the data from brain 2.
            l_name_lipids_brain_1 (list(str)): List of lipids names for brain 1.
            l_name_lipids_brain_2 (list(str)): Same as for l_name_lipids_brain_1, but with the data
                from brain 2.
            l_genes_brain_1 (list(str)): List of genes names for brain 1.
            l_genes_brain_2 (list(str)): Same as for l_genes_brain_1, but with the data from
                brain 2.
            array_coef_brain_1 (np.ndarray): Array of coefficients for the LASSO regression for
                brain 1, explaining lipid expression in terms of gene expression (lipids are rows,
                genes are columns).
            array_coef_brain_2 (np.ndarray): Same as for array_coef_brain_1, but with the data from
                brain 2.
            l_score_brain_1 (list(float)): List of scores for the LASSO regression for brain 1.
            l_score_brain_2 (list(float)): Same as for l_score_brain_1, but with the data from
                brain 2.

            xmol (np.ndarray): Array of x coordinates of the acquired spots.
            ymol (np.ndarray): Array of y coordinates of the acquired spots.
            zmol (np.ndarray): Array of z coordinates of the acquired spots.

        Methods:
            __init__(path_scRNAseq="data/scRNAseq/"): Initialize the scRNAseq class.
    """

    # ==============================================================================================
    # --- Constructor
    # ==============================================================================================

    def __init__(self, path_scRNAseq="data/scRNAseq/"):
        """Initialize the class ScRNAseq.

        Args:
            path (str): Path of the scRNAseq data.
        """

        logging.info("Initializing ScRNAseq object" + logmem())

        # Load the array of lipids and genes and corresponding names for brain 1
        self.array_exp_lipids_brain_1 = np.load(path_scRNAseq + "array_exp_lipids_True.npy")
        self.l_name_lipids_brain_1 = np.load(path_scRNAseq + "array_name_lipids_True.npy").tolist()
        self.array_exp_genes_brain_1 = np.load(path_scRNAseq + "array_exp_genes_True.npy")
        self.l_genes_brain_1 = np.load(path_scRNAseq + "array_name_genes_True.npy").tolist()
        self.array_coef_brain_1 = np.load(path_scRNAseq + "array_coef_True.npy")
        self.l_score_brain_1 = np.load(path_scRNAseq + "array_score_True.npy").tolist()

        # Same for brain 2
        self.array_exp_lipids_brain_2 = np.load(path_scRNAseq + "array_exp_lipids_False.npy")
        self.l_name_lipids_brain_2 = np.load(path_scRNAseq + "array_name_lipids_False.npy").tolist()
        self.array_exp_genes_brain_2 = np.load(path_scRNAseq + "array_exp_genes_False.npy")
        self.l_genes_brain_2 = np.load(path_scRNAseq + "array_name_genes_False.npy").tolist()
        self.array_coef_brain_2 = np.load(path_scRNAseq + "array_coef_False.npy")
        self.l_score_brain_2 = np.load(path_scRNAseq + "array_score_False.npy").tolist()

        # Load the array of coordinates
        self.xmol, self.ymol, self.zmol = np.load(path_scRNAseq + "array_coordinates.npy")

        logging.info("ScRNAseq object instantiated" + logmem())

    # ==============================================================================================
    # --- Methods
    # ==============================================================================================
