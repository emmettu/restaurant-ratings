from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from unicodedata import normalize
import requests
import re


def get_google_page(query):
    url = "http://www.google.com/search?q={}&amp;ie=utf-8&as_qdr=all&amp;aq=t&amp;rls=org:mozilla:us:official&amp;client=firefox&num=30".format(quote_plus(query))
    response = requests.get(url)
    content = response.text
    return content


def parse_ratings(content):
    soup = BeautifulSoup(content, "html.parser")
    results = soup.find_all("div", {"class": "g"})
    google_result = get_google_rating(soup)
    return [get_rating(result) for result in results if has_rating(result)]\
        +  google_result


def get_google_rating(soup):
    rating = soup.find("span", {"class": "_kgd"})

    if not rating:
        return []

    votes = soup.find("span", {"style": "color:#777"}).get_text()
    votes = votes.split(" ")[1]
    return [(rating.get_text(), votes, "google")]

def get_rating(result):
    rating_text = result.find("div", {"class": "f slp"}).get_text()
    rating_text = normalize("NFKD", rating_text)
    rating, votes = parse_rating_text(rating_text)
    source = result.cite.get_text()
    source = re.sub("http(s)?://", "", source).replace("www.", "").split(".")[0]
    return (rating, votes, source)


def parse_rating_text(text):
    rating, votes = text\
        .strip(" ")\
        .replace("Rating: ", "")\
        .replace(",", "")\
        .split(" - ")[0:2]

    votes = re.sub(r"( vote| review|Review)(s)?.*", "", votes)
    votes = "1" if votes == "" else votes

    return rating, votes


def has_rating(result):
    rating = len(result.find_all("div", {"class": "star"})) > 0
    source = result.cite
    return rating and source


def filter_ratings(rating_list):
    return {domain: (rating, votes) for rating, votes, domain in rating_list}


def get_average(ratings):
    total_votes = 0
    score_sum = 0

    for (r, v) in ratings.values():
        vote_number = int(v)
        total_votes += vote_number
        rating_number = get_rating_number(r)
        score_sum += vote_number * rating_number

    return (score_sum / total_votes) * 100

def get_rating_number(rating):
    num, den = rating.split("/") if "/" in rating else (rating, 5)
    return float(num) / float(den)


if __name__ == '__main__':
    content = get_google_page("Chipotle Toronto")
    # content = open("test.html", "r").read()
    rating_list = parse_ratings(content)
    rating_list = filter_ratings(rating_list)
    print(rating_list)
    average = get_average(rating_list)
    print("{:.0f}%".format(round(average)))
