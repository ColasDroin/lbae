// Select div
var gd = document.getElementById("rotating-brain");

// Build plot
Plotly.plot(
  gd,
  [
    {
      type: "volume",
      x: x_rotating_brain,
      y: y_rotating_brain,
      z: z_rotating_brain,
      value: value_rotating_brain,
      isomin: 9,
      isomax: 500,
      colorscale: [
        [0, "rgb(62, 74, 137)"],
        [0.25, "rgb(38, 130, 142)"],
        [0.5, "rgb(53, 183, 121)"],
        [0.75, "rgb(180, 222, 44)"],
        [1.0, "rgb(253, 231, 37)"],
      ],
      opacity: 0.5,
      surface: { count: 6 },
      showscale: false,
    },
  ],
  {
    scene: {
      camera: {
        eye: { x: 0, y: 1.1 * 1.3, z: 0.2 * 1.3 },
      },
      dragmode: false,
      xaxis: {
        autorange: true,
        showgrid: false,
        zeroline: false,
        showline: false,
        autotick: true,
        ticks: "",
        showticklabels: false,
        visible: false,
      },
      yaxis: {
        autorange: true,
        showgrid: false,
        zeroline: false,
        showline: false,
        autotick: true,
        ticks: "",
        showticklabels: false,
        visible: false,
      },
      zaxis: {
        autorange: true,
        showgrid: false,
        zeroline: false,
        showline: false,
        autotick: true,
        ticks: "",
        showticklabels: false,
        visible: false,
      },
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    hovermode: false,
    height: 500,
    margin: {
      l: 0,
      r: 0,
      b: 0,
      t: 0,
      pad: 0,
    },
  },
  { displayModeBar: false, responsive: true, scrollZoom: false }
);

// Remove skeleton
document.getElementById("skeleton-rotating-brain").innerHTML = "";

// Functions to rotate brain

var cnt = 0;
function run() {
  rotate("scene", Math.PI / 720);
  requestAnimationFrame(run);
}
run();

function rotate(id, angle) {
  var eye0 = gd.layout[id].camera.eye;
  var rtz = xyz2rtz(eye0);
  rtz.t += angle;

  var eye1 = rtz2xyz(rtz);
  Plotly.relayout(gd, id + ".camera.eye", eye1);
}

function xyz2rtz(xyz) {
  return {
    r: Math.sqrt(xyz.x * xyz.x + xyz.y * xyz.y),
    t: Math.atan2(xyz.y, xyz.x),
    z: xyz.z,
  };
}

function rtz2xyz(rtz) {
  return {
    x: rtz.r * Math.cos(rtz.t),
    y: rtz.r * Math.sin(rtz.t),
    z: rtz.z,
  };
}
