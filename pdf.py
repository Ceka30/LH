import os
import time
#import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    driver = None
    try:
        # Configura las opciones de Chrome
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")

        # Instala y configura chromedriver
        #chromedriver_autoinstaller.install()
        driver = webdriver.Chrome(options=options)
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
        if driver:
            driver.quit()

def convertir_all_htmls(pathCarpetaHTML, pathCarpetaPDF):
    inicio = time.time()

    archivosHTML = [f for f in os.listdir(pathCarpetaHTML) if f.endswith(".html")]

    if not os.path.exists(pathCarpetaPDF):
        os.makedirs(pathCarpetaPDF)

    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = []
        for nombreArchivo in archivosHTML:
            pathHTML = os.path.join(pathCarpetaHTML, nombreArchivo)
            pathPDF = os.path.join(pathCarpetaPDF, nombreArchivo.replace(".html", ".pdf"))
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
    current_directory = os.getcwd()
    pathCarpetaHTMLDesktop = f'{current_directory}/HTMLDesktop'
    pathCarpetaPDFDesktop = f'{current_directory}/PDFDesktop'
    pathCarpetaHTMLMobile = f'{current_directory}/HTMLMobile'
    pathCarpetaPDFMobile = f'{current_directory}/PDFMobile'

    print("Convirtiendo archivos HTMLDesktop a PDFDesktop...")
    convertir_all_htmls(pathCarpetaHTMLDesktop, pathCarpetaPDFDesktop)

    print("Convirtiendo archivos HTMLMobile a PDFMobile...")
    convertir_all_htmls(pathCarpetaHTMLMobile, pathCarpetaPDFMobile)
