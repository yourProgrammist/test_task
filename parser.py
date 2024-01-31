import csv
import requests
from bs4 import BeautifulSoup


MAIN_URL = "https://ru.wiktionary.org/wiki/Индекс:Русский_язык"
FILENAME_1 = "words.csv"
FILENAME_2 = "sentences.csv"


def remove_accent(word):
    """
    Remove accent from word
    :param word: str
    :return: str
    """
    return word.replace('́', '')


def csv_writer(writer, array):
    """
    Write line in csv file
    :param writer: DictWriter[str]
    :param array: list[dict]
    :return: None
    """
    if array:
        writer.writerows(array)


def parser_sentences(soup, url):
    """
    Parsing usage examples from https://ru.wiktionary.org/
    :param soup: BeautifulSoup
    :param url: str
    :return: None
    """
    NON_BREAKING_SPACE = chr(160)  # NBSP
    sentences = []
    headline_tags = soup.find_all('h1')
    if len(headline_tags) > 2:
        second_headline = headline_tags[1]
        third_headline = headline_tags[2]
        example_blocks = []
        found_third_headline = False
        for descendant in second_headline.find_parent().descendants:
            if descendant == third_headline:
                found_third_headline = True
                break
            if descendant.name == 'span' and 'example-block' in descendant.get('class', [
            ]):
                example_blocks.append(descendant)
        if found_third_headline:
            for example in example_blocks:
                if example.get_text().strip() != "Отсутствует пример употребления (см. рекомендации).":
                    sentences.append({"Предложение": example.get_text().strip().replace(
                        NON_BREAKING_SPACE, ' ')})
    else:
        row_data = soup.find_all('span', class_="example-block")
        for i in row_data:
            if i.get_text().strip() != "Отсутствует пример употребления (см. рекомендации).":
                sentences.append({"Предложение": i.get_text().strip().replace(
                    NON_BREAKING_SPACE, ' ')})
    csv_writer(writer_2, sentences)


def parser_words(
        table1,
        main_word,
        url):
    """
    Parsing all forms of the word from https://ru.wiktionary.org/
    :param table1: BeautifulSoup
    :param main_word: str
    :param url: str
    :return: array [{"Слово": word, "Ссылка": url}, ...}
    """
    data = []
    words = set()
    headers = []
    if not table1:
        return data
    for i in table1.find_all('th'):
        title = i.text
        headers.append(title)
    for j in table1.find_all('tr')[1:]:
        row_data = j.find_all('td')
        for td in row_data[1:]:
            text = td.get_text(separator=" ", strip=True)
            for word in text.split():
                if word != '—' and word != 'одуш.' and word != 'неод.' and word != ',' and word != 'буду/будешь…' and word != '*':
                    words.add(remove_accent(word))

    words.add(remove_accent(main_word))
    for i in words:
        data.append({"Слово": i, "Ссылка": url})
    return data


def parser(
        main_word,
        writer_1,
        writer_2):
    """
    Parsing usage examples and words from https://ru.wiktionary.org/
    :param main_word: str
    :param writer_1: DictWrite
    :param writer_2: DictWrite
    :return: None
    """
    url = 'https://ru.wiktionary.org/wiki/' + main_word
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    table1 = soup.find('table', class_="morfotable ru")
    words = parser_words(table1, main_word, url)
    csv_writer(writer_1, words)
    sentences = parser_sentences(soup, url)
    csv_writer(writer_2, sentences)


def find(url, writer_1, writer_2):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    table1 = soup.find('div', class_="index")
    if table1:
        status = table1.find_all('li')
    else:
        table1 = soup.find('div', class_="mw-content-ltr mw-parser-output")
        status = table1.find_all('li')
    for j in status:
        parser(j.select("a")[0].get_text(), writer_1, writer_2)


if __name__ == "__main__":
    file_1 = open(FILENAME_1, mode='w', newline='', encoding='utf-8')
    file_2 = open(FILENAME_2, mode='w', newline='', encoding='utf-8')
    writer_1 = csv.DictWriter(file_1, fieldnames=["Слово", "Ссылка"])
    writer_1.writeheader()
    writer_2 = csv.DictWriter(file_2, fieldnames=["Предложение"])
    writer_2.writeheader()
    page = requests.get(MAIN_URL)
    soup = BeautifulSoup(page.text, 'lxml')
    table1 = soup.find('div', align="center")
    for j in table1.find_next('p').find_all('a')[1:]:
        if j.get_text() not in ['Ь', 'Ъ']:
            l_url = "https://ru.wiktionary.org" + j.get('href')
            page = requests.get(l_url)
            soup = BeautifulSoup(page.text, 'lxml')
            table1 = soup.find('div', class_="mw-content-ltr mw-parser-output")

            for k in table1.find_all('p'):
                if k.find_parent('table') is None:
                    url = "https://ru.wiktionary.org" + \
                        k.find_next('a').get('href')
                    find(url, writer_1, writer_2)
            find(l_url, writer_1, writer_2)
    file_1.close()
    file_2.close()
