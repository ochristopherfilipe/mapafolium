from flask import Flask, render_template, request, redirect, url_for
import folium
import os
import geopandas as gpd


app = Flask(__name__)

# Coordenadas iniciais para centralizar o mapa
initial_coords = [-15.7942, -47.8822]  # Brasília, Brasil
mapa = folium.Map(location=initial_coords, zoom_start=4)
folium.TileLayer("OpenTopoMap").add_to(mapa)

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
                mapa = folium.Map(location=initial_coords, zoom_start=4)
                folium.TileLayer("OpenTopoMap").add_to(mapa)
                for loc in locations:
                    folium.Marker(loc).add_to(mapa)
                # Salvar o mapa atualizado
                mapa.save(os.path.join('static', 'map.html'))
            except ValueError:
                pass  # Lidar com erro de formato inválido
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global mapa
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Nenhum arquivo enviado", 400
        file = request.files['file']
        if file.filename == '':
            return "Nenhum arquivo selecionado", 400
        if file and file.filename.endswith('.kml'):
            try:
                # Salvar o arquivo KML temporariamente
                temp_kml = 'temp.kml'
                file.save(temp_kml)
                
                # Carregar o KML usando geopandas
                gdf = gpd.read_file(temp_kml, driver='KML')
                
                # Converter para GeoJSON
                geojson_data = gdf.to_json()
                
                # Adicionar o GeoJSON ao mapa
                folium.GeoJson(geojson_data).add_to(mapa)
                
                # Salvar o mapa atualizado
                mapa.save(os.path.join('static', 'map.html'))
                
                # Remover o arquivo temporário
                os.remove(temp_kml)
                
                return redirect(url_for('index'))  # Redirecionar para a página principal
            except Exception as e:
                return f"Erro ao processar o arquivo: {str(e)}", 500
        else:
            return "Arquivo inválido. Por favor, envie um arquivo KML.", 400
    return render_template('upload.html')

if __name__ == '__main__':
    # Garantir que o diretório 'static' exista
    if not os.path.exists('static'):
        os.makedirs('static')
    # Salvar o mapa inicial
    mapa.save(os.path.join('static', 'map.html'))
    app.run(debug=True)
