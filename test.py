import bs4 as bs
import urllib.request
import sys

sauce = urllib.request.urlopen("https://bbs.io-tech.fi/forums/myydaeaen.80/").read()

soup = bs.BeautifulSoup(sauce, "lxml")

thread = soup.find_all("div", class_="structItem-cell structItem-cell--main")
latest = soup.find_all("div", class_="structItem-cell structItem-cell--latest")
answers = soup.find_all("div", class_="structItem-cell structItem-cell--meta")

list = []
for item in thread:
    for l in latest:
        for a in answers:
            temp_dict = {}
            temp_dict["content"] = item
            temp_dict["timestamp"] = l
            temp_dict["answers"] = a
            answers.remove(a)
            list.append(temp_dict)
            break
        latest.remove(l)
        break


def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def parse_content(dict):
    value = dict["content"]
    list = value.find_all("a")
    # for href in list:
    #     print(href)
    # print("---------------------------")
    if len(list) == 4:
        dict = {"status": "NULL", "topic": list[0].text, "url": list[2]["href"],
                "published": list[2].find_all("time")[0]["datetime"], "category": list[3].text}
    else:
        dict = {"status": list[0].text, "topic": list[1].text, "url": list[3]["href"],
                "published": list[3].find_all("time")[0]["datetime"], "category": list[4].text}

    return dict


def parse_answers(dict):
    value = dict["answers"]
    list = value.find_all("dd")
    dict = {"answers": list[0].text, "seen": list[1].text}
    return dict


def parse_timestamp(dict):
    value = dict["timestamp"]
    list = value.find_all("a")
    dict = {"last_activity": list[0].text}
    return dict


def parse(dict):
    dict_content = parse_content(dict)
    dict_answers = parse_answers(dict)
    dict_timestamp = parse_timestamp(dict)
    result_dict = {**dict_content, **dict_answers, **dict_timestamp}
    spesific_infomation_dict = get_information(result_dict)
    new_result_dict = {**result_dict, **spesific_infomation_dict}
    return new_result_dict


def get_information(dict):
    url = "https://bbs.io-tech.fi{}".format(dict["url"])
    print(url)
    sauce = urllib.request.urlopen(url).read()
    soup = bs.BeautifulSoup(sauce, "lxml")
    articles = soup.find_all("article", class_="message-body js-selectToQuote")
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
# if "Myytävä tuote" in line:
#     try:
#         temp_dict["product"] = line.split(":")[1]
#     except:
#         print("Unexpected error: {}".format(sys.exc_info()[0]))
#     continue
# if "Hinta" in line:
#     print(line)
#     temp_dict["price"] = line.split(":")[1]
# if "Paikkakunta" in line:
#     try:
#         temp_dict["location"] = line.split(":")[1]
#     except:
#         print("Unexpected error: {}".format(sys.exc_info()[0]))
# if "Toimitustapa" in line:
#     temp_dict["delivery_method"] = line.split(":")[1]
# if "Kuitti löytyy" in line:
#     temp_dict["receipt_found"] = line.split(":")[1]
# if "Tuote ostettu" in line:
#     temp_dict["purchase_day"] = line.split(":")[1]
# if "Muuta huomioitavaa" in line:
#     temp_dict["other"] = line.split(":")[1]
#     return temp_dict

final = parse(list[0])

final_list = []
for dict in list:
    temp_dict = parse(dict)
    final_list.append(temp_dict)

for item in final_list:
    print(item)

# get_information(final_list[0])