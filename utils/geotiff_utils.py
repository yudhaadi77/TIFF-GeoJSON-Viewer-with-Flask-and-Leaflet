from osgeo import gdal, osr
import numpy as np
import json


def create_tiff(data, long_coords, lat_coords, output_path, resolution_factor=1, compress_tiff=False):
    """
    Membuat file GeoTIFF dari array data dengan opsi mengurangi resolusi.

    Parameters:
    - data: Array data nilai Z.
    - long_coords: Koordinat longitude (long).
    - lat_coords: Koordinat latitude (lat).
    - output_path: Path untuk file output TIFF.
    - resolution_factor: Faktor downsampling untuk mengurangi resolusi (default: 1, tanpa downsampling).
    - compress_tiff: Aktifkan kompresi TIFF menggunakan DEFLATE (default: False).
    """
    if not data or not long_coords or not lat_coords:
        raise ValueError("Data, long_coords, dan lat_coords tidak boleh kosong.")

    # Unikkan dan urutkan koordinat longitude dan latitude
    long_unique = sorted(list(set(long_coords)))
    lat_unique = sorted(list(set(lat_coords)))

    # Downsampling untuk mengurangi resolusi
    long_downsampled = long_unique[::resolution_factor]
    lat_downsampled = lat_unique[::resolution_factor]

    # Buat array 2D untuk menyimpan data
    array = np.zeros((len(lat_downsampled), len(long_downsampled)))

    # Isi array dengan nilai Z
    for long, lat, value in zip(long_coords, lat_coords, data):
        if long in long_downsampled and lat in lat_downsampled:
            x_idx = long_downsampled.index(long)
            y_idx = lat_downsampled.index(lat)
            array[y_idx, x_idx] = value

    # Simpan array sebagai file GeoTIFF
    driver = gdal.GetDriverByName('GTiff')
    options = ['COMPRESS=DEFLATE'] if compress_tiff else []  # Opsi kompresi
    out_ds = driver.Create(output_path, len(long_downsampled), len(lat_downsampled), 1, gdal.GDT_Float32, options)
    out_ds.GetRasterBand(1).WriteArray(array)

    # Set geotransform (transformasi geospasial) dan proyeksi
    geotransform = (
        min(long_downsampled),  # Origin X
        (max(long_downsampled) - min(long_downsampled)) / len(long_downsampled),  # Resolusi piksel X
        0,  # Rotasi X
        max(lat_downsampled),  # Origin Y
        0,  # Rotasi Y
        -(max(lat_downsampled) - min(lat_downsampled)) / len(lat_downsampled)  # Resolusi piksel Y (negatif untuk arah Y ke bawah)
    )
    out_ds.SetGeoTransform(geotransform)

    # Tetapkan proyeksi ke WGS 84 (EPSG:4326)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS 84
    out_ds.SetProjection(srs.ExportToWkt())

    # Tutup file GeoTIFF
    out_ds = None
    print(f"File GeoTIFF berhasil dibuat: {output_path}")
    return output_path


def create_point(data, long_coords, lat_coords, output_path, resolution_factor=1):
    """
    Membuat file GeoJSON kontur dari array data dengan opsi mengurangi resolusi.

    Parameters:
    - data: Array data nilai Z.
    - long_coords: Koordinat longitude (long).
    - lat_coords: Koordinat latitude (lat).
    - output_path: Path untuk file output GeoJSON.
    - resolution_factor: Faktor downsampling untuk mengurangi resolusi (default: 1, tanpa downsampling).
    """
    from scipy.interpolate import griddata
    import matplotlib.pyplot as plt
    import matplotlib.contour as mcontour

    if not data or not long_coords or not lat_coords:
        raise ValueError("Data, long_coords, dan lat_coords tidak boleh kosong.")

    # Interpolasi data menjadi grid
    long_unique = np.linspace(min(long_coords), max(long_coords), 100 // resolution_factor)
    lat_unique = np.linspace(min(lat_coords), max(lat_coords), 100 // resolution_factor)
    grid_x, grid_y = np.meshgrid(long_unique, lat_unique)
    grid_z = griddata((long_coords, lat_coords), data, (grid_x, grid_y), method='linear')

    # Buat kontur dari grid
    fig, ax = plt.subplots()
    contour = ax.contour(grid_x, grid_y, grid_z, levels=10)

    # Konversi kontur menjadi GeoJSON
    features = []
    for collection in contour.collections:
        for path in collection.get_paths():
            coords = path.vertices
            if len(coords) > 1:  # Pastikan hanya poligon valid
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coords.tolist()
                    },
                    "properties": {}
                })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Simpan GeoJSON ke file
    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=4)

    print(f"File GeoJSON kontur berhasil dibuat: {output_path}")
    return output_path

