## Alignment to the Allen Brain Atlas

The 64 slices were aligned to the [adult mouse brain reference](http://atlas.brain-map.org/atlas?atlas=602630314#atlas=602630314&plate=576989940&structure=549&x=5280.271251166045&y=3744.257593866604&zoom=-3&resolution=11.93&z=3) acquired by the Allen Institute using [ABBA](https://biop.github.io/ijp-imagetoatlas/), a FIJI plugin developped at EPFL for the registration of thin mouse brain slices.

Each slice image was built from three different channels, each corresponding to a different set of lipids highlighting different types of structures in the brain. Image were then manually warped and aligned using landmark points. A higher resolution version of the warped slices was exported, along with the corresponding deformation field and the original and warped coordinates in the CCFv3 reference.

![](ressources/slice_cleaning.png)

This procedure allows to track the displacement of every single slice pixel, each of which is linked to a MALDI-MSI spectrum. Due to the warping and upscaling, some pixels are duplicated to fill the empty regions in the final slice image.
