from bs4 import BeautifulSoup
import requests
import utils

# TODO:cleanup
def get_purse_breakdown(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise utils.ResponseErrorHTTP

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')

    pay_breakdown = {}

    for table in tables:
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            cell_data = [cell.get_text(strip=True) for cell in cells]
            try:
                pay_breakdown[int(cell_data[0])] = utils.dollars_to_int(cell_data[2])
            except ValueError:
                pass

    return pay_breakdown