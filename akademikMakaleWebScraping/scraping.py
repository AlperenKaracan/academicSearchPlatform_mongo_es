import requests
import os
import random
from bs4 import BeautifulSoup
from datetime import datetime
from spellchecker import SpellChecker

DERGIPARK_BASE_URL = "https://dergipark.org.tr"
spellchecker = SpellChecker()

def correct_spelling(sentence: str) -> str:
    if not sentence:
        return ""

    words = sentence.strip().split()
    corrected_words = []
    for w in words:
        c = spellchecker.correction(w)
        if c is None:
            c = w
        corrected_words.append(str(c))
    return " ".join(corrected_words)

def turkce_tarih_to_datetime(turkce_tarih):
    turkce_aylar = {
        'ocak': 'January', 'şubat': 'February', 'mart': 'March', 'nisan': 'April',
        'mayıs': 'May', 'haziran': 'June', 'temmuz': 'July', 'ağustos': 'August',
        'eylül': 'September', 'ekim': 'October', 'kasım': 'November', 'aralık': 'December'
    }

    if not turkce_tarih:
        return None

    try:
        parts = turkce_tarih.strip().split()
        if len(parts) < 3:
            return None

        ay_ing = turkce_aylar.get(parts[1].lower())
        if not ay_ing:
            return None

        parts[1] = ay_ing
        ingilizce_tarih = " ".join(parts)

        dt = datetime.strptime(ingilizce_tarih, '%d %B %Y')
        return dt

    except Exception as e:
        print("Tarih parse hatası:", e)
        return None

def scrape_dergipark(aranacak_kelimeler: str, limit=10) -> list:

    aranacak_kelimeler = correct_spelling(aranacak_kelimeler.strip())
    aranacak_kelimeler_url = aranacak_kelimeler.replace(" ", "+")
    url = f"{DERGIPARK_BASE_URL}/tr/search?q={aranacak_kelimeler_url}&section=articles"

    makale_listesi = []
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "lxml")
        article_divs = soup.find(class_='article-cards')
        if not article_divs:
            return makale_listesi

        cards = article_divs.find_all("div", class_="card article-card dp-card-outline")
        for i, card in enumerate(cards):
            if i >= limit:
                break
            makale_data = {}
            title_a = card.find("a")
            if not title_a:
                continue

            makale_data["makale_isim"] = title_a.text.strip()
            makale_data["makale_site_URL"] = title_a["href"]

            detail_page = requests.get(makale_data["makale_site_URL"])
            detail_soup = BeautifulSoup(detail_page.content, "lxml")

            try:
                pdf_a = detail_soup.find(id='article-toolbar').find("a", title="Makale PDF linki")
                if pdf_a:
                    makale_data["PDF_URL"] = DERGIPARK_BASE_URL + pdf_a["href"]
                else:
                    makale_data["PDF_URL"] = ""
            except Exception:
                makale_data["PDF_URL"] = ""


            try:
                yazar_p = detail_soup.find("p", class_='article-authors')
                makale_data["makale_yazar"] = yazar_p.text.strip() if yazar_p else ""
            except:
                makale_data["makale_yazar"] = ""

            try:
                portlet_div = detail_soup.find("div", id='article-main-portlet')
                title_div = portlet_div.find("div", class_='kt-portlet__head-title')
                makale_data["makale_tur"] = title_div.text.strip() if title_div else ""
            except:
                makale_data["makale_tur"] = ""

            try:
                ozet_div = detail_soup.find("div", id="article_tr").find("div", class_="article-abstract data-section")
                if ozet_div:
                    makale_data["makale_ozet"] = ozet_div.text.replace("\nÖz\n", "").strip()
                else:
                    makale_data["makale_ozet"] = ""
            except:
                makale_data["makale_ozet"] = ""

            makale_data["makale_anahtarkelimeler_tarayici"] = aranacak_kelimeler
            makale_data["makale_yayinciadi"] = "Dergi Park"
            makale_data["makale_alintisayisi"] = random.randint(1, 50)

            # Anahtar kelimeler
            try:
                anahtar_div = detail_soup.find("div", id="article_tr").find("div", class_="article-keywords data-section")
                if anahtar_div:
                    anahtar = anahtar_div.text.replace("Anahtar Kelimeler\n", "").strip()
                    makale_data["makale_anahtarkelimeler"] = anahtar
                else:
                    makale_data["makale_anahtarkelimeler"] = ""
            except:
                makale_data["makale_anahtarkelimeler"] = ""

            makale_data["makale_referanslar"] = []
            try:
                citations_div = detail_soup.find("div", id="article_tr").find("div", class_="article-citations data-section")
                if citations_div:
                    ref_list = citations_div.find("ul", class_="fa-ul")
                    if ref_list:
                        refs = ref_list.find_all("li")
                        for r in refs:
                            makale_data["makale_referanslar"].append(r.text.strip())

                makale_data["makale_alintisayisi"] = len(makale_data["makale_referanslar"])
            except:
                pass
            makale_data["makale_tarih"] = None
            try:
                table = detail_soup.find("table", class_='record_properties table')
                if table:
                    table_rows = table.find_all("tr")
                    for tr in table_rows:
                        th_text = tr.find("th").text.strip() if tr.find("th") else ""
                        td_text = tr.find("td").text.strip() if tr.find("td") else ""
                        if th_text == "Yayımlanma Tarihi":
                            makale_data["makale_tarih"] = turkce_tarih_to_datetime(td_text)
                            break
            except:
                pass

            # DOI
            try:
                doi_div = detail_soup.find("div", id="article_tr").find("div", class_="article-doi data-section")
                if doi_div:
                    makale_data["makale_doi"] = doi_div.text.strip()
                else:
                    makale_data["makale_doi"] = ""
            except:
                makale_data["makale_doi"] = ""

            makale_listesi.append(makale_data)
        return makale_listesi
    except Exception as e:
        print("Scraping hata:", e)
        return []

def download_pdf(pdf_url: str, makale_isim: str, download_folder="pdfler"):
    if not pdf_url:
        return
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # Dosya adını temizle
    safe_filename = makale_isim.replace("/", "_").replace("\\", "_") + ".pdf"
    file_path = os.path.join(download_folder, safe_filename)

    if os.path.exists(file_path):
        print(f"{file_path} zaten mevcut.")
        return

    try:
        r = requests.get(pdf_url, timeout=10)
        with open(file_path, "wb") as f:
            f.write(r.content)
        print(f"PDF indirildi: {file_path}")
    except Exception as e:
        print("PDF indirme hatası:", e)
