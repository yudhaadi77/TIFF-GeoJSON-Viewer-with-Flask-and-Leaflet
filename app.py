from flask import Flask, render_template, send_from_directory, jsonify, abort
import os
from utils.db_to_tiff import convert_all_tables_to_files

app = Flask(__name__)

# Folder data untuk file TIFF dan GeoJSON
DATA_FOLDER = 'data'

@app.route('/')
def index():
    try:
        # Konversi tabel ke TIFF, point dan kontur GeoJSON
        convert_all_tables_to_files(output_dir=DATA_FOLDER)

        # Render halaman utama
        return render_template('index.html')
    except Exception as e:
        return f"Terjadi kesalahan: {e}", 500


@app.route('/data/<path:filename>')
def serve_file(filename):
    """
    Serve TIFF atau GeoJSON file to the client.
    """
    file_path = os.path.join(DATA_FOLDER, filename)

    if not os.path.exists(file_path):
        abort(404, description="File tidak ditemukan")

    return send_from_directory(DATA_FOLDER, filename)


@app.route('/data/files')
def list_files():
    """
    Mengirimkan daftar semua file dalam folder DATA_FOLDER.
    """
    try:
        files = os.listdir(DATA_FOLDER)
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Pastikan folder data ada sebelum aplikasi berjalan
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    app.run(debug=True)
