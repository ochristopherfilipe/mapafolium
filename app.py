from flask import Flask, render_template, request, redirect, url_for
import folium
import os
import geopandas as gpd
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)

# Coordenadas iniciais para centralizar o mapa
initial_coords = [-5.315518848620957, -61.98811551121906]  # Brasília, Brasil
mapa = folium.Map(location=initial_coords, zoom_start=7)
folium.TileLayer("Stadia.AlidadeSatellite").add_to(mapa)

# Lista para armazenar as localizações adicionadas
locations = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global mapa, locations
    if request.method == 'POST':
        coords = request.form.get('coords')
        if coords:
            try:
                lat, lon = map(float, coords.split(','))
                # Adicionar a nova localização
                location = (lat, lon)
                locations.append(location)
                # Criar um novo mapa e adicionar as localizações
                mapa = folium.Map(location=initial_coords, zoom_start=7)
                folium.TileLayer("Esri.WorldImagery", name="Satélite 1").add_to(mapa)
                folium.TileLayer("Stadia.AlidadeSatellite").add_to(mapa)
                for loc in locations:
                    folium.Marker(loc).add_to(mapa)
                # Salvar o mapa atualizado
                mapa.save(os.path.join('static', 'map.html'))
            except ValueError:
                pass  # Lidar com erro de formato inválido
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global mapa, locations
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Nenhum arquivo enviado", 400
        file = request.files['file']
        if file.filename == '':
            return "Nenhum arquivo selecionado", 400
        if file and file.filename.endswith('.zip'):
            try:
                # Salvar o arquivo ZIP temporariamente
                temp_zip = secure_filename(file.filename)
                file.save(temp_zip)
                
                # Extrair o arquivo ZIP
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall('temp_shapefile')
                
                # Carregar o Shapefile usando geopandas
                shapefile_path = [os.path.join('temp_shapefile', f) for f in os.listdir('temp_shapefile') if f.endswith('.shp')][0]
                gdf = gpd.read_file(shapefile_path)
                
                # Converter para GeoJSON
                geojson_data = gdf.to_json()
                
                # Criar um novo mapa e adicionar as localizações existentes
                mapa = folium.Map(location=initial_coords, zoom_start=7)
                
                # Adicionar diferentes estilos de mapas
                folium.TileLayer("OpenTopoMap", name="OpenTopoMap").add_to(mapa)
                folium.TileLayer("Esri.WorldImagery", name="Esri World Imagery").add_to(mapa)
                folium.TileLayer("Stadia.AlidadeSatellite", name="Stadia Alidade Satellite").add_to(mapa)
                
                # Adicionar as localizações existentes
                for loc in locations:
                    folium.Marker(loc).add_to(mapa)
                
                # Criar uma camada de sobreposição para o GeoJSON
                overlay = folium.FeatureGroup(name='Shapefile Overlay')
                folium.GeoJson(geojson_data).add_to(overlay)
                overlay.add_to(mapa)
                
                # Adicionar controle de camadas
                folium.LayerControl().add_to(mapa)
                
                # Salvar o mapa atualizado
                mapa.save(os.path.join('static', 'map.html'))
                
                # Remover os arquivos temporários
                os.remove(temp_zip)
                for f in os.listdir('temp_shapefile'):
                    os.remove(os.path.join('temp_shapefile', f))
                os.rmdir('temp_shapefile')
                
                return redirect(url_for('index'))  # Redirecionar para a página principal
            except Exception as e:
                return f"Erro ao processar o arquivo: {str(e)}", 500
        else:
            return "Arquivo inválido. Por favor, envie um arquivo ZIP contendo um Shapefile.", 400
    return render_template('upload.html')

if __name__ == '__main__':
    # Garantir que o diretório 'static' exista
    if not os.path.exists('static'):
        os.makedirs('static')
    # Salvar o mapa inicial
    mapa.save(os.path.join('static', 'map.html'))
    app.run(debug=True)
