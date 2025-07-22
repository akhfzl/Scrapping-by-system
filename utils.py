from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from dotenv import load_dotenv
import json, os
import time

load_dotenv()


def SettingSelenium():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-web-security')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(80)  
    wait = WebDriverWait(driver, 60)
    return driver, wait


def Autentication(driver, wait, link):
    driver.get(link)
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))

    email_input.send_keys(os.getenv('EMAIL'))
    password_input.send_keys(os.getenv('PASSWORD'))
    time.sleep(1)

    submit_button = wait.until(EC.presence_of_element_located((By.ID, "kt_sign_in_submit")))
    submit_button.click()

    try:
        wait.until(EC.url_changes(link))
        print("V Login berhasil.")
    except TimeoutException:
        print("X Login gagal.")
    return driver, wait


def SelectClass(driver, wait, link):
    driver.get(link)
    Select(wait.until(EC.element_to_be_clickable((By.ID, "filter-kategori-tema")))).select_by_value("material")
    Select(wait.until(EC.element_to_be_clickable((By.NAME, "is_publish")))).select_by_value("1")
    time.sleep(2)
    return driver, wait


def CollectLinkDetail(driver, wait, count_pages):
    try:
        tombol_cari = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Cari')]")))
        tombol_cari.click()
    except:
        pass

    overal_link = []

    for page in range(count_pages):
        print(f"🔄 Memproses halaman {page + 1}...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.btn-detail")))

        try:
            tombol_detail = driver.find_elements(By.CSS_SELECTOR, "a.btn-detail")
            judul_kelas = driver.find_elements(By.CSS_SELECTOR, "h5.mt-0")
        except StaleElementReferenceException:
            print("⚠️  Elemen stale, coba cari ulang...")
            time.sleep(1)
            tombol_detail = driver.find_elements(By.CSS_SELECTOR, "a.btn-detail")
            judul_kelas = driver.find_elements(By.CSS_SELECTOR, "h5.mt-0")

        for idx in range(min(len(tombol_detail), len(judul_kelas))):
            try:
                href = tombol_detail[idx].get_attribute("href")
                judul_txt = judul_kelas[idx].text
                if href:
                    overal_link.append({"judul": judul_txt, "url": href})
            except StaleElementReferenceException:
                print("❌ Gagal ambil href, elemen stale.")
                continue

        print(f"✅ Halaman {page + 1} selesai. Total link terkumpul: {len(overal_link)}")

        if page < count_pages - 1:
            try:
                tombol_next = wait.until(EC.element_to_be_clickable((By.ID, "table-kelas_next")))
                if "disabled" in tombol_next.get_attribute("class") or not tombol_next.is_enabled():
                    print("⛔ Tombol next nonaktif. Berhenti.")
                    break

                current_page = driver.find_element(By.CSS_SELECTOR, "li.paginate_button.active a").text
                tombol_next.click()

                wait.until(
                    lambda d: d.find_element(By.CSS_SELECTOR, "li.paginate_button.active a").text != current_page
                )

            except Exception as e:
                print("🚫 Gagal klik 'Next':", e)
                break

    with open("overal_link_class.json", "w", encoding="utf-8") as file:
        json.dump(overal_link, file, indent=2, ensure_ascii=False)

    return overal_link


def OpenDiscussionTab(driver, wait):
    try:
        tab_diskusi = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#kt_tab_diskusi"]')))
        tab_diskusi.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.accordion-button')))
    except:
        print("X Tab diskusi tidak ditemukan.")


def OpenFeedbackTab(driver, wait):
    try:
        tab_feedback = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#kt_tab_feedback"]')))
        tab_feedback.click()
        wait.until(EC.presence_of_element_located((By.ID, "table-peserta-feedback")))
    except:
        print("X Tab feedback tidak ditemukan.")


def SubTopicAll(driver, wait, judul):
    comment_found = []

    accordion_buttons = driver.find_elements(By.CSS_SELECTOR, '.accordion-button')
    for topik_btn in accordion_buttons:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", topik_btn)
            topik_btn.click()
            time.sleep(0.5)
        except:
            continue

    subtopik_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.btn-menu-topik[data-topik]')
    for subtopik in subtopik_buttons:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", subtopik)
            subtopik.click()
            time.sleep(1)

            komentar_divs = driver.find_elements(By.CSS_SELECTOR, 'div.media.row.g-0.mb-1.p-3')
            for div in komentar_divs:
                try:
                    media_body = div.find_element(By.CLASS_NAME, "media-body")
                    ps = media_body.find_elements(By.TAG_NAME, "p")

                    semua_komentar = "\n".join([p.text.strip() for p in ps if p.text.strip()])

                    if semua_komentar:
                        comment_found.append({
                            'user_statement': semua_komentar,
                            'judul': judul,
                            'rating': '',
                            'type': 'komentar/pertanyaan',
                            "kategori": "Smartclass",
                            "pusat_inovasi": "Semua Pusat Inovasi",
                            "status": "publish",
                            "tema": "Semua tema",
                        })
                except:
                    continue
        except:
            continue

    return comment_found

def ScrapeFeedback(driver, wait, judul):
    feedback_data = []

    try:
        wait.until(EC.presence_of_element_located((By.ID, "table-peserta-feedback")))

        page_number = 1  

        while True:
            print(f"[INFO] Halaman {page_number}...")

            for _ in range(5):  
                time.sleep(5)
                rows = driver.find_elements(By.CSS_SELECTOR, "#table-peserta-feedback > tbody > tr")
                rows_td = rows[0].find_elements(By.TAG_NAME, "td")
                print('rows td -> ', rows_td)
                if rows and len(rows_td) >= 4:
                    print('break cols < 4')
                    break
                print("[WAIT] Menunggu baris muncul...")
                time.sleep(5)
            else:
                print("[WARN] Tidak ada baris yang valid di halaman ini.")
                break  

            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 4:
                        nilai = cols[2].text.strip()
                        feedback = cols[3].text.strip()

                        if nilai or feedback:
                            feedback_data.append({
                                "user_statement": feedback,
                                "rating": nilai,
                                "kategori": "Smartclass",
                                "pusat_inovasi": "Semua Pusat Inovasi",
                                "status": "publish",
                                "tema": "Semua tema",
                                "judul": judul,
                                "type": "feedback"
                            })
                except Exception as e:
                    print(f"[ERROR] Gagal parsing baris: {e}")
                    continue

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "#table-peserta-feedback_next")
                if "disabled" in next_button.get_attribute("class"):
                    print("[INFO] Halaman terakhir, selesai.")
                    break
                else:
                    first_row = rows[0]
                    next_button.click()
                    wait.until(EC.staleness_of(first_row))
                    page_number += 1
            except Exception as e:
                print(f"[WARN] Tombol next tidak ditemukan atau gagal klik: {e}")
                break

    except Exception as e:
        print(f"[FATAL] Gagal mengambil data feedback: {e}")

    return feedback_data

def scraping_komentar(driver, wait):
    all_comments = []
    all_feedbacks = []

    link_kelas = CollectLinkDetail(driver, wait, 4)

    for index, url in enumerate(link_kelas, 1):
        try:
            print(f"\n>>> Memproses kelas {index}: {url['url']}")
            try:
                driver.get(url['url'])
            except TimeoutException:
                print(f"X Timeout saat membuka {url['url']}")
                continue

            OpenDiscussionTab(driver, wait)
            comment_by_class = SubTopicAll(driver, wait, url['judul'])
            all_comments.extend(comment_by_class)
            print(f">>> Komentar diskusi: {len(comment_by_class)}")

            OpenFeedbackTab(driver, wait)
            feedback_by_class = ScrapeFeedback(driver, wait, url['judul'])
            all_feedbacks.extend(feedback_by_class)
            print(f"Feedback ditemukan: {len(feedback_by_class)}")

        except Exception as e:
            print(f"!!! Gagal memproses kelas {url['url']}: {e}")
            continue

    with open("comments_by_classes.json", "w") as file:
        json.dump(all_comments, file, indent=2)

    with open("feedback_by_classes.json", "w") as file:
        json.dump(all_feedbacks, file, indent=2)

    return all_comments, all_feedbacks