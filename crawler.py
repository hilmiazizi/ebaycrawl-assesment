from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs
import json
import argparse
import aiohttp
import asyncio
from dataclasses import dataclass
import aiofiles
import os


@dataclass
class Response:
    url: str
    text: str

class Curl:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self._set_header()

    async def close(self):
        await self.session.close()

    def _set_header(self, header=None):
        default_headers = {
            'Host': 'www.ebay.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.7,en;q=0.3',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }
        if header:
            self.session.headers.update(header)
        else:
            self.session.headers.update(default_headers)

    async def _get(self, target, params=None):
        try:
            async with self.session.get(target, params=params, timeout=5) as response:
                text = await response.text()
                return Response(url=str(response.url), text=text)
        except aiohttp.ClientError as e:
            print(f"Error fetching {target}: {e}")
            return None
        except asyncio.TimeoutError:
            print(f"Timeout fetching {target}")
            return None

    async def _post(self, target, data=None):
        try:
            async with self.session.post(target, data=data, timeout=5) as response:
                text = await response.text()
                return Response(url=str(response.url), text=text)
        except aiohttp.ClientError as e:
            print(f"Error posting to {target}: {e}")
            return None
        except asyncio.TimeoutError:
            print(f"Timeout posting to {target}")
            return None
    
    async def close(self):
        await self.session.close()

class Crawler:
    def __init__(self, url):
        self.curl = Curl()
        self.url = url
    
    async def _start(self):
        response = await self.curl._get(self.url)
        self.first_response,ssn = await self._to_usd(response.url)
        self.conditions = await self._get_condition(ssn, self.first_response.url)

    async def Scrape(self, url, condition):
        if self.first_response:
            response = self.first_response
            soup = BeautifulSoup(self.first_response.text, 'html.parser')
            self.first_response = None
        else:
            response = await self.curl._get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
        next_page = soup.find('a', class_='pagination__next')
        if next_page:
            next_page = next_page['href']

        content = soup.find("div", id="srp-river-results")
        if content:
            items = content.find_all('li', class_=re.compile(r"\bs-item\b"))

            if items:
                for item in items:
                    product_link = item.find('a')
                    product_link = product_link['href'] if product_link else None
                    product_name = item.find('span', role="heading")
                    product_name = product_name.text if product_name else None
                    raw_price = item.find('span', class_="s-item__price")
                    raw_price = raw_price.text if raw_price else None
                    product_price  = re.sub(r'[^\d.]', '', raw_price)
                    
                    pattern = r"itm/(\d+)"
                    match = re.search(pattern, product_link)
                    if match:
                        itemid = match.group(1)
                        result = {
                            'title': product_name,
                            'condition': condition,
                            'price': product_price,
                            'product_link': product_link
                        }
                        await self._write_to_file(result, itemid)

                print(f"Scraped --> {response.url}")
            else:
                print(f"Failed to extract items on --> {response.url}")

        else:
            print(f'Failed to extract -> {response.url}')
        
        if next_page:
            await self.Scrape(next_page, condition)
               
    async def _write_to_file(self, result, itemid):
        async with aiofiles.open(f'./result/{itemid}.json', mode='w') as f:
            await f.write(json.dumps(result, indent=4))
            
    async def _to_usd(self, current_url):
        param = parse_qs(urlparse(current_url).query)
        ssn = param['_ssn'][0]
        
        response = await self.curl._get('https://www.ebay.com/sch/ajax/customize?_ssn='+ssn)
        if response:
            result = json.loads(response.text)
            if result['success']:
                token = result['token']
            else:
                return False

        data = [
            ('_fcdm', '1'),
            ('_fcss', '12'),
            ('_fcippl', '2'),
            ('_fctab', '0'),
            ('_fcpe', '7'),
            ('_fcpe', '5'),
            ('_fcse', '1'),
            ('_fcpe', '3'),
            ('_fcsp', current_url),
            ('action', 'apply'),
            ('srt', token),
        ]

        response = await self.curl._post('https://www.ebay.com/sch/customize', data)
        return response,ssn

    async def _get_condition(self, ssn, url):
        params = {
            'no_encode_refine_params': '1',
            '_fsrp': '1',
            '_ssn': ssn,
            '_aspectname': 'condition',
        }

        response = await self.curl._get('https://www.ebay.com/sch/ajax/refine', params=params)
        result = json.loads(response.text)['group']
        condition_temp = [x for x in result if x['fieldId'] == "condition"][0]['entries']
        conditions = []
        for line in condition_temp:
            conditions.append({
                "name": line['label']['textSpans'][0]['text'],
                "base_url": f'{url}&LH_ItemCondition={line["paramValue"]}'
            })
        return conditions

async def main():
    crawler = Crawler('https://www.ebay.com/sch/garlandcomputer/m.html')
    await crawler._start()
    await crawler.curl.close()

    if args.set_cond:
        chosen_condition_name = args.set_cond
        selected_url = None
        for condition in crawler.conditions:
            if condition["name"].lower() == chosen_condition_name.lower():
                selected_url = condition["base_url"]
                selected_condition = condition["name"]

                crawler = Crawler('https://www.ebay.com/sch/garlandcomputer/m.html')
                await crawler._start()
                await crawler.Scrape(selected_url, selected_condition)
                await crawler.curl.close()
                break

        else:
            print(f"Error: Condition '{chosen_condition_name}' not found.")
            print("Available Conditions:")
            for condition in crawler.conditions:
                print(f"- {condition['name']}")
            exit()
    else:
        await crawler.curl.close()
        for line in crawler.conditions:
            crawler = Crawler(line['base_url'])
            await crawler._start()
            await crawler.Scrape(line['base_url'], line['name'])
            await crawler.curl.close()

    
parser = argparse.ArgumentParser(description="eBay Crawler", add_help=True)
parser.add_argument("--set-cond", help="Set condition to scrape ")
args = parser.parse_args()

if __name__ == "__main__":
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    if not os.path.exists('./result'):
        os.makedirs('./result')
    asyncio.run(main())
