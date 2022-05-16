## How to use the app

The use of the app should be relatively intuitive. It is composed of 4 different pages, accessible from the left navigation bar. From top to bottom, they are as follow (described in the sections hereafter):
 - Dataset overview
 - Lipid selection
 - Region analysis
 - Three-dimensional analysis
 
Each of this tabs allows for a different type of exploration/analysis of the MALDI-MSI data, through the use of various widgets. Apart from the *three-dimensional analysis*, all the pages can only display one slice at most. In this case, slices can be browsed using the slider at the bottom of the page. 

On most graphs (in particular, heatmap and m/z plot), you can draw a square with your mouse to zoom in, and double click to reset zoom level. Many items in the app are embedded with advice. Just hover such an item with your mouse to get a tip on how to use it.

The documentation is always available using the corresponding icon at the bottom left of the screen.

### Dataset overview

This part of the app allows for an overview of the whole dataset. Four tabs are available:
 - Original slices: these images correspond to the Total Ion Content (TIC) of the slices directly from the original acquisitions. No filtering or warping whatsoever has been done here.
 - Warped slices: these images correspond to the TIC of the slices from the original acquisitions after they have been upscaled and warped using ABBA.
 -  Filtered slices: same as warped slices, except that all the pixels that do not correspond to a specific annotation in the Allen mouse brain reference are zero-ed out.
 -  Atlas slices: these images, coming from the Allen mouse brain reference, should match the filtered slices. Note that, to this end, they may correspond to tilted sections, since the tilt angle of the original slices is not necessarily zero.
 
An additionnal switch to display the annotations from the reference is available. Finally, a button allows to display the complete set of filtered slices in 3D, to provide an intuitive representation of the distance between the different acquisitions, as well as the corresponding tilting angle.

### Lipid selection

This part of the app allows for the visualization of up to three manually selected lipids (themselves, corresponding to a given m/z range in the original MALDI-MSI data) using the top-left dropdown, or the visualization of a manually inputed range using the bottom left user input field. 

If lipids are selected, they can be displayed as a RGB image (each lipid corresponding to a given channel), or summed and displayed as a heatmap with the standard *viridis* colormap. For manually selectes ranges, only the colormap option is available. In both case, no explicit scale is displayed as mass-spectrometry intensity data is hard to interpret in terms of concentration of quantity units. For most lipids, the scale is anyway normalized according to the 95th percentile of the image. However, the lipids that were significantly expressed in all the slices were renormalized according to the method [MAIA](TODO.linkpaperMAIA) , allowing for a comparison of the intensity across slices (given that the switch to activate the transform is on).

To avoid confusion, the input used for plotting the image in the center is always displayed at the top-right, along with the potentially selected lipids (each with the color of the channel it corresponds to, in the case of a RGB plot).

Finally, using the buttons at the bottom right, you also have the possibility to display the spectral data used to plot the images that are displayed. More precicely, you can display the average spectrum of the currently selected slice (but with a relatively low resolution, as the data would be too large to download in real time), or the average spectrum of the currently selected lipid or range (in high-resolution). The corresponding image and spectral data can be downloaded with the appropriate buttons.

### Region analysis

This part of the app allows for the data exploration of up to four manually drawned regions, or structures selected from a pre-computed list (top-left dropdown menu). Once the regions have been drawn/selected, a click on the button "Compute spectral data" will trigger... the computation of the corresponding spectral data. In practice, all the pixel spectra (in the original data, duplicated pixels are ignored) are averaged and displayed in the color of the initial selection.

At the bottom left, a heatmap shows the most differentially expressed lipids in the selected regions (sorted by standard deviation). As many lipids are very little expressed and the dataset is relatively noisy, the results would not be nor relevant or significant if all of them were displayed. Therefore, a slider allows for filtering out the most lowly expressed, by percentile of expression.

At the bottom right, a RGB image represents the three most differentially expressed lipids in the initial set of selections (which can be superimposed using the switch "Toggle masks and shapes display"). The defaults selection of lipids can be changed (add/remove lipids) by using the three dropdown menus above the image, one for each channel.

As previously, data and images can be downloaded with the appropriate buttons.  

### Three-dimensional analysis

This part of the app allows for the exploration of the dataset structure-wise, in three dimensions. As it incorporates data coming from several slices, and lipid expression can be tricky to compare in the original data, only the MAIA transformed lipids are available here. 

The left widget, called a treemap, allows for browsing the Allen mouse brain structural hierarchy, and add the structure(s) of interest using the button below.  On the right side of the screen, using the dropdown menu, one can select up to three lipids of interest.

If at least two structures have been selected, one can display a clustergram of lipid expression in the selected structures (that is, a heatmap of lipid expression clustered both by lipids and by structures), by clicking the button "Compare lipid expression in the selected structures".  As preivously, the lipid expression being low for some lipids, they can be filtered out using the slider above to keep only the lipids whose expression is above a given percentile.

If at least one structure and one lipid have been selected, by clicking on "Display lipid expression in the selected structure(s)", one can display the corresponding lipid expression (summed, if several lipids were selected) in the corresponding structures, in a 3D graph representing isosurfaces of expression.