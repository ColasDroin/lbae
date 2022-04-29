
# Lipid Brain Atlas Explorer Documentation

IMAGE 3D rotating brain

## Overview

The Lipid Brain Atlas Explorer is a Python Dash web-application developped as part of the **Lipid Brain Atlas project**, led by the [Lipid Cell Biology lab (EPFL)](https://www.epfl.ch/labs/dangelo-lab/) and the [Neurodevelopmental Systems Biology (EPFL)](https://www.epfl.ch/labs/nsbl/). It is thought as a graphical user interface to assist the inspection and the analysis of a large mass-spectrometry dataset of lipids distribution at micrometric resolution across the entire mouse brain.

All of the brain slices aquired have prealably been registered to the [Allen Mouse Brain Common Coordinate Framework v3.0](https://www.sciencedirect.com/science/article/pii/S0092867420304025) (CCFv3), allowing for a hierarchically structured annotation of our data. This registration can be used to display lipid signal between two m/z boundaries in a given slice (*lipid selection* page, in the app) and perform analyses comparing neuroanatomical regions, e.g. averaging and comparing lipid abundance in each region and make an enrichment analysis (*region analysis* page, in the app). It is also used to combine the 2D slice acquisitions into a browsable 3d model of lipid expression (*three dimensional analysis* page, in the app).

We hope that this application will be of great help to query the Lipid Brain Atlas to guide your hypotheses and experiments, and more generally to achieve a better understanding of the cellular mechanisms involving lipids that are fundamental for nervous system development and function.

## Data

PHOTO DATA

The multidimensional atlas of the mouse brain lipidome that you can explore through LBAE has been entirely acquired from MALDI Mass Spectrometry Imaging (MALDI-MSI) experiments. We have collected about 6 millions mass spectra, corresponding to 18’000 lipid images of 64 serial sections of two individual adult mouse brains (8 weeks old males BL6). Each pixel captures a region of $5μm$, with a spatial resolution of $25μm$ along a given slice and about $200μm$ across slices. The spectral resolution is of the order of $10^{-5} m/z$.

## Alignment to the Allen Brain Atlas

The 64 slices were aligned to the [adult mouse brain reference](http://atlas.brain-map.org/atlas?atlas=602630314#atlas=602630314&plate=576989940&structure=549&x=5280.271251166045&y=3744.257593866604&zoom=-3&resolution=11.93&z=3) acquired by the Allen Institute using [ABBA](https://biop.github.io/ijp-imagetoatlas/), a FIJI plugin developped at EPFL for the registration of thin mouse brain slices.

Each slice image was built from three different channels, each corresponding to a different set of lipids highlighting different types of structures in the brain. Image were then manually warped and aligned using landmark points. A higher resolution version of the warped slices was exported, along with the corresponding deformation field and the original and warped coordinates in the CCFv3 reference.

IMAGE OF A NICE SLICE BEFORE AND AFTER WARPING + HOLES 

This procedure allows to track the displacement of every single slice pixel, each of which is linked to a MALDI-MSI spectrum. Due to the warping and upscaling, some pixels are duplicated to fill the empty regions in the final slice image.

## How to use the app

  

### Dataset overview

  

TODO

  

### Lipid selection

  

TODO

  

### Region analysis

  

TODO

  

### Three-dimensional analysis

  

TODO

  

# Demo version

The app should be available at [TODO.LBAE.epfl.ch](TODO.github.com). A demo version of the app using a small sample of the dataset is available at: [TODO.heroku.com](TODO.heroku.com)

# About

The app was developed by Colas Droin, scientific programmer at EPFL, under the supervision of Gioele La Manno and Giovanni d'Angelo, as part of the Lipid Brain Atlas project. Laura Capolupo was involved in data collection and acquisition, Hannah Schede was involded in data wrangling and analysis. 

# To go further

  For more information about the technical details of this project (especially data handling, app design and implementation), please refer to [TODO.bioarxiv.com](TODO.bioarxiv.com). You can install your own version of the app and check the source code at [TODO.github.com](TODO.github.com).