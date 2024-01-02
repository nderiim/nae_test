import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    url = "https://ipfabric.io/"
    new_urls = []

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")


    link_elements = soup.select("a[href]")

    for link_element in link_elements:
        url = link_element["href"]
        
        if "https://ipfabric.io/" in url:

            if 'about-us/' in url.lower():
                response = requests.get(url)
                soup = BeautifulSoup(response.content, "html.parser")

                element = soup.findAll('h2')

                for i, link_element in enumerate(element):
                    print(f'{i + 1}. {link_element.string}')
                
                choosen_element_index = int(input('\nChoose: '))
                choosen_element = element[choosen_element_index - 1]
                next_element = choosen_element.find_next_sibling()
                
                if choosen_element_index and next_element:
                    print(choosen_element.text + ':')
                    print(next_element.text)

                break