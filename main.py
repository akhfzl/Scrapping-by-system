from utils import SettingSelenium, Autentication, SelectClass, scraping_komentar

if __name__ == '__main__':
    driver, wait = SettingSelenium()
    driver, wait = Autentication(driver, wait, 'https://smartidapp.co.id/auth?redirect=')
    driver, wait = SelectClass(driver, wait, 'https://smartidapp.co.id/admin/kelas')
    scraping_komentar(driver, wait)