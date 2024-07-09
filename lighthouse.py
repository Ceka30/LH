import json
import re
import time
import subprocess
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from openpyxl import Workbook, load_workbook

# Función para verificar si una URL responde con un código de estado 200 y obtener el código de estado y su descripción
def validar_url(url):
    try:
        response = requests.head(url, allow_redirects=True)
        codigo = response.status_code
        if codigo == 200:
            # Realizar una solicitud GET para verificar el contenido de la página
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            titulo = soup.title.string if soup.title else ""
            if "Error" in titulo or "Página de Error | Entel" in titulo:
                codigo = 404
                descripcion = "Página de Error Detectada"
                print(f"Error al verificar la URL {url}: {codigo} {descripcion}")
            else:
                descripcion = "OK"
        else:
            descripcion = requests.status_codes._codes[codigo][0].replace('_', ' ').title()
        return codigo, descripcion
    except requests.RequestException as e:
        print(f"Error al verificar la URL {url}: {e}")
        return None, str(e)

# Función para ejecutar Lighthouse en una URL específica (Mobile - Desktop)
def auditoria_Lighthouse(url, mode):
    nombre_limpio = re.sub(r'[^\w.-]', '_', url)
    final_HTML = f'{mode}_{nombre_limpio}.html'

    # Ruta completa al ejecutable de Node.js
    #node_path = '/Users/carlosgomez/.nvm/versions/node/v20.15.1/bin/node'
    node_path = r'C:\Program Files\nodejs\node.exe'  # Cambia esto por la ruta completa de node.exe

    # Ruta completa al archivo de Lighthouse
    #lighthouse_path = '/Users/carlosgomez/.nvm/versions/node/v20.15.1/lib/node_modules/lighthouse/cli/index.js'
    lighthouse_path = r'C:\Users\carlo\AppData\Roaming\npm\node_modules\lighthouse\cli\index.js'  # Cambia esto por la ruta completa encontrada

    # Comando para ejecutar Lighthouse con la configuración necesaria
    command = [
        node_path,
        lighthouse_path,
        url,
        '--output=html',
        f'--output-path={final_HTML}',
        '--chrome-flags=--incognito --headless --no-sandbox --disable-gpu --disable-dev-shm-usage'
    ]

    # Configuración extra para el modo Desktop
    if mode == 'desktop':
        command.append('--preset=desktop')

    try:
        # Ejecuta la auditoría de Lighthouse
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error al ejecutar Lighthouse desde {url} ({mode}):\n{result.stderr}")
            return None
    except FileNotFoundError:
        print(f"Lighthouse no se encontró en la ruta especificada. Asegúrate de que está instalado y accesible en {lighthouse_path}.")
        return None
    
    print(f"Se genera informe {final_HTML}")
    return final_HTML

# Función para extraer el contenido JSON desde el string
def extraer_Contenido(string):
    match = re.search(r'=(.*?);<', string)
    if match:
        return match.group(1)
    else:
        return None

# Función para extraer las puntuaciones de SEO, Accesibilidad y Performance del reporte HTML
def extraer_puntuaciones(html_path):
    try:
        scores = {
            'performance': None,
            'accessibility': None,
            'seo': None
        }

        with open(html_path, 'r', encoding="utf-8") as file:
            lines = file.readlines()
        
        # Buscamos la línea que contiene los datos JSON
        json_line = next((line for line in lines if 'window.__LIGHTHOUSE_JSON__' in line), None)
        if json_line:
            resultados = extraer_Contenido(json_line)
            data = json.loads(resultados)
            scores['performance'] = data["categories"]["performance"]["score"]
            scores['accessibility'] = data["categories"]["accessibility"]["score"]
            scores['seo'] = data["categories"]["seo"]["score"]

        return scores
    except Exception as e:
        print(f"Error al extraer puntuaciones desde {html_path}: {e}")
        return {
            'performance': None,
            'accessibility': None,
            'seo': None
        }

# Función para actualizar el archivo Excel con los resultados usando openpyxl
def actualizar_excel(url, scores_mobile, scores_desktop, codigo, descripcion_codigo):
    file_path = 'resultados.xlsx'
    try:
        wb = load_workbook(file_path)
        ws = wb.active
    except FileNotFoundError:
        wb = Workbook()
        ws = wb.active
        ws.append(['URL', 'Performance Mobile', 'Performance Desktop', 'Accesibilidad Mobile', 'Accesibilidad Desktop', 'SEO Mobile', 'SEO Desktop', 'Código', 'Descripción Código'])

    updated = False
    for row in ws.iter_rows(min_row=2, values_only=False):
        if row[0].value == url:
            row[1].value = scores_mobile['performance']
            row[2].value = scores_desktop['performance']
            row[3].value = scores_mobile['accessibility']
            row[4].value = scores_desktop['accessibility']
            row[5].value = scores_mobile['seo']
            row[6].value = scores_desktop['seo']
            row[7].value = codigo
            row[8].value = descripcion_codigo
            updated = True
            break

    if not updated:
        new_row = [
            url,
            scores_mobile['performance'], scores_desktop['performance'],
            scores_mobile['accessibility'], scores_desktop['accessibility'],
            scores_mobile['seo'], scores_desktop['seo'],
            codigo, descripcion_codigo
        ]
        ws.append(new_row)

    # Ajustar el ancho de las columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    wb.save(file_path)

# Función que ejecuta Lighthouse para una URL
def urls_Lighthouse(url):
    codigo, descripcion_codigo = validar_url(url)
    if codigo is None or codigo != 200:
        # Si la URL no es válida, registrar el error en el Excel
        actualizar_excel(url, {'performance': None, 'accessibility': None, 'seo': None}, {'performance': None, 'accessibility': None, 'seo': None}, "Error", descripcion_codigo)
        return {
            'url': url,
            'total_test': None
        }

    inicio = time.time()

    # Ejecutar Lighthouse (Mobile - Desktop)
    reporte_MOBILE = auditoria_Lighthouse(url, 'mobile')
    if reporte_MOBILE:
        scores_mobile = extraer_puntuaciones(reporte_MOBILE)
    else:
        scores_mobile = {'performance': None, 'accessibility': None, 'seo': None}

    reporte_DESKTOP = auditoria_Lighthouse(url, 'desktop')
    if reporte_DESKTOP:
        scores_desktop = extraer_puntuaciones(reporte_DESKTOP)
    else:
        scores_desktop = {'performance': None, 'accessibility': None, 'seo': None}

    # Actualizar el archivo Excel después de completar ambas auditorías
    actualizar_excel(url, scores_mobile, scores_desktop, codigo, descripcion_codigo)
    
    termino = time.time()
    
    total_test = round(termino - inicio, 2)
    
    return {
        'url': url,
        'total_test': total_test
    }

# Leer las URLs desde un archivo de texto
with open('urls.txt', 'r') as archivo:
    urls = archivo.read().splitlines()

# Ejecutar las pruebas en paralelo
with ThreadPoolExecutor(max_workers=1) as ejec:
    future_to_url = {ejec.submit(urls_Lighthouse, url): url for url in urls}
    
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            result = future.result()
            if result['total_test'] is not None:
                print(f"Duración total de la auditoría para {url}: {result['total_test']} segundos")
        except Exception as e:
            print(f"Error de procesamiento en {url}: {e}")
