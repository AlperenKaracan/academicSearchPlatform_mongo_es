import os
import atexit
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "akademikMakale")
MONGO_COLLECTION_NAME = os.environ.get("MONGO_COLLECTION_NAME", "makale_database")

ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
ES_INDEX_NAME = os.environ.get("ES_INDEX_NAME", "academic_publications")

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
collection = mongo_db[MONGO_COLLECTION_NAME]

es_client = Elasticsearch(ES_HOST)

def create_es_index(index_name=ES_INDEX_NAME):
    if not es_client.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "makale_ID": {"type": "integer"},
                    "makale_isim": {"type": "text"},
                    "makale_yazar": {"type": "text"},
                    "makale_tur": {"type": "text"},
                    "makale_tarih": {"type": "date"},
                    "makale_ozet": {"type": "text"},
                    "makale_alintisayisi": {"type": "integer"},
                    "makale_anahtarkelimeler": {"type": "text"},
                    "makale_anahtarkelimeler_tarayici": {"type": "text"}
                }
            }
        }
        es_client.indices.create(index=index_name, mappings=mapping["mappings"])
        print(f"Elasticsearch index '{index_name}' oluşturuldu.")
    else:
        print(f"Index '{index_name}' zaten mevcut.")

def insert_to_mongo(data: dict) -> int:
    existing = collection.find_one({"PDF_URL": data.get("PDF_URL")})
    if existing:
        makale_id = existing["makale_ID"]
        collection.update_one(
            {"_id": existing["_id"]},
            {"$set": data}
        )
        print(f"Mevcut makale_ID {makale_id} güncellendi.")
        return makale_id
    else:
        new_id = 0
        while True:
            if collection.find_one({"makale_ID": new_id}) is None:
                data["makale_ID"] = new_id
                break
            new_id += 1

        collection.insert_one(data)
        print(f"Yeni makale_ID {new_id} ile eklendi.")
        return new_id

def index_to_es(doc: dict, index_name=ES_INDEX_NAME):
    doc_to_index = {k: v for k, v in doc.items() if k != '_id'}

    es_client.index(index=index_name, id=doc["makale_ID"], document=doc_to_index)
    print(f"Makale_ID {doc['makale_ID']} Elasticsearch'e indekslendi.")

def bulk_index_to_es(docs: list, index_name=ES_INDEX_NAME):
    actions = []
    for d in docs:
        doc_to_index = {k: v for k, v in d.items() if k != '_id'}
        action = {
            "_index": index_name,
            "_id": d["makale_ID"],
            "_source": doc_to_index
        }
        actions.append(action)
    if actions:
        helpers.bulk(es_client, actions)
        print(f"{len(actions)} doküman Elasticsearch'e indekslendi.")

def search_in_mongo(query: dict, sort_field=None, sort_order=1):
    cursor = collection.find(query)
    if sort_field:
        cursor = cursor.sort(sort_field, sort_order)
    results = list(cursor)
    print(f"MongoDB'den {len(results)} sonuç bulundu.")
    return results

def search_in_es(query_str: str, index_name=ES_INDEX_NAME, size=20):
    body = {
        "query": {
            "multi_match": {
                "query": query_str,
                "fields": [
                    "makale_isim^2",
                    "makale_ozet",
                    "makale_yazar",
                    "makale_anahtarkelimeler"
                ],
                "fuzziness": "AUTO"
            }
        }
    }
    res = es_client.search(index=index_name, query=body["query"], size=size)
    hits = res["hits"]["hits"]
    results = [hit["_source"] for hit in hits]
    print(f"Elasticsearch'den {len(results)} sonuç bulundu.")
    return results

def close_connections():
    if mongo_client:
        mongo_client.close()
        print("MongoDB bağlantısı kapatıldı.")
    if es_client:
        es_client.close()
        print("Elasticsearch bağlantısı kapatıldı.")

atexit.register(close_connections)
