import time
import json
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from jinja2 import Template
from concurrent.futures import ThreadPoolExecutor, as_completed

# Función para ejecutar Lighthouse en una URL específica (Mobile - Desktop)
def auditoria_Lighthouse(url, mode):
    # Ruta salida informe JSON
    final_JSON = f'report_{mode}_{url.replace("https://", "").replace("/", "_")}.json'
    
    # Comando para ejecutar Lighthouse con la config necesaria
    command = [
        'lighthouse',
        url,
        '--output=json',
        f'--output-path={final_JSON}',
        '--chrome-flags="--headless --no-sandbox --disable-gpu --disable-dev-shm-usage"'
    ]
    # Configuracion extra para el modo Desktop
    if mode == 'desktop':
        command.append('--preset=desktop')
    
    # Eejcuta la auditoria de Lighthouse y captura cualquier salida o error generado por el comando.
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Si el comando no se ejecutó correctamente, imprime el error
    if result.returncode != 0:
        print(f"Error al ejecutar Lighthouse desde {url} ({mode}):\n{result.stderr}")
        return None
    
    
    try:
        with open(final_JSON, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # Extraer las puntuaciones de rendimiento, accesibilidad y SEO
        performance = report['categories']['performance']['score']
        accessibility = report['categories']['accessibility']['score']
        seo = report['categories']['seo']['score']
        
        return {
            'url': url,
            'mode': mode,
            'performance': performance,
            'accessibility': accessibility,
            'seo': seo
        }
    except FileNotFoundError:
        print(f"Archivo {final_JSON} no encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"Error al decodificar el archivo JSON: {final_JSON}.")
        return None

# Funcion que levanta Google Chrome y ejecuta Lighthouse para una URL
def urls_Lighthouse(url):
    # Configuracion de Google Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(url)

    time.sleep(10)
    inicio = time.time()

    # Ejecutar Lighthouse (Movile - Desktop)
    resultados_MOBILE = auditoria_Lighthouse(url, 'mobile')
    resultados_DESKTOP = auditoria_Lighthouse(url, 'desktop')
    
    termino = time.time()
    driver.quit()
    
    total_test = round(termino - inicio, 2)
    
    return {
        'url': url,
        'resultados_MOBILE': resultados_MOBILE,
        'resultados_DESKTOP': resultados_DESKTOP,
        'total_test': str(total_test)
    }

# Función para generar un informe HTML con los resultados de Lighthouse
def generarReporte(url, resultados_MOBILE, resultados_DESKTOP, total_test):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lighthouse Report</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f0f0f0;
        }

        h1 {
            margin-top: 0;
            text-align: center;
        }

        table {
            width: auto;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th, td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }

        th {
            background-color: #f4f4f41c;
        }

        canvas {
            width: 150px;
            height: 150px;
            margin: 10px;
        }
        </style>
    </head>
    <body>
        <h1>Reporte Lighthouse - URL : {{ url }}</h1>
        <p>Duracion de la Auditoria: {{ total_test }} segundos</p>
        <table>
            <thead>
                <tr>
                    <th>Metricas</th>
                    <th>Mobile</th>
                    <th>Desktop</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Performance</td>
                    <td><canvas id="mobilePerformance"></canvas></td>
                    <td><canvas id="desktopPerformance"></canvas></td>
                </tr>
                <tr>
                    <td>Accessibility</td>
                    <td><canvas id="mobileAccessibility"></canvas></td>
                    <td><canvas id="desktopAccessibility"></canvas></td>
                </tr>
                <tr>
                    <td>SEO</td>
                    <td><canvas id="mobileSEO"></canvas></td>
                    <td><canvas id="desktopSEO"></canvas></td>
                </tr>
            </tbody>
        </table>
        <script>
            function getColor(score) {
                if (score < 0.5) {
                    return '#b81818';  // Rojo
                } else if (score < 0.9) {
                    return '#FFA500';  // Amarillo
                } else {
                    return '#13ab34';  // Verde
                }
            }

            function renderChart(id, value) {
                const ctx = document.getElementById(id).getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: [value * 100, 100 - (value * 100)],
                            backgroundColor: [getColor(value), '#ddd']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutoutPercentage: 50,
                        tooltips: { enabled: false },
                        plugins: {
                            datalabels: {
                                display: true,
                                formatter: (val, ctx) => {
                                    if (ctx.dataIndex === 0) {
                                        return `${value * 100}%`;
                                    } else {
                                        return '';
                                    }
                                },
                                color: '#000',
                                font: { weight: 'bold', size: 20 }
                            }
                        }
                    },
                    plugins: [{
                        beforeDraw: function(chart) {
                            var width = chart.width,
                                height = chart.height,
                                ctx = chart.ctx;
                            ctx.restore();
                            var fontSize = (height / 114).toFixed(2);
                            ctx.font = fontSize + "em sans-serif";
                            ctx.textBaseline = "middle";
                            var text = (value * 100).toFixed(0) + "%",
                                textX = Math.round((width - ctx.measureText(text).width) / 2),
                                textY = height / 2;
                            ctx.fillText(text, textX, textY);
                            ctx.save();
                        }
                    }]
                });
            }

            document.addEventListener('DOMContentLoaded', function() {
                renderChart('mobilePerformance', {{ mobile.performance }});
                renderChart('desktopPerformance', {{ desktop.performance }});
                renderChart('mobileAccessibility', {{ mobile.accessibility }});
                renderChart('desktopAccessibility', {{ desktop.accessibility }});
                renderChart('mobileSEO', {{ mobile.seo }});
                renderChart('desktopSEO', {{ desktop.seo }});
            });
        </script>
    </body>
    </html>
    """

    # Renderizar el contenido del informe HTML utilizando la plantilla y los datos proporcionados
    template = Template(html_template)
    contenido_HTML = template.render(url=url, mobile=resultados_MOBILE, desktop=resultados_DESKTOP, total_test=total_test)

    # Nombre del reporte = nombre de la URL
    reporte_URL = f'{url.replace("https://", "").replace("/", "_")}.html'
    # Escribe el contenido HTML en el archivo
    with open(reporte_URL, 'w', encoding='utf-8') as f:
        f.write(contenido_HTML)

    print(f"Reporte Lighthouse: {reporte_URL}")

# Leer las URLs desde un archivo de texto
with open('urls.txt', 'r') as archivo:
    urls = archivo.read().splitlines()

# Ejecutar las pruebas en paralelo
with ThreadPoolExecutor(max_workers=2) as ejec:

    future_to_url = {ejec.submit(urls_Lighthouse, url): url for url in urls}
    
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            result = future.result()
            # Generar el informe HTML para la URL procesada
            generarReporte(result['url'], result['resultados_MOBILE'], result['resultados_DESKTOP'], result['total_test'])
        except Exception as e:
            print(f"Error de procesamiento en {url}: {e}")
