# 🌍 TIFF & GeoJSON Viewer with Flask and Leaflet

This is a **Flask-based web application** for visualizing **GeoTIFF** and **GeoJSON** data using **Leaflet.js**.  
It **automatically** converts data from a PostgreSQL database into:
- **TIFF (Raster)**
- **GeoJSON (Point)**
- **GeoJSON (Contour)**

Then, it **displays them on an interactive map** with **layer control**, allowing users to toggle visibility.

---

## ✨ Features
- ✔ **Automatic conversion from PostgreSQL → GeoTIFF, GeoJSON (Point & Contour)**
- ✔ **TIFF visualization using Leaflet**
- ✔ **Point and Contour GeoJSON visualization**
- ✔ **Layer control for toggling TIFF, Point, and Contour layers**
- ✔ **Dynamic file loading (auto-detects TIFF & GeoJSON files in `/data/` folder)**

---

## 📥 Installation Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

### 2️⃣ Create a Virtual Environment (Optional)
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up PostgreSQL Database
Ensure your PostgreSQL database contains a table with the following columns:
- **long** → Longitude  
- **lat** → Latitude  
- **z** → Data value (e.g., elevation)

Modify `db_to_tiff.py` to match your database connection:
```python
conn = psycopg2.connect(
    dbname="your_database",
    user="your_user",
    password="your_password",
    host="localhost",
    port="5432"
)
```

### 5️⃣ Run the Flask Application
```bash
python app.py
```
The app will be available at **`http://127.0.0.1:5000/`**.

---

## 📂 Project Structure
```plaintext
/FLASK_TIFF
│── /data               # Stores converted TIFF & GeoJSON files
│── /static             # Contains main.js and CSS files
│── /templates          # HTML files (index.html)
│── /utils              # Scripts for database conversion
│── app.py              # Flask application
│── db_to_tiff.py       # PostgreSQL to TIFF & GeoJSON conversion
│── requirements.txt    # Dependencies list
│── README.md           # Documentation
```

---

## ⚡ Core Functions in `db_to_tiff.py`
### 🔹 `convert_to_tiff()`
Converts PostgreSQL data to **GeoTIFF**.

### 🔹 `create_point()`
Generates **GeoJSON Points** to represent individual measurement points.

### 🔹 `create_contour()`
Generates **GeoJSON Contour** based on interpolated elevation values.

### 🔹 `convert_all_tables_to_files()`
Scans the PostgreSQL database, finds all tables containing `long`, `lat`, and `z`, and automatically converts them to **TIFF and GeoJSON**.

---

## 🎨 Frontend (Leaflet.js)
The **Leaflet map** dynamically loads and displays:
- **TIFF Raster Layers**
- **GeoJSON Point Layers**
- **GeoJSON Contour Layers**
- **Layer control for toggling visibility**

Example code snippet to load these layers in `main.js`:
```javascript
// Initialize map
var map = L.map('map').setView([-6.2, 106.8], 10);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Load TIFF files dynamically
async function loadTIFF() {
    const tiffFiles = {{ tiff_files | tojson | safe }};
    tiffFiles.forEach(async (file) => {
        const response = await fetch(`/data/${file}`);
        const arrayBuffer = await response.arrayBuffer();
        const georaster = await parseGeoraster(arrayBuffer);
        const layer = new GeoRasterLayer({
            georaster: georaster,
            opacity: 0.7,
            resolution: 256,
        });
        layer.addTo(map);
    });
}

// Load GeoJSON Point Layers
async function loadPoints() {
    const pointFiles = {{ point_files | tojson | safe }};
    pointFiles.forEach(async (file) => {
        const response = await fetch(`/data/${file}`);
        const geojson = await response.json();
        L.geoJSON(geojson, {
            pointToLayer: function (feature, latlng) {
                return L.marker(latlng, { icon: blueIcon });
            }
        }).addTo(map);
    });
}

// Load GeoJSON Contour Layers
async function loadContours() {
    const contourFiles = {{ contour_files | tojson | safe }};
    contourFiles.forEach(async (file) => {
        const response = await fetch(`/data/${file}`);
        const geojson = await response.json();
        L.geoJSON(geojson, {
            style: {
                color: 'red',
                weight: 1
            }
        }).addTo(map);
    });
}

// Load all layers
loadTIFF();
loadPoints();
loadContours();
```

---

## 🛠 Troubleshooting
### ❌ Issue: `ModuleNotFoundError: No module named 'shapely'`
Solution:
```bash
pip install shapely
```

### ❌ Issue: `'QuadContourSet' object has no attribute 'collections'`
Solution:
- Ensure **Matplotlib** is installed
```bash
pip install matplotlib
```
- Avoid calling `plt.show()` in scripts running outside of Jupyter Notebooks

### ❌ Issue: `'tuple' object has no attribute 'step'`
Solution:
- Ensure **SciPy** is installed
```bash
pip install scipy
```
- Check that `numpy.arange()` is used properly when defining contour levels

---

## 📧 Contact
For any inquiries or contributions, feel free to reach out:
- **Email:** yudhaadiputra26@gmail.com
- **LinkedIn:** [your-profile](https://linkedin.com/in/yudha-adi-putra)
```