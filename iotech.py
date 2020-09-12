#Preconditions:
# sudo apt-get install python3-lxml
# sudo apt-get install python3-bs4
# Nice tutorial: https://www.youtube.com/watch?v=GjKQ6V_ViQE

import bs4 as bs
import urllib.request
import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

sauce = urllib.request.urlopen("https://bbs.io-tech.fi/forums/myydaeaen.80/").read()

soup = bs.BeautifulSoup(sauce, "lxml")

# Use a service account
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


def parse_content(dict):
    """

    :param dict:
    :return:
    """
    value = dict["content"]
    list = value.find_all("a")
    if len(list) == 4:
        dict = {"status": "NULL", "topic": list[0].text, "url": "https://bbs.io-tech.fi{}".format(list[2]["href"]),
                "published": list[2].find_all("time")[0]["datetime"], "category": list[3].text}
    else:
        dict = {"status": list[0].text, "topic": list[1].text, "url": "https://bbs.io-tech.fi{}".format(list[3]["href"]),
                "published": list[3].find_all("time")[0]["datetime"], "category": list[4].text}
    return dict

def parse_answers(dict):
    """

    :param dict:
    :return:
    """
    value = dict["answers"]
    list = value.find_all("dd")
    dict = {"answers": list[0].text, "seen": list[1].text}
    return dict

def parse_timestamp(dict):
    """

    :param dict:
    :return:
    """
    value = dict["timestamp"]
    list = value.find_all("a")
    dict = {"last_activity": list[0].text}
    return dict

def parse(dict):
    """
    Function uses functions parse_content, parse_answers, parse_timestamp, get_information and create_keywords
    :param dict: Dictionary with keys content, timestamp and answers. Values are in html code.
    :return: Parsed dictionary with keys: status, topic, url, published, category, answers, product, price, location, delivery_method, receipt_found, purchase_day and other.
    """
    dict_content = parse_content(dict)
    dict_answers = parse_answers(dict)
    dict_timestamp = parse_timestamp(dict)
    combine_dict = {**dict_content, **dict_answers, **dict_timestamp}
    specific_information_dict = get_information(combine_dict["url"])
    result_dict = {**combine_dict, **specific_information_dict}
    with_keywords_dict = create_keywords(result_dict)
    return with_keywords_dict

def get_information(url):
    """

    :param url: Url of specific message.
    :return:
    """
    print(url)
    sauce2 = urllib.request.urlopen(url).read()
    soup2 = bs.BeautifulSoup(sauce2, "lxml")
    articles = soup2.find_all("article", class_="message-body js-selectToQuote")
    text_lines = articles[0].text
    temp_dict = {}
    str_dict = {"Myytävä tuote": "product", "Hinta": "price", "Paikkakunta": "location",
                "Toimitustapa": "delivery_method", "Kuitti löytyy": "receipt_found",
                "Tuote ostettu": "purchase_day", "Muuta huomioitavaa": "other"}
    for line in text_lines.split("\n"):
        for_dict = {}
        for key in str_dict:
            result = False
            if key in line and key not in for_dict:
                try:
                    temp_dict[str_dict[key]] = line.split(":")[1]
                    for_dict[key] = "DONE"
                except:
                    print(line)
                    print("Unexpected error: {}".format(sys.exc_info()[0]))
    return temp_dict

def create_keywords(dict):
    """
    Takes dictionary, and if there are keys for "topic" and "product", function will split those values by space and make them lower case.
    Also removes special charters from the keywords list.
    :param dict: Dictionary where keywords are sorted from.
    :return: Same dictionary as original, but also with "keywords" key and list of keywords as a value.
    """
    temp_list = []
    if "topic" in dict:
        topic = dict["topic"]
        keywords_topic = topic.split()
        for keyword in keywords_topic:
            word = "".join(e for e in keyword if e.isalnum())
            temp_list.append(word.lower())
    if "product" in dict:
        product = dict["product"]
        keywords_product = product.split()
        for keyword in keywords_product:
            word = "".join(e for e in keyword if e.isalnum())  #Removing other characters than numbers and letters.
            temp_list.append(word.lower())
    final_list = list(set(temp_list))  #Removing duplicates
    final_list = [i for i in final_list if i]  #Removing empty strings
    dict["keywords"] = final_list
    return dict


thread = soup.find_all("div", class_="structItem-cell structItem-cell--main")    #Storing div from https://bbs.io-tech.fi/forums/myydaeaen.80/ with information about url(= url to that message chain), status (=is it sold or in selling), topic, published (time of original message published) and category.
latest = soup.find_all("div", class_="structItem-cell structItem-cell--latest")  #Storing information about latest (latest message in that messagechain).
answers = soup.find_all("div", class_="structItem-cell structItem-cell--meta")   #Storing information about how many answers original message has gotten.
#example = soup.find_all("p", string=re.compile(("(S|s)ome")))  #Finding all paragraphs with word "Some" or "some"

list_of_dicts = []

#Going through each of lists (thread, latest and answers) and combining them to dictionary. Storing these dictionaries to list_of_dicts variable.
for item in thread:
    for l in latest:
        for a in answers:
            temp_dict = {}
            temp_dict["content"] = item
            temp_dict["timestamp"] = l
            temp_dict["answers"] = a
            answers.remove(a)
            list_of_dicts.append(temp_dict)
            break
        latest.remove(l)
        break

final_list = []

for dictionary in list_of_dicts:
    temp_dict = parse(dictionary)
    final_list.append(temp_dict)

for item in final_list:
    published = item["published"]
    doc_ref = db.collection("iotech-kaikki").document(published)
    doc_ref.set(item)
    print(item)

