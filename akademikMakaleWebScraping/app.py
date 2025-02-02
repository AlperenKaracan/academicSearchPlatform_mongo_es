from flask import Flask, render_template, request, redirect, url_for
from database import (
    collection,
    create_es_index,
    insert_to_mongo,
    bulk_index_to_es,
    search_in_es
)
from scraping import scrape_dergipark, download_pdf
from pymongo import ASCENDING, DESCENDING
from datetime import datetime

app = Flask(__name__)

create_es_index()

@app.route("/")
def index():
    all_docs = list(collection.find().sort("makale_ID", ASCENDING))
    return render_template("index.html", makale_datas=all_docs)

@app.route("/ara", methods=["POST"])
def ara():
    keyword = request.form.get("inputText", "").strip()
    if not keyword:
        return redirect(url_for("index"))

    results = scrape_dergipark(keyword, limit=10)
    for r in results:
        new_id = insert_to_mongo(r)
        r["makale_ID"] = new_id

    all_in_mongo = list(collection.find())
    bulk_index_to_es(all_in_mongo)

    return redirect(url_for("index"))

@app.route("/makale/<int:makale_id>")
def detay(makale_id):

    doc = collection.find_one({"makale_ID": makale_id})
    return render_template("detail.html", makale_data_JSON=doc)

@app.route("/indir/<int:makale_id>")
def indir_pdf(makale_id):

    doc = collection.find_one({"makale_ID": makale_id})
    if not doc:
        return redirect(url_for("index"))
    pdf_url = doc.get("PDF_URL", "")
    makale_isim = doc.get("makale_isim", f"makale_{makale_id}")
    download_pdf(pdf_url, makale_isim)
    return redirect(url_for("index"))

@app.route("/filtre", methods=["POST"])
def filtre():

    min_id = request.form.get("minNumber", "")
    max_id = request.form.get("maxNumber", "")
    min_alinti = request.form.get("minNumber2", "")
    max_alinti = request.form.get("maxNumber2", "")
    date1 = request.form.get("dateInput", "")
    date2 = request.form.get("dateInput2", "")

    sort_field = request.form.get("sortField", "makale_ID")
    sort_order = int(request.form.get("sortOrder", "1"))

    isim_filter = request.form.get("isimFilterInput", "")
    ozet_filter = request.form.get("ozetFilterInput", "")
    yazar_filter = request.form.get("yazarFilterInput", "")
    tur_filter = request.form.get("turFilterInput", "")
    anahtar_filter = request.form.get("anahtarKelimeInput", "")
    tarayici_filter = request.form.get("aramaKelimeInput", "")

    query = {}

    if min_id or max_id:
        query["makale_ID"] = {}
        if min_id:
            query["makale_ID"]["$gte"] = int(min_id)
        if max_id:
            query["makale_ID"]["$lte"] = int(max_id)

    if min_alinti or max_alinti:
        query["makale_alintisayisi"] = {}
        if min_alinti:
            query["makale_alintisayisi"]["$gte"] = int(min_alinti)
        if max_alinti:
            query["makale_alintisayisi"]["$lte"] = int(max_alinti)

    if date1 or date2:
        query["makale_tarih"] = {}
        if date1:
            query["makale_tarih"]["$gte"] = datetime.strptime(date1, "%Y-%m-%d")
        if date2:
            query["makale_tarih"]["$lte"] = datetime.strptime(date2, "%Y-%m-%d")

    if isim_filter:
        query["makale_isim"] = {"$regex": isim_filter, "$options": "i"}
    if ozet_filter:
        query["makale_ozet"] = {"$regex": ozet_filter, "$options": "i"}
    if yazar_filter:
        query["makale_yazar"] = {"$regex": yazar_filter, "$options": "i"}
    if tur_filter:
        query["makale_tur"] = {"$regex": tur_filter, "$options": "i"}
    if anahtar_filter:
        query["makale_anahtarkelimeler"] = {"$regex": anahtar_filter, "$options": "i"}
    if tarayici_filter:
        query["makale_anahtarkelimeler_tarayici"] = {"$regex": tarayici_filter, "$options": "i"}

    direction = ASCENDING if sort_order == 1 else DESCENDING
    results = list(collection.find(query).sort(sort_field, direction))

    filter_form_data = {
        "minNumber": min_id,
        "maxNumber": max_id,
        "minNumber2": min_alinti,
        "maxNumber2": max_alinti,
        "dateInput": date1,
        "dateInput2": date2,
        "isimFilterInput": isim_filter,
        "ozetFilterInput": ozet_filter,
        "yazarFilterInput": yazar_filter,
        "turFilterInput": tur_filter,
        "anahtarKelimeInput": anahtar_filter,
        "aramaKelimeInput": tarayici_filter,
        "sortField": sort_field,
        "sortOrder": str(sort_order),
    }

    return render_template("index.html",
                           makale_datas=results,
                           filter_form_data=filter_form_data,
                           es_form_data={})

@app.route("/es_arama", methods=["POST"])
def es_arama():

    query_str = request.form.get("esKeyword", "").strip()
    if not query_str:
        return redirect(url_for("index"))

    es_results = search_in_es(query_str)
    es_form_data = {
        "esKeyword": query_str
    }

    return render_template("index.html",
                           makale_datas=es_results,
                           es_form_data=es_form_data,
                           filter_form_data={})
from datetime import datetime

@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

if __name__ == "__main__":
    app.run(debug=True)
