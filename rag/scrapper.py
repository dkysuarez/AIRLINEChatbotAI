import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AirIndiaSeleniumScraper:
    def __init__(self):
        """Inicializa el scraper con Chrome visible para debug"""
        self.data_dir = "data/raw"
        os.makedirs(self.data_dir, exist_ok=True)

        # Configuración de Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless=False")  # Cambia a True si no quieres ver la ventana
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)

    def close_popups_and_cookies(self):
        """Cierra banners de cookies y chat bot"""
        print("   🔒 Cerrando popups y cookies...")
        time.sleep(3)
        try:
            # Aceptar cookies
            accept_btn = self.driver.find_element(By.CSS_SELECTOR, "button[id*='onetrust-accept'], button:has-text('Accept all'), button:has-text('Accept')")
            self.driver.execute_script("arguments[0].click();", accept_btn)
            time.sleep(2)
            print("   ✅ Cookies aceptadas")
        except:
            pass

        try:
            # Cerrar chat bot
            close_chat = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close'], button.close, .close-chat")
            close_chat.click()
            time.sleep(1)
        except:
            pass

    def force_expand_all_accordions(self):
        """Método infalible: fuerza expansión de TODOS los accordions con JavaScript"""
        print("   🔓 Forzando expansión de todos los accordions...")
        script = """
        // Click en todos los botones accordion
        document.querySelectorAll('button.accordion-button').forEach(btn => {
            btn.click();
        });
        // Forzar visibilidad de todo el contenido colapsable
        document.querySelectorAll('.accordion-collapse').forEach(collapse => {
            collapse.classList.add('show');
            collapse.style.display = 'block';
        });
        // Remover clase collapsed y actualizar aria-expanded
        document.querySelectorAll('button.accordion-button').forEach(btn => {
            btn.classList.remove('collapsed');
            btn.setAttribute('aria-expanded', 'true');
        });
        """
        self.driver.execute_script(script)
        time.sleep(5)  # Tiempo para que todo el contenido cargue

    def extract_tables_formatted(self):
        """Extrae todas las tablas y las formatea como texto legible con cabeceras en negrita"""
        print("   📊 Extrayendo y formateando todas las tablas...")
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        table_text = ""
        for i, table in enumerate(tables):
            table_text += f"\n{'='*100}\nTABLA {i+1} - BAGGAGE ALLOWANCE\n{'='*100}\n"
            rows = table.find_elements(By.TAG_NAME, "tr")
            for j, row in enumerate(rows):
                cells = row.find_elements(By.TAG_NAME, "td") + row.find_elements(By.TAG_NAME, "th")
                row_line = " | ".join([cell.text.strip() for cell in cells if cell.text.strip()])
                if row_line:
                    # Poner cabeceras en negrita
                    if j == 0 or any(keyword in row_line.lower() for keyword in ["cabin", "from", "to", "brand", "class"]):
                        table_text += f"**{row_line}**\n"
                    else:
                        table_text += row_line + "\n"
            table_text += "\n"
        return table_text

    def scrape_page(self, url, filename):
        """Scrapea una página completa: cierra popups, expande accordions, extrae texto + tablas"""
        print(f"\n🌐 Navegando a: {url}")
        self.driver.get(url)
        time.sleep(5)

        self.close_popups_and_cookies()

        self.force_expand_all_accordions()

        # Scroll final para asegurar carga completa
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Texto general de la página
        full_text = self.driver.find_element(By.TAG_NAME, "body").text

        # Tablas formateadas
        tables_text = self.extract_tables_formatted()

        # Combinar todo
        content = full_text + "\n\n" + tables_text

        # Guardar
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"FUENTE: {url}\n")
            f.write(f"FECHA DE SCRAPEO: 2025-12-24\n")
            f.write("="*120 + "\n\n")
            f.write(content)

        print(f"✅ Guardado: {filename} ({len(content)} caracteres) - Tablas completas incluidas")

    def run_all(self):
        """Ejecuta el scraper para todas las páginas importantes"""
        pages = {
            "baggage_guidelines.txt": "https://www.airindia.com/in/en/travel-information/baggage-guidelines.html",
            "checked_baggage.txt": "https://www.airindia.com/in/en/travel-information/baggage-guidelines/checked-baggage-allowance.html",
            "faq_baggage.txt": "https://www.airindia.com/in/en/frequently-asked-questions/baggage.html",
            "web_checkin.txt": "https://www.airindia.com/in/en/manage/web-checkin.html",
            "flight_status.txt": "https://www.airindia.com/in/en/manage/flight-status.html"
        }

        print("🛫 INICIANDO SCRAPER COMPLETO DE AIR INDIA")
        print("=" * 80)

        for filename, url in pages.items():
            self.scrape_page(url, filename)
            time.sleep(5)  # Pausa entre páginas para no sobrecargar

        self.driver.quit()
        print("\n🎉 ¡SCRAPING COMPLETO! Todos los archivos guardados en data/raw/")
        print("   Ahora puedes usar estos .txt para crear el vectorstore del RAG.")

if __name__ == "__main__":
    scraper = AirIndiaSeleniumScraper()
    scraper.run_all()