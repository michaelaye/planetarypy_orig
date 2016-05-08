
# coding: utf-8

# In[ ]:

url = "https://nspires.nasaprs.com/external/viewrepositorydocument/cmdocumentid=492458/solicitationId=%7B68C12087-132D-3814-9A87-5323BCE6CAB6%7D/viewSolicitationDocument=1/Table%202%202016_amend8_clarify.html"


# In[ ]:

import requests


# In[ ]:

from bs4 import BeautifulSoup


# In[ ]:

r = requests.get(url)


# In[ ]:

soup = BeautifulSoup(r.text, 'lxml')


# In[ ]:

table = soup.find('table')


# In[ ]:

rows = table.find_all('tr')


# In[ ]:

def parse_header(row):
    headers = [i.get_text() for i in row.find_all('th')]
    headers = [i.strip() for i in headers]
    return [header.splitlines()[0].strip() for header in headers]


# In[ ]:

columns = parse_header(rows[0])


# In[ ]:

def parse_table(rows):
    cell_data = []
    for row in rows:
        cells = [cell.get_text().strip() for cell in row.find_all('td')]
        cell_data.append(cells)
    return cell_data


# In[ ]:

df = pd.DataFrame(parse_table(rows[1:]), columns=columns)


# In[ ]:

df.head()


# In[ ]:



