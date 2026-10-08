from __future__ import annotations
import json, re, time
from dataclasses import dataclass, asdict
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

@dataclass
class Result:
    pn: str; ean: str; nazwa: str; zrodlo: str; typ: str
    cena: float | None; waluta: str; dostepnosc: str; url: str
    status: str; komunikat: str = ""
    def dict(self): return asdict(self)

def normalize_price(value):
    if value is None: return None
    s = str(value).replace("\xa0", " ").replace("PLN", "").replace("zł", "")
    s = re.sub(r"[^0-9,.-]", "", s).replace(",", ".")
    try: return round(float(s), 2)
    except Exception: return None

def jsonld_products(soup):
    out=[]
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data=json.loads(tag.get_text(strip=True))
            stack=data if isinstance(data,list) else [data]
            for obj in stack:
                if isinstance(obj,dict) and '@graph' in obj: stack.extend(obj['@graph'])
                if isinstance(obj,dict) and obj.get('@type') in ('Product','IndividualProduct'):
                    out.append(obj)
        except Exception: pass
    return out

def generic_search(source, kind, search_url, pn, ean, name):
    queries=[]
    for value in (ean, pn, name):
        value=str(value or '').strip()
        if value and value not in queries: queries.append(value)
    last=None
    for query in queries:
        url=search_url.format(q=quote_plus(query))
        try:
            r=requests.get(url,headers=HEADERS,timeout=20)
            if r.status_code in (403,429):
                last=Result(pn,ean,name,source,kind,None,'PLN','nieznana',url,'zablokowano',f'HTTP {r.status_code}')
                continue
            r.raise_for_status()
            soup=BeautifulSoup(r.text,'lxml')
            for product in jsonld_products(soup):
                offers=product.get('offers') or {}
                if isinstance(offers,list): offers=offers[0] if offers else {}
                price=normalize_price(offers.get('price') or offers.get('lowPrice'))
                if price:
                    product_url=product.get('url') or offers.get('url') or url
                    avail=str(offers.get('availability','')).split('/')[-1] or 'nieznana'
                    return Result(pn,ean,name,source,kind,price,'PLN',avail,product_url,'ok',f'Znaleziono po: {query}')
            text=soup.get_text(' ',strip=True)
            prices=re.findall(r'(\d{1,5}(?:[\s.]\d{3})*[,.]\d{2})\s*(?:zł|PLN)',text,re.I)
            vals=[normalize_price(x) for x in prices]; vals=[x for x in vals if x and 1 <= x <= 100000]
            if vals: return Result(pn,ean,name,source,kind,min(vals),'PLN','nieznana',url,'ok',f'Cena z wyników; znaleziono po: {query}')
            last=Result(pn,ean,name,source,kind,None,'PLN','nieznana',url,'brak',f'Brak wyniku dla: {query}')
        except Exception as exc:
            last=Result(pn,ean,name,source,kind,None,'PLN','nieznana',url,'blad',str(exc)[:180])
    return last or Result(pn,ean,name,source,kind,None,'PLN','nieznana','','brak','Brak identyfikatora produktu')
