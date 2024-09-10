from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import folium
import os
import geopandas as gpd
from werkzeug.utils import secure_filename
import zipfile
import json
import markdown

app = Flask(__name__, static_folder='static')

# Coordenadas iniciais para centralizar o mapa
initial_coords = [-5.315518848620957, -61.98811551121906]  # Brasília, Brasil
mapa = folium.Map(location=initial_coords, zoom_start=7)
folium.TileLayer("Stadia.AlidadeSatellite").add_to(mapa)

# Lista para armazenar as localizações adicionadas e shapefiles
locations = []
shapefiles = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global mapa, locations, shapefiles
    error_message = None
    if request.method == 'POST':
        # Capturar o tipo selecionado pelo usuário
        shapefile_type = request.form.get('type')
        
        # Definir a cor com base no tipo selecionado
        color = 'blue'  # Cor padrão
        if shapefile_type == 'ruas':
            color = 'red'  # ou '#FF0000'
        elif shapefile_type == 'cidades':
            color = 'lightgreen'  # ou '#90EE90'
        elif shapefile_type == 'areas_indigenas':
            color = 'lightyellow'  # ou '#FFFFE0'

        # Processar o shapefile e outras informações...
        shapefiles.append({'type': shapefile_type, 'color': color})

        coords = request.form.get('coords')
        info = request.form.get('info')
        if coords and info:
            try:
                lat, lon = map(float, coords.split(','))
                # Verificar se a coordenada já existe
                if any(loc['coords'] == (lat, lon) for loc in locations):
                    error_message = "Essa coordenada já foi inserida"
                else:
                    # Converter Markdown para HTML
                    info_html = markdown.markdown(info)
                    # Adicionar a nova localização com informações
                    location = {
                        'coords': (lat, lon),
                        'info': info_html
                    }
                    locations.append(location)
                    # Atualizar o mapa
                    update_map()
            except ValueError:
                error_message = "Formato de coordenada inválido!"
    return render_template('index.html', shapefiles=shapefiles, locations=locations, enumerate=enumerate, error_message=error_message)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global mapa, locations, shapefiles
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Nenhum arquivo enviado", 400
        file = request.files['file']
        info = request.form.get('info', '')  # Adicionar campo para informações com valor padrão
        shapefile_type = request.form.get('type', 'default')  # Tipo de shapefile (ruas, cidades, etc.)
        
        # Definir a cor com base no tipo selecionado
        color = 'blue'  # Cor padrão
        if shapefile_type == 'ruas':
            color = 'red'  # ou '#FF0000'
        elif shapefile_type == 'cidades':
            color = 'lightgreen'  # ou '#90EE90'
        elif shapefile_type == 'areas_indigenas':
            color = 'lightyellow'  # ou '#FFFFE0'
        
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
                
                # Adicionar o shapefile com o tipo e informação
                shapefiles.append({
                    'data': geojson_data,
                    'info': markdown.markdown(info),
                    'type': shapefile_type,  # Salvar o tipo de shapefile
                    'color': color  # Salvar a cor do shapefile
                })
                
                # Atualizar o mapa
                update_map()
                
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

def update_map():
    global mapa, locations, shapefiles
    mapa = folium.Map(location=initial_coords, zoom_start=7)
    folium.TileLayer("Esri.WorldImagery", name="Satélite 1").add_to(mapa)
    folium.TileLayer("Stadia.AlidadeSatellite").add_to(mapa)
    
    # Caminho do ícone personalizado
    icon_path = os.path.join('static', 'images', 'iconcoord.png')
    
    for loc in locations:
        popup_content = f"""
        <div class='popup-content' style='max-width:300px; max-height:200px; overflow-y:auto;'>
            <div class='popup-info'>{loc['info']}</div>
        </div>
        """
        folium.Marker(
            loc['coords'],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.CustomIcon(icon_path, icon_size=(30, 30))  # Usando o ícone personalizado
        ).add_to(mapa)
    
    for shapefile in shapefiles:
        overlay = folium.FeatureGroup(name='Shapefile Overlay')
        folium.GeoJson(
            shapefile['data'],
            style_function=lambda feature, color=shapefile['color']: {
                'fillColor': color,
                'color': color,
                'weight': 2,
                'fillOpacity': 0.5
            },
            popup=folium.Popup(shapefile['info'], max_width=300) if shapefile['info'] else None
        ).add_to(overlay)
        overlay.add_to(mapa)
    
    folium.LayerControl().add_to(mapa)
    mapa.save(os.path.join('static', 'map.html'))

@app.route('/reset', methods=['POST'])
def reset():
    global locations, shapefiles, mapa
    locations = []
    shapefiles = []
    mapa = folium.Map(location=initial_coords, zoom_start=7)
    folium.TileLayer("Stadia.AlidadeSatellite").add_to(mapa)
    mapa.save(os.path.join('static', 'map.html'))
    return redirect(url_for('index'))

@app.route('/delete_shapefile/<int:index>', methods=['POST'])
def delete_shapefile(index):
    global mapa, shapefiles
    if 0 <= index < len(shapefiles):
        del shapefiles[index]
        # Atualizar o mapa
        update_map()
    return redirect(url_for('index'))

@app.route('/delete_location/<int:index>', methods=['POST'])
def delete_location(index):
    global mapa, locations, shapefiles
    if 0 <= index < len(locations):
        del locations[index]
        # Atualizar o mapa
        update_map()
    return redirect(url_for('index'))

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    # Garantir que o diretório 'static' exista
    if not os.path.exists('static'):
        os.makedirs('static')
    # Salvar o mapa inicial
    mapa.save(os.path.join('static', 'map.html'))
    app.run(debug=True) 