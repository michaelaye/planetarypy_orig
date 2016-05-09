
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
columns.append('url')


# In[ ]:

def parse_out_url(row):
    cells = row.find_all('td')
    cell = cells[1]
    a = cell.find('a')
    a['href'] = a['href'].strip().replace('http','https')
    return a

def parse_table(rows):
    cell_data = []
    for row in rows:
        cells = [cell.get_text().strip() for cell in row.find_all('td')]
        if len(cells) == 3:
            cells.append('None')
        cells.append(parse_out_url(row))
        cell_data.append(cells)
    return cell_data


# In[ ]:

df = pd.DataFrame(parse_table(rows[1:]), columns=columns)


# In[ ]:

from IPython.display import HTML


# In[ ]:

pd.set_option('display.max_colwidth', 1000)


# In[ ]:

HTML(df.to_html(escape=False))


# In[ ]:

def parse_date_cell(cell):
    try:
        tokens = cell.split('(')
    except AttributeError:
        return cell, False
    date = tokens[0]
    step = True if len(tokens)==2 else False        
    if date == 'N/A':
        d = pd.NaT
    elif date[0].isdigit():
        t = pd.to_datetime(str(date))
        d = t.date()
    else:
        d = date
    return d, step
    
def parse_date_columns(row):
    cell = row['NOI/Step-1']
    date1, step1 = parse_date_cell(cell)
    cell = row['PROPOSAL']
    date2, step2 = parse_date_cell(cell)
    if step1!=step2:
        raise ValueError('steps not the same')
    return pd.Series([date1, step1, date2], index=['date1', 'step', 'date2'])


# In[ ]:

df = pd.concat([df, df.apply(parse_date_columns, axis=1)], axis=1)


# In[ ]:

from icalendar import Calendar, Event


# In[ ]:

cal = Calendar()

cal.add('prodid', '-//NASA ROSES deadline calendar//mxm.dk//')
cal.add('version', '2.0')
cal.add('name', 'NASA ROSES Deadlines')
cal.add('x-wr-calname', 'NASA ROSES Deadlines')
cal.add('x-wr-caldesc', 'NASA ROSES Deadlines for 2016')


# In[ ]:

def create_cal_events_from_row(row, i):
    events = []
    for j,col in enumerate(['date1', 'date2']):
        date = row[col]

        event = Event()
        event.add('dtstart', date)

        descr = 'APPENDIX '
        descr += row['APPENDIX'] + '\n'
        event.add('description', descr)

        sumtext = 'ROSES D/L '
        if row['step']:
            if col == 'date1':
                sumtext += 'Step_1 '
            else:
                sumtext += 'Step_2 '
        else:
            if col == 'date':
                sumtext += 'NOI '
            else:
                sumtext += 'Final '

        event.add('summary', sumtext + row['PROGRAM'])
        s = row['url'].get('href')
        event.add('location', s)
        s = s.replace('&', '%26')
        s = s.replace('?', '%3F')
        s = s.replace('{', '%7B')
        s = s.replace('}', '%7D')
        event.add('url', s)
        uid = 'nasa_roses_deadlines_2016_'+str(i)+str(j)
        event.add('uid', uid)
        events.append(event)
    return events


# In[ ]:

import datetime
for i, row in df.iterrows():
    date = row['date1']
    if type(date) == datetime.date:
        for event in create_cal_events_from_row(row, i):
            cal.add_component(event)


# In[ ]:

import os

with open(os.path.join(os.environ['HOME'], 'NASA_ROSES_deadlines.ics'), 'wb') as f:
    f.write(cal.to_ical())

get_ipython().system('open {f.name}')

