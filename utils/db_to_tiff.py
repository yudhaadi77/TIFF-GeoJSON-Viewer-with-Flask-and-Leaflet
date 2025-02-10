import psycopg2
from osgeo import gdal, osr
import json
import numpy as np
import os
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from matplotlib.contour import ContourSet


def convert_all_tables_to_files(output_dir='data/', compress_tiff=False, resolution_factor=2):
    """
    Otomatis mencari tabel dalam schema tertentu (misalnya 'data_demo') yang memiliki kolom long, lat, dan z,
    lalu mengonversinya ke file TIFF dan GeoJSON dengan opsi mengurangi resolusi.
    """
    try:
        # Koneksi ke database PostgreSQL
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        # Dapatkan semua tabel yang memiliki kolom long, lat, dan z di schema data_demo
        cursor.execute("""
            SELECT table_name
            FROM information_schema.columns
            WHERE table_schema = 'data_demo'
              AND column_name IN ('long', 'lat', 'z')
            GROUP BY table_name
            HAVING COUNT(column_name) = 3;
        """)
        tables = cursor.fetchall()

        if not tables:
            print("Tidak ada tabel dengan kolom long, lat, dan z dalam schema data_demo.")
            return

        # Iterasi setiap tabel
        for table in tables:
            table_name = table[0]
            print(f"Proses tabel: {table_name}")

            # Query data dari tabel
            cursor.execute(f"SELECT long, lat, z FROM data_demo.{table_name}")
            data = cursor.fetchall()

            if not data:
                print(f"Tabel {table_name} kosong. Melewati...")
                continue

            # Buat folder output jika belum ada
            os.makedirs(output_dir, exist_ok=True)

            # Konversi ke TIFF
            tiff_file = os.path.join(output_dir, f"{table_name}.tiff")
            convert_to_tiff(data, tiff_file, compress_tiff, resolution_factor)

            # Konversi ke point GeoJSON
            point_file = os.path.join(output_dir, f"{table_name}_point.geojson")
            create_point([row[2] for row in data], [row[0] for row in data], [row[1] for row in data], point_file, resolution_factor)

            # Konversi ke Contour GeoJSON
            contour_file = os.path.join(output_dir, f"{table_name}_contour.geojson")
            create_contour([row[2] for row in data], [row[0] for row in data], [row[1] for row in data], contour_file, resolution_factor)

    except psycopg2.Error as e:
        print(f"Database Error: {e}")
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()


def convert_to_tiff(data, output_file, compress_tiff, resolution_factor=2):
    """
    Konversi data tabel menjadi file TIFF dengan opsi untuk mengurangi resolusi.
    """
    long_coords = [row[0] for row in data]
    lat_coords = [row[1] for row in data]
    values = [row[2] for row in data]

    # Buat array 2D dari data
    long_unique = sorted(list(set(long_coords)))
    lat_unique = sorted(list(set(lat_coords)))

    # Downsampling untuk mengurangi resolusi
    long_downsampled = long_unique[::resolution_factor]
    lat_downsampled = lat_unique[::resolution_factor]
    array = np.zeros((len(lat_downsampled), len(long_downsampled)))

    for long, lat, value in zip(long_coords, lat_coords, values):
        if long in long_downsampled and lat in lat_downsampled:
            x_idx = long_downsampled.index(long)
            y_idx = lat_downsampled.index(lat)
            array[y_idx, x_idx] = value

    # Simpan array sebagai TIFF
    driver = gdal.GetDriverByName('GTiff')
    options = ['COMPRESS=DEFLATE'] if compress_tiff else []  
    out_ds = driver.Create(output_file, len(long_downsampled), len(lat_downsampled), 1, gdal.GDT_Float32, options)
    out_ds.GetRasterBand(1).WriteArray(array)

    # Set geotransform dan proyeksi
    geotransform = (min(long_downsampled), (max(long_downsampled) - min(long_downsampled)) / len(long_downsampled), 0,
                    max(lat_downsampled), 0, -(max(lat_downsampled) - min(lat_downsampled)) / len(lat_downsampled))
    out_ds.SetGeoTransform(geotransform)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84
    out_ds.SetProjection(srs.ExportToWkt())

    out_ds = None  # Simpan dan tutup file
    print(f"File TIFF berhasil dibuat dengan resolusi lebih rendah: {output_file}")


def create_point (values, long_coords, lat_coords, output_path, resolution_factor=2, contour_interval=500, density_factor=20):
    """
    Membuat GeoJSON berbentuk titik-titik (point) dari data (long, lat, values).

    Parameters:
    - values: Nilai Z (contoh: elevasi atau intensitas).
    - long_coords: Koordinat longitude (long).
    - lat_coords: Koordinat latitude (lat).
    - output_path: Path untuk file output GeoJSON.
    - resolution_factor: Faktor downsampling untuk grid interpolasi (default: 2, moderate resolution).
    - contour_interval: Interval point dalam nilai Z
    - density_factor: Faktor pengurangan kerapatan titik (default: 5, semakin besar semakin renggang).
    """
    if not values or not long_coords or not lat_coords:
        raise ValueError("Data, long_coords, dan lat_coords tidak boleh kosong.")

    # Unikkan dan urutkan koordinat longitude dan latitude
    long_unique = np.unique(long_coords)
    lat_unique = np.unique(lat_coords)

    # Downsampling koordinat longitude dan latitude
    long_downsampled = long_unique[::resolution_factor]
    lat_downsampled = lat_unique[::resolution_factor]

    # Grid untuk interpolasi
    grid_x, grid_y = np.meshgrid(long_downsampled, lat_downsampled)
    grid_z = griddata(
        (long_coords, lat_coords), values, (grid_x, grid_y), method='cubic', fill_value=np.nan
    )

    # Hitung titik-titik kontur
    features = []
    levels = np.arange(np.nanmin(grid_z), np.nanmax(grid_z), contour_interval)

    for level in levels:
        indices = np.where(np.isclose(grid_z, level, atol=contour_interval / 2))
        for i, (y, x) in enumerate(zip(indices[0], indices[1])):
            # Tambahkan downsampling berdasarkan density_factor
            if i % density_factor == 0:  # Pilih hanya setiap titik ke-n berdasarkan density_factor
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(grid_x[y, x]), float(grid_y[y, x])]
                    },
                    "properties": {
                        "z": float(level)
                    }
                })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Simpan file GeoJSON
    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=4)

    print(f"File GeoJSON Titik Kontur berhasil dibuat: {output_path}")
    return output_path

def create_contour(values, long_coords, lat_coords, output_path, resolution_factor=2, contour_interval=500):
    """
    Membuat GeoJSON berbentuk garis kontur dari data (long, lat, values).

    Parameters:
    - values: Nilai Z (contoh: elevasi atau intensitas).
    - long_coords: Koordinat longitude (long).
    - lat_coords: Koordinat latitude (lat).
    - output_path: Path untuk file output GeoJSON.
    - resolution_factor: Faktor downsampling untuk grid interpolasi (default: 2, moderate resolution).
    - contour_interval: Interval kontur dalam nilai Z.
    """
    if not values or not long_coords or not lat_coords:
        raise ValueError("Data, long_coords, dan lat_coords tidak boleh kosong.")

    # Unikkan dan urutkan koordinat longitude dan latitude
    long_unique = np.unique(long_coords)
    lat_unique = np.unique(lat_coords)

    # Downsampling koordinat longitude dan latitude
    long_downsampled = long_unique[::resolution_factor]
    lat_downsampled = lat_unique[::resolution_factor]

    # Grid untuk interpolasi
    grid_x, grid_y = np.meshgrid(long_downsampled, lat_downsampled)
    grid_z = griddata(
        (long_coords, lat_coords), values, (grid_x, grid_y), method='cubic', fill_value=np.nan
    )

    # Buat kontur menggunakan matplotlib
    contour_set = plt.contour(grid_x, grid_y, grid_z, levels=np.arange(np.nanmin(grid_z), np.nanmax(grid_z), contour_interval))

    # Konversi kontur menjadi GeoJSON
    features = []
    levels = contour_set.levels  # Nilai level kontur
    all_segments = contour_set.allsegs  # Segmen-segmen kontur

    for level, segments in zip(levels, all_segments):
        for segment in segments:
            coordinates = [[float(x), float(y)] for x, y in segment]
            if len(coordinates) > 1:  # Tambahkan hanya jika segmen memiliki lebih dari 1 koordinat
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates
                    },
                    "properties": {
                        "level": float(level)
                    }
                })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Simpan file GeoJSON
    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=4)

    print(f"File GeoJSON Kontur berhasil dibuat: {output_path}")
    return output_path

# # Contoh pemanggilan fungsi
# if __name__ == "__main__":
#     convert_all_tables_to_files(
#         output_dir='data/',
#         compress_tiff=True,  # Aktifkan kompresi TIFF
#         resolution_factor=4  # Mengurangi resolusi (1 dari 4 titik)
#     )
