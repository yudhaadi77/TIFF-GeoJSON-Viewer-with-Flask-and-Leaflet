// Inisialisasi peta Leaflet
var map = L.map('map').setView([-6.2, 106.8], 10);

// Tambahkan basemap (OpenStreetMap)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Fungsi untuk memuat TIFF secara otomatis
async function loadTIFFs() {
    try {
        // Ambil daftar file TIFF dari server
        const response = await fetch('/data/files');
        const files = await response.json();
        const tiffFiles = files.filter(file => file.endsWith('.tiff'));

        for (const tiffFile of tiffFiles) {
            const tiffResponse = await fetch(`/data/${tiffFile}`);
            const arrayBuffer = await tiffResponse.arrayBuffer();
            const georaster = await parseGeoraster(arrayBuffer);

            // Tambahkan GeoRasterLayer ke Leaflet
            const layer = new GeoRasterLayer({
                georaster: georaster,
                opacity: 0.7,
                resolution: 256, // Sesuaikan resolusi tampilan
            });
            layer.addTo(map);

            // Sesuaikan tampilan peta ke area TIFF
            map.fitBounds(layer.getBounds());
        }
    } catch (error) {
        console.error("Error loading TIFFs:", error);
    }
}

// Fungsi untuk memuat GeoJSON point secara otomatis
async function loadPoints() {
    try {
        // Ambil daftar file GeoJSON point dari server
        const response = await fetch('/data/files');
        const files = await response.json();
        const pointFiles = files.filter(file => file.endsWith('_point.geojson'));

        for (const pointFile of pointFiles) {
            const pointResponse = await fetch(`/data/${pointFile}`);
            const geojson = await pointResponse.json();

            // Tambahkan GeoJSON layer ke Leaflet
            const pointLayer = L.geoJSON(geojson, {
                pointToLayer: (feature, latlng) => {
                    return L.marker(latlng);
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`Value: ${feature.properties.z}`);
                }
            }).addTo(map);

            // Sesuaikan tampilan peta ke area point
            map.fitBounds(pointLayer.getBounds());
        }
    } catch (error) {
        console.error("Error loading points:", error);
    }
}

// Fungsi untuk memuat GeoJSON contour secara otomatis
async function loadContours() {
    try {
        // Ambil daftar file GeoJSON contour dari server
        const response = await fetch('/data/files');
        const files = await response.json();
        const contourFiles = files.filter(file => file.endsWith('_contour.geojson'));

        for (const contourFile of contourFiles) {
            const contourResponse = await fetch(`/data/${contourFile}`);
            const geojson = await contourResponse.json();

            // Tambahkan GeoJSON layer ke Leaflet
            const contourLayer = L.geoJSON(geojson, {
                style: {
                    color: 'red', // Warna garis kontur
                    weight: 2,    // Ketebalan garis
                }
            }).addTo(map);

            // Sesuaikan tampilan peta ke area contour
            map.fitBounds(contourLayer.getBounds());
        }
    } catch (error) {
        console.error("Error loading contours:", error);
    }
}

// Panggil fungsi untuk memuat semua file TIFF, point, dan kontur
loadTIFFs();
loadPoints();
loadContours();
