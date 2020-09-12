import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import sys

args = sys.argv
# collection = args[1]
keyword = args[1]
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()
cities_ref = db.collection(u'iotech-kaikki')
docs = cities_ref.where(u'keywords', "array_contains", keyword).get()
print(type(docs))
print(docs)
for doc in docs:
    print(f'{doc.id} => {doc.to_dict()["url"]} ==> {doc.to_dict()["price"]}')