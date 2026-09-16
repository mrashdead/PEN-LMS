const lineMap = new jsVectorMap({
    selector: "#orderTrackingMap",
    map: "world",
    lineStyle: {
        stroke: "#676767",
        strokeWidth: 1.5,
        fill: "#ff5566",
        fillOpacity: 1,
        strokeDasharray: "6 3 6", // OR: [6, 2, 6]
        animation: true, // Enables animation
    },
    markers: [
        {
            name: "برزیل",
            coords: [-14.235, -51.9253], // Brazil coordinates
            style: { fill: "red" },
        },
        {
            name: "چین",
            coords: [34.9727, 105.0324],
            style: { fill: "purple" },
        }
    ],
    lines: [
        {from: "برزیل", to: "چین" },
    ]
});