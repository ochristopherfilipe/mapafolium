from flask import Flask, render_template, request, redirect, url_for
import folium
import os

app = Flask(__name__)

# Coordenadas iniciais para centralizar o mapa
initial_coords = [-15.7942, -47.8822]  # Brasília, Brasil
mapa = folium.Map(location=initial_coords, zoom_start=4)
folium.TileLayer ("OpenTopoMap"). add_to(mapa)
# Lista para armazenar as localizações adicionadas
locations = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global mapa
    if request.method == 'POST':
        coords = request.form.get('coords')
        if coords:
            try:
                lat, lon = map(float, coords.split(','))
                # Adicionar marcação no mapa
                location = (lat, lon)
                locations.append(location)
                folium.Marker(location).add_to(mapa)
                # Garantir que o diretório 'static' exista
                if not os.path.exists('static'):
                    os.makedirs('static')
                mapa.save(os.path.join('static', 'map.html'))
            except ValueError:
                # Lidar com erro de formato inválido
                pass
    return render_template('index.html')

if __name__ == '__main__':
    # Garantir que o diretório 'static' exista
    if not os.path.exists('static'):
        os.makedirs('static')
    # Salvar o mapa inicial
    mapa.save(os.path.join('static', 'map.html'))
    app.run(debug=True)
