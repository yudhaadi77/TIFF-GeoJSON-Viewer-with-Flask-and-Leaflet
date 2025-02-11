// Inisialisasi peta Leaflet
var map = L.map('map').setView([-6.2, 106.8], 10);

// Tambahkan basemap (OpenStreetMap)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Layer untuk menyimpan data yang dipilih
var tiffLayer, pointLayer, contourLayer;

// Fungsi untuk mengambil daftar file dari server dan mengisi dropdown
async function populateFileDropdowns() {
    try {
        const response = await fetch('/data/files');
        const files = await response.json();

        // Filter TIFF, Point, dan Contour files
        const tiffFiles = files.filter(file => file.endsWith('.tiff'));
        const pointFiles = files.filter(file => file.endsWith('_point.geojson'));
        const contourFiles = files.filter(file => file.endsWith('_contour.geojson'));

        // Isi dropdown TIFF
        const selectTIFF = document.getElementById("selectTIFF");
        tiffFiles.forEach(file => {
            let option = new Option(file, file);
            selectTIFF.add(option);
        });

        // Isi dropdown Point
        const selectPoint = document.getElementById("selectPoint");
        pointFiles.forEach(file => {
            let option = new Option(file, file);
            selectPoint.add(option);
        });

        // Isi dropdown Contour
        const selectContour = document.getElementById("selectContour");
        contourFiles.forEach(file => {
            let option = new Option(file, file);
            selectContour.add(option);
        });

    } catch (error) {
        console.error("Error loading file list:", error);
    }
}

// Fungsi untuk memuat TIFF yang dipilih
async function loadSelectedTIFF() {
    const selectedFile = document.getElementById("selectTIFF").value;
    if (!selectedFile) {
        if (tiffLayer) map.removeLayer(tiffLayer);
        return;
    }

    try {
        const response = await fetch(`/data/${selectedFile}`);
        const arrayBuffer = await response.arrayBuffer();
        const georaster = await parseGeoraster(arrayBuffer);

        if (tiffLayer) {
            map.removeLayer(tiffLayer);
        }

        tiffLayer = new GeoRasterLayer({
            georaster: georaster,
            opacity: 0.7,
            resolution: 256
        });

        tiffLayer.addTo(map);
        map.fitBounds(tiffLayer.getBounds());

    } catch (error) {
        console.error("Error loading TIFF:", error);
    }
}

// Fungsi untuk memuat Point Layer yang dipilih
async function loadSelectedPoint() {
    const selectedFile = document.getElementById("selectPoint").value;
    if (!selectedFile) {
        if (pointLayer) map.removeLayer(pointLayer);
        return;
    }

    try {
        const response = await fetch(`/data/${selectedFile}`);
        const geojson = await response.json();

        if (pointLayer) {
            map.removeLayer(pointLayer);
        }

        pointLayer = L.geoJSON(geojson, {
            pointToLayer: (feature, latlng) => {
                return L.marker(latlng);
            },
            onEachFeature: (feature, layer) => {
                layer.bindPopup(`Value: ${feature.properties.z}`);
            }
        });

        pointLayer.addTo(map);
        map.fitBounds(pointLayer.getBounds());

    } catch (error) {
        console.error("Error loading Point Layer:", error);
    }
}

// Fungsi untuk memuat Contour Layer yang dipilih
async function loadSelectedContour() {
    const selectedFile = document.getElementById("selectContour").value;
    if (!selectedFile) {
        if (contourLayer) map.removeLayer(contourLayer);
        return;
    }

    try {
        const response = await fetch(`/data/${selectedFile}`);
        const geojson = await response.json();

        if (contourLayer) {
            map.removeLayer(contourLayer);
        }

        contourLayer = L.geoJSON(geojson, {
            style: {
                color: 'red',
                weight: 2
            }
        });

        contourLayer.addTo(map);
        map.fitBounds(contourLayer.getBounds());

    } catch (error) {
        console.error("Error loading Contour Layer:", error);
    }
}

// Fungsi untuk menghapus semua layer (Reset)
function resetLayers() {
    if (tiffLayer) {
        map.removeLayer(tiffLayer);
        tiffLayer = null;
    }
    if (pointLayer) {
        map.removeLayer(pointLayer);
        pointLayer = null;
    }
    if (contourLayer) {
        map.removeLayer(contourLayer);
        contourLayer = null;
    }

    // Reset dropdown ke default
    document.getElementById("selectTIFF").selectedIndex = 0;
    document.getElementById("selectPoint").selectedIndex = 0;
    document.getElementById("selectContour").selectedIndex = 0;
}

// Event listener untuk mendeteksi perubahan pada dropdown
document.getElementById("selectTIFF").addEventListener("change", loadSelectedTIFF);
document.getElementById("selectPoint").addEventListener("change", loadSelectedPoint);
document.getElementById("selectContour").addEventListener("change", loadSelectedContour);

// Event listener untuk tombol reset
document.getElementById("resetButton").addEventListener("click", resetLayers);

// Jalankan saat halaman dimuat
populateFileDropdowns();
