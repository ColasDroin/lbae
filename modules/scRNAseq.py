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
from imageio import imread
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
            ll_coef (list(np.ndarray)): List of coefficients for the LASSO regression explaining 
                lipid expression in terms of gene expression.
            l_score (list(float)): List of scores for the LASSO regression.


        Methods:
            __init__(maldi_data, resolution=25, sample=False): Initialize the scRNAseq class.
            compute_dic_acronym_children_id(): Recursively compute a dictionnary that associates brain
                structures to the set of their children.


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

        # Load the array of lipids and genes and corresponding names
        self.array_exp_lipids = np.load(path_scRNAseq + "array_exp_lipids.npy")
        self.array_exp_genes = np.load(path_scRNAseq + "array_exp_genes.npy")
        self.l_name_lipids = np.load(path_scRNAseq + "array_name_lipids.npy").tolist()
        self.l_genes = np.load(path_scRNAseq + "array_name_genes.npy").tolist()

        # Load the array of coordinates
        self.xmol, self.ymol, self.zmol = np.load(path_scRNAseq + "array_coordinates.npy")

        # Get the regression coefficients
        self.ll_coef, self.l_score = self.storage.return_shelved_object(
            "scRNAseq",
            "ll_coef",
            force_update=False,
            compute_function=self.compute_regression_all_lipids,
        )





        logging.info("ScRNAseq object instantiated" + logmem())

    # ==============================================================================================
    # --- Methods
    # ==============================================================================================


    def compute_regression_all_lipids(self):

        # Define regression as a function for potential parallelization
        def compute_regression(index_lipid):
            print(index_lipid)
            clf = linear_model.ElasticNet(fit_intercept = True, alpha=0.2, positive = False)#linear_model.Lasso(alpha=0.001)##
            clf.fit(self.array_exp_genes, self.array_exp_lipids[:,index_lipid])
            return [clf.coef_, clf.score(self.array_exp_genes, self.array_exp_lipids[:,index_lipid])]

        # Compute regression for all lipids
        l_lipid_indices = list(range(self.array_exp_lipids.shape[1]))
        l_res =  [x for x in map(compute_regression, l_lipid_indices)]

        # Store the coefficients and the score of the regressions
        ll_coef = []
        l_score = []
        for res in l_res:
            ll_coef.append(res[0])
            l_score.append(res[1])

        # Return result
        return ll_coef, l_score




    def compute_dic_acronym_children_id(self):
        """Recursively compute a dictionnary that associates brain structures to the set of their
            children.

        Returns:
            dict: A dictionnary that associate to each structure (acronym) the set of ids (int) of
                all of its children.
        """

        # Recursive function to compute the parent of each structure
        def fill_dic_acronym_children_id(dic_acronym_children_id, l_id_leaves):
            older_leave_id = l_id_leaves[0]
            acronym = self.bg_atlas.structures[older_leave_id]["acronym"]
            for id_leave in l_id_leaves:
                # Fill dic with current acronym and id
                if acronym in dic_acronym_children_id:
                    dic_acronym_children_id[acronym].add(id_leave)
                else:
                    dic_acronym_children_id[acronym] = set([id_leave])
            # While root is not reached, climb back the ancestor tree
            if len(self.bg_atlas.structures[older_leave_id]["structure_id_path"]) >= 2:
                id_parent = self.bg_atlas.structures[older_leave_id]["structure_id_path"][-2]
                dic_acronym_children_id = fill_dic_acronym_children_id(
                    dic_acronym_children_id, [id_parent] + l_id_leaves
                )
            return dic_acronym_children_id

        # Initialize dictionnary as empty
        dic_acronym_children_id = {}

        # Loop over each structure
        for id in set(self.bg_atlas.annotation.flatten()):
            if id != 0:
                # Fill the dictionnary by climbing up the hierarchy structure
                dic_acronym_children_id = fill_dic_acronym_children_id(
                    dic_acronym_children_id, [id]
                )
        return dic_acronym_children_id

 