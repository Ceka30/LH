import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import base64
from concurrent.futures import ProcessPoolExecutor, as_completed

def guardar_como_pdf(driver, pathPDF):
    # Usa DevTools para guardar la página como PDF
    result = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "format": "A4"
    })

    # Decodifica el resultado en base64 y guarda el archivo PDF
    with open(pathPDF, "wb") as archivo:
        archivo.write(base64.b64decode(result['data']))

def convertir_a_pdf(pathHTML, pathPDF):
    try:
        # Configura las opciones de Chrome
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.get('file://' + pathHTML)

        # Espera a que la página cargue completamente
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "script"))
        )

        # Guarda la página como PDF
        guardar_como_pdf(driver, pathPDF)
        print(f'PDF generado en: {pathPDF}')
    except Exception as e:
        print(f"Error al convertir {pathHTML}: {e}")
    finally:
        driver.quit()

def convertir_all_htmls(pathCarpeta):
    inicio = time.time()

    archivosHTML = [f for f in os.listdir(pathCarpeta) if f.endswith(".html")]

    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = []
        for nombreArchivo in archivosHTML:
            pathHTML = os.path.join(pathCarpeta, nombreArchivo)
            pathPDF = os.path.join(pathCarpeta, nombreArchivo.replace(".html", ".pdf"))
            futures.append(executor.submit(convertir_a_pdf, pathHTML, pathPDF))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error en la conversión: {e}")

    termino = time.time()
    totalTest = round(termino - inicio, 2)
    print(f'Tiempo total de la prueba: {totalTest} segundos')

if __name__ == "__main__":
    pathCarpeta = r'C:\Users\carlo\OneDrive\Escritorio\Proyectos\Lighthouse'
    convertir_all_htmls(pathCarpeta)
