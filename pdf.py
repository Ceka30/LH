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

def save_as_pdf(driver, output_pdf_path):
    # Usa DevTools para guardar la página como PDF
    result = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "format": "A4"
    })

    # Decodifica el resultado en base64 y guarda el archivo PDF
    with open(output_pdf_path, "wb") as file:
        file.write(base64.b64decode(result['data']))

def convert_html_to_pdf(input_html_path, output_pdf_path):
    try:
        # Configura las opciones de Chrome
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        # Abre el archivo HTML
        driver.get('file://' + input_html_path)

        time.sleep(2)
        # Espera a que la página cargue completamente
        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.TAG_NAME, "script"))
        # )

        # Guarda la página como PDF
        save_as_pdf(driver, output_pdf_path)
        print(f'PDF generado en: {output_pdf_path}')
    except Exception as e:
        print(f"Error al convertir {input_html_path}: {e}")
    finally:
        driver.quit()

def convert_all_html_in_folder(folder_path):
    start_time = time.time()  # Marca el inicio del tiempo

    html_files = [f for f in os.listdir(folder_path) if f.endswith(".html")]
    max_workers = os.cpu_count()  # Obtiene el número de núcleos de la CPU

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for filename in html_files:
            input_html_path = os.path.join(folder_path, filename)
            output_pdf_path = os.path.join(folder_path, filename.replace(".html", ".pdf"))
            futures.append(executor.submit(convert_html_to_pdf, input_html_path, output_pdf_path))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error en la conversión: {e}")

    end_time = time.time()  # Marca el final del tiempo
    total_time = round(end_time - start_time, 2)
    print(f'Tiempo total de la prueba: {total_time} segundos')

if __name__ == "__main__":
    folder_path = r'C:\Users\carlo\OneDrive\Escritorio\Proyectos\Lighthouse'
    convert_all_html_in_folder(folder_path)
