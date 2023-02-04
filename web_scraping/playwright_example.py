#!/usr/bin/env python3

from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
import requests
import datefinder
import pandas as pd

def get_search_results(start="17/12/22",end="18/12/22"):
    """Fetch rip search table"""
    res = []
    html = 'test'
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,slow_mo=50)
        page = browser.new_page()
        page.goto('https://rip.ie/Deathnotices/All')
        # Fill in the dates
        page.fill("input#DateFrom", start)
        page.fill("input#DateTo", end)

        for i in range(1):
            #wait to load table
            page.wait_for_timeout(1000)
            # Extract the HTML of the results
            html = page.inner_html("#deathnotice_page_table")
            res.append(html)
            #get next page in table
            page.locator('"Next"').click()

        # Close the browser
        browser.close()
    return res

rows = get_search_results()

pref = 'https://rip.ie'
links = []
for html in rows:
    # Use Scrapy to parse the HTML and extract the data you are interested in
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('a',class_="showdn-link")
    for a in rows:
        #print (a['href'])
        links.append(pref+a['href'])

print (links)
results={}
for url in links[:2]:
    print (url)
    name,date,cty,addr,txt = get_dn_page(url)
    if name == '':
        continue
    results[n] = [name,date,cty,addr,txt]
    time.sleep(0.05)

res = pd.DataFrame.from_dict(results,orient='index',columns=['name','date','county','address','notice']).reset_index()
res = res.rename(columns={'index':'id'})

print (res)
