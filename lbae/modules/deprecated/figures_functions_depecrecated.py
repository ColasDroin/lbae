### DEPRECATED FUNCTIONS. SHOULD BE CHECKED FOR BUG BEFORE USAGE ###
def compute_figure_basic_images_with_slider_DEPRECATED(
    self, type_figure="warped_data", plot_atlas_contours=False
):
    # Get array of images
    array_images = return_shelved_object(
        "figures/load_page",
        "array_basic_images",
        force_update=False,
        compute_function=self.compute_array_basic_images,
        type_figure=type_figure,
    )

    if plot_atlas_contours:
        array_images_atlas = self._atlas.list_projected_atlas_borders_arrays

    # Build plot with slider
    fig = go.Figure(
        frames=[
            go.Frame(
                data=[
                    go.Image(
                        visible=True,
                        source=convert_image_to_base64(
                            array_images[i],
                            overlay=array_images_atlas[i] if plot_atlas_contours else None,
                            optimize=True,
                            quality=40,
                        ),
                        hoverinfo="none",
                    ),
                    # array_images_atlas[i],
                ],
                name=str(i + 1),
            )
            for i in range(0, self._data.get_slice_number(), 1)
        ]
    )
    fig.add_trace(
        go.Image(
            visible=True,
            source=convert_image_to_base64(
                array_images[0],
                overlay=array_images_atlas[0] if plot_atlas_contours else None,
                optimize=True,
                quality=40,
            ),
            hoverinfo="none",
        )
    )

    def frame_args(duration):
        return {
            "frame": {"duration": duration},
            "mode": "immediate",
            "fromcurrent": True,
            "transition": {"duration": duration, "easing": "linear"},
        }

    sliders = [
        {
            "pad": {"b": 10, "t": 60},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": [
                {"args": [[f.name], frame_args(0)], "label": str(k), "method": "update",}
                for k, f in enumerate(fig.frames)
            ],
        }
    ]

    # Layout
    fig.update_layout(margin=dict(t=25, r=0, b=0, l=0),)

    def frame_args(duration):
        return {
            "frame": {"duration": duration, "redraw": True},
            "mode": "immediate",
            "fromcurrent": True,
            "transition": {"duration": duration, "easing": "linear"},
        }

    fig.layout.sliders = [
        {
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {"prefix": "Slice" + "="},
            "pad": {"b": 10, "t": 60},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": [
                {"args": [[f.name], frame_args(0)], "label": f.name, "method": "animate",}
                for f in fig.frames
            ],
        }
    ]

    logging.info("Figure has been computed")
    return fig


# This function sums over the selected lipids for now
def compute_figure_bubbles_3D_DEPRECATED(
    self,
    ll_t_bounds,
    normalize_independently=True,
    high_res=False,
    name_lipid_1="",
    name_lipid_2="",
    name_lipid_3="",
    cache_flask=None,
):
    logging.info("Starting computing figure bubbles 3D")

    # Get 3D arrays for lipid distribution
    array_x, array_y, array_z, array_c = return_shelved_object(
        "figures/3D_page",
        "arrays_3D_" + name_lipid_1 + "_" + name_lipid_2 + "_" + name_lipid_3,
        force_update=False,
        compute_function=self.compute_array_3D,
        ignore_arguments_naming=True,
        ll_t_bounds=ll_t_bounds,
        normalize_independently=normalize_independently,  # normalize_independently,
        high_res=high_res,
        cache_flask=cache_flask,
    )

    # Build figure
    fig = go.Figure(
        data=go.Scatter3d(
            x=array_x,
            y=array_y,
            z=array_z,
            mode="markers",
            marker=dict(
                # sizemode="diameter",
                # sizeref=40,
                size=1.5,  # array_c,
                color=array_c,
                colorscale="Viridis",
                reversescale=True,
                colorbar_title="Expression",
                # line_color="rgba(140, 140, 170, 0.01)",
            ),
        )
    )
    fig.update_layout(
        scene=dict(
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", color="grey", gridcolor="grey"),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", color="grey", gridcolor="grey"),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", color="grey", gridcolor="grey"),
        ),
        margin=dict(t=5, r=0, b=0, l=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    logging.info("Done computing 3D bubble figure" + logmem())
    return fig


def compute_sunburst_figure_DEPRECATED(self, maxdepth=3):
    fig = px.sunburst(names=self._atlas.l_nodes, parents=self._atlas.l_parents, maxdepth=maxdepth)
    fig.update_layout(margin=dict(t=0, r=0, b=0, l=0),)
    return fig


def compute_root_data_DEPRECATED(self):

    # Get root data
    mesh_data_root = self._atlas.bg_atlas.mesh_from_structure("root")
    vertices_root = mesh_data_root.points
    triangles_root = mesh_data_root.cells[0].data

    # Compute points and vertices
    x_root, y_root, z_root = vertices_root.T
    I_root, J_root, K_root = triangles_root.T
    # tri_points_root = vertices_root[triangles_root]

    pl_mesh_root = go.Mesh3d(
        x=x_root / 1000 / 1000 * 25 * 10,
        y=y_root / 1000 / 1000 * 25 * 10,
        z=z_root / 1000 / 1000 * 25 * 10,
        colorscale=([0, "rgb(153, 153, 153)"], [1.0, "rgb(255,255,255)"]),
        intensity=z_root,
        flatshading=False,
        i=I_root / 1000 / 1000 * 25 * 10,
        j=J_root / 1000 / 1000 * 25 * 10,
        k=K_root / 1000 / 1000 * 25 * 10,
        opacity=0.1,
        name="Mesh CH",
        showscale=False,
    )
    return pl_mesh_root


def compute_3D_figure_DEPRECATED(self, structure=None):

    root_lines = return_shelved_object(
        "figures/atlas_page/3D",
        "root",
        force_update=False,
        compute_function=self.compute_root_data,
    )

    layout = go.Layout(
        # title="3D atlas representation",
        font=dict(size=16, color="white"),
        scene_xaxis_visible=False,
        scene_yaxis_visible=False,
        scene_zaxis_visible=False,
        # paper_bgcolor='rgb(50,50,50)',
        margin=dict(t=10, r=10, b=10, l=10),
        # Zoom by 2 initially
        # ! Find a fix
        # scene={"aspectratio": {"x": 1, "y": 1.0, "z": 1.0}, "aspectmode": "cube"},
    )

    if structure is not None:
        # get structure data
        mesh_data = self._atlas.bg_atlas.mesh_from_structure(structure)
        vertices = mesh_data.points
        triangles = mesh_data.cells[0].data

        # compute points and vertices
        x, y, z = vertices.T
        I, J, K = triangles.T
        tri_points = vertices[triangles]

        Xe = []
        Ye = []
        Ze = []
        for T in tri_points:
            Xe.extend([T[k % 3][0] for k in range(4)] + [None])
            Ye.extend([T[k % 3][1] for k in range(4)] + [None])
            Ze.extend([T[k % 3][2] for k in range(4)] + [None])

        pl_mesh = go.Mesh3d(
            x=x,
            y=y,
            z=z,
            colorscale="Blues",
            intensity=z,
            flatshading=True,
            i=I,
            j=J,
            k=K,
            # name="Mesh CH",
            showscale=False,
        )

        pl_mesh.update(
            cmin=-7,
            lighting=dict(
                ambient=0.2,
                diffuse=1,
                fresnel=0.1,
                specular=1,
                roughness=0.05,
                facenormalsepsilon=1e-15,
                vertexnormalsepsilon=1e-15,
            ),
            lightposition=dict(x=100, y=200, z=0),
        )

    if structure is not None:
        fig = go.Figure(data=[pl_mesh, root_lines], layout=layout)
    else:
        fig = go.Figure(data=[root_lines], layout=layout)

    return fig


def compute_figure_slices_2D_DEPRECATED(
    self, ll_t_bounds, normalize_independently=True, cache_flask=None
):

    fig = go.Figure(
        frames=[
            go.Frame(
                data=self.compute_rgb_image_per_lipid_selection(
                    i,
                    ll_t_bounds[i - 1],
                    normalize_independently=True,
                    title=False,
                    projected_image=True,
                    enrichment=False,
                    log=False,
                    return_image=True,
                    use_pil=True,
                    cache_flask=cache_flask,
                ),
                name=str(i),
            )
            for i in range(1, self._data.get_slice_number() + 1, 1)
            if ll_t_bounds[i - 1] != [None, None, None]
        ]
    )

    fig.add_trace(
        self.compute_rgb_image_per_lipid_selection(
            1,
            [
                ll_t_bounds[i - 1]
                for i in range(1, self._data.get_slice_number() + 1, 1)
                if ll_t_bounds[i - 1] != [None, None, None]
            ][0],
            normalize_independently=True,
            title=False,
            projected_image=True,
            enrichment=False,
            log=False,
            return_image=True,
            use_pil=True,
            cache_flask=cache_flask,
        ),
    )

    def frame_args(duration):
        return {
            "frame": {"duration": duration},
            "mode": "immediate",
            "fromcurrent": True,
            "transition": {"duration": duration, "easing": "linear"},
        }

    sliders = [
        {
            "pad": {"b": 5, "t": 10},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": [
                {"args": [[f.name], frame_args(0)], "label": f.name, "method": "animate",}
                for k, f in enumerate(fig.frames)
            ],
            "currentvalue": {"visible": False,},
        }
    ]

    # Improve graph layout
    fig.update_layout(
        title={
            "text": "",
            "y": 0.97,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=14,),
        },
        margin=dict(t=5, r=0, b=0, l=0),
        sliders=sliders,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    return fig


def compute_atlas_with_slider_DEPRECATED(self, view="frontal", contour=False):
    # Check that the given view exists
    if view not in ("frontal", "horizontal", "sagittal"):
        logging.warning(
            "The provided view must be of of the following: frontal, horizontal, or sagittal."
            + "Back to default, i.e. frontal"
        )
        view = "frontal"

    if view == "frontal":
        idx_view = 0
        axis_labels = self._atlas.bg_atlas.space.axis_labels[0]
    elif view == "horizontal":
        idx_view = 1
        axis_labels = self._atlas.bg_atlas.space.axis_labels[1]
    elif view == "sagittal":
        idx_view = 2
        axis_labels = self._atlas.bg_atlas.space.axis_labels[1]

    # multiplier to compute proper slice index depending if contours/mask are present or not
    multiplier = 2 if contour else 1

    # Create figure
    fig = go.Figure()

    subsampling = list(
        range(0, self._atlas.bg_atlas.reference.shape[idx_view], self._atlas.subsampling_block)
    )
    # Add traces, one for each slider step
    for step in subsampling:
        if view == "frontal":
            image_array = self._atlas.bg_atlas.reference[step, :, :]
        elif view == "horizontal":
            image_array = self._atlas.bg_atlas.reference[:, step, :]
        elif view == "sagittal":
            image_array = self._atlas.bg_atlas.reference[:, :, step]

        base64_string = convert_image_to_base64(image_array)

        if not contour:
            fig.add_trace(go.Image(visible=True, source=base64_string, hoverinfo="none",))

        else:
            fig.add_trace(go.Image(visible=True, source=base64_string))

            if view == "frontal":
                contour = self._atlas.simplified_labels_int[step, :, :]
            elif view == "horizontal":
                contour = self._atlas.simplified_labels_int[:, step, :]
            elif view == "sagittal":
                contour = self._atlas.simplified_labels_int[:, :, step]

            fig.add_trace(
                go.Contour(
                    visible=False,
                    showscale=False,
                    z=contour,
                    contours=dict(coloring="none"),
                    line_width=2,
                    line_color="gold",
                    hoverinfo="none",
                )
            )

    # Make 1st trace visible
    fig.data[multiplier * 1].visible = True

    # Create and add slider
    steps = []
    for i in range(len(fig.data) // multiplier):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data) * multiplier},],  # layout attribute
            label=subsampling[i],
        )
        step["args"][0]["visible"][multiplier * i] = True  # Toggle i'th trace to "visible"
        if contour:
            step["args"][0]["visible"][multiplier * i + 1] = True

        steps.append(step)

    sliders = [
        dict(
            active=10,
            currentvalue={"visible": False,},
            pad={"t": 30, "l": 100, "r": 100},
            steps=steps,
            # len = 0.4,
            # xanchor = 'center',
        )
    ]

    fig.update_layout(sliders=sliders)

    fig.update_layout(
        yaxis=dict(scaleanchor="x"),
        # width=1000,
        # height=800,
        title={
            "text": f"{view.capitalize()} view",
            "y": 0.99,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=14,),
        },
        margin=dict(t=30, r=0, b=0, l=0),
    )

    fig.update_xaxes(title_text=axis_labels[1])
    fig.update_yaxes(title_text=axis_labels[0])
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    return fig


def compute_array_3D_on_the_fly_DEPRECATED(
    self, ll_t_bounds, normalize_independently=True, high_res=False, cache_flask=None
):

    logging.info("Starting computing 3D arrays" + logmem())

    # get list of original coordinates for each slice
    if not high_res:
        l_coor = self._atlas.l_original_coor
        estimate = 400 * 400
    else:
        estimate = 1311 * 918
        l_coor = self._atlas.array_coordinates_warped_data

    # Initialize empty arrays with a large estimate for the orginal acquisition size

    max_size = estimate * self._data.get_slice_number()
    array_x = np.empty(max_size, dtype=np.float32)
    array_y = np.empty(max_size, dtype=np.float32)
    array_z = np.empty(max_size, dtype=np.float32)
    array_c = np.empty(max_size, dtype=np.int16)
    total_index = 0
    logging.debug(f"Size array_x: {array_x.nbytes / 1024 / 1024 :.2f}")
    logging.info("Starting slice iteration" + logmem())

    # get atlas shape and resolution
    reference_shape = self._atlas.bg_atlas.reference.shape
    resolution = self._atlas.resolution
    array_annotations = np.array(self._atlas.bg_atlas.annotation, dtype=np.int32)

    for slice_index in range(0, self._data.get_slice_number(), 1):
        if ll_t_bounds[slice_index] != [None, None, None]:

            # Get the data as an expression image per lipid
            array_data = self.compute_rgb_array_per_lipid_selection(
                slice_index + 1,
                ll_t_bounds[slice_index],
                normalize_independently=normalize_independently,
                projected_image=high_res,
                log=False,
                enrichment=False,
                apply_transform=True,
                cache_flask=cache_flask,
            )

            # Sum array colors (i.e. lipids)
            array_data = np.sum(array_data, axis=-1)
            # Remove pixels for which lipid expression is zero
            array_data_stripped = array_data[array_data != 0]
            # array_data_stripped = array_data.flatten()

            # Skip the current slice if expression is very sparse
            if len(array_data_stripped) < 10 or np.sum(array_data_stripped) < 1:
                continue

            # Compute the percentile of expression to filter out lowly expressed pixels
            # Set to 0 for now, as no filtering is done
            percentile = 0  # np.percentile(array_data_stripped, 10)

            # Get the coordinates of the pixels in the ccfv3
            coordinates = l_coor[slice_index]
            # coordinates_stripped = coordinates[array_data != 0]
            coordinates_stripped = coordinates.reshape(-1, coordinates.shape[-1])

            array_x, array_y, array_z, array_c, total_index = filter_voxels(
                array_data_stripped,
                coordinates_stripped,
                array_annotations,
                percentile,
                array_x,
                array_y,
                array_z,
                array_c,
                total_index,
                reference_shape,
                resolution,
            )
            logging.info("Slice " + str(slice_index) + " done" + logmem())

    # Strip the arrays from the zeros
    array_x = array_x[:total_index]
    array_y = array_y[:total_index]
    array_z = array_z[:total_index]
    # * Caution, array_c should be a list to work with Plotly
    array_c = array_c[:total_index].to_list()

    # Return the arrays for the 3D figure
    return array_x, array_y, array_z, array_c
