#!/usr/bin/env python3
"""Mirror the current public takkensokuto.com static site into this repo.

This preserves the deployed Cloudflare Pages output as source-controlled static files.
Run from repo root: python3 scripts/mirror_live_site.py
"""
from __future__ import annotations
import os, re, time, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

HOST = "takkensokuto.com"
BASE = f"https://{HOST}"
UA = "Mozilla/5.0 Hermes static mirror (+https://takkensokuto.com)"
ROOT = Path(__file__).resolve().parents[1]
SKIP_PREFIXES = ("/cdn-cgi/",)
EXTERNAL_HOSTS_SKIP = {"static.cloudflareinsights.com"}

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        for key in ("href","src","poster"):
            if key in attrs:
                self.links.append(attrs[key])
        srcset=attrs.get("srcset")
        if srcset:
            for part in srcset.split(','):
                u=part.strip().split(' ')[0]
                if u: self.links.append(u)

def fetch(url: str) -> bytes:
    req=Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    with urlopen(req, timeout=30) as r:
        return r.read()

def local_path_for(url: str) -> Path | None:
    url,_=urldefrag(url)
    p=urlparse(url)
    if p.scheme and p.netloc and p.netloc != HOST:
        return None
    path=p.path or "/"
    if any(path.startswith(x) for x in SKIP_PREFIXES):
        return None
    if path.endswith('/'):
        return ROOT / path.lstrip('/') / 'index.html'
    if not Path(path).suffix and path != '/robots.txt':
        return ROOT / path.lstrip('/') / 'index.html'
    return ROOT / path.lstrip('/')

def save(url: str) -> tuple[Path|None, bytes|None]:
    lp=local_path_for(url)
    if lp is None: return None, None
    if lp.exists() and lp.stat().st_size > 0: return lp, None
    full=urljoin(BASE+'/', url)
    try:
        data=fetch(full)
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"WARN fetch failed {full}: {e}", file=sys.stderr)
        return lp, None
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_bytes(data)
    print(f"saved {lp.relative_to(ROOT)} {len(data)}")
    return lp, data

def main():
    # Fetch sitemap URL list plus core files.
    sitemap=fetch(BASE+'/sitemap.xml')
    (ROOT/'sitemap.xml').write_bytes(sitemap)
    (ROOT/'robots.txt').write_bytes(fetch(BASE+'/robots.txt'))
    urls=[BASE+'/', BASE+'/robots.txt', BASE+'/sitemap.xml', BASE+'/favicon.svg', BASE+'/site.webmanifest']
    locs=re.findall(rb'<loc>(.*?)</loc>', sitemap)
    for loc in locs:
        urls.append(loc.decode())
    seen=set()
    for url in urls:
        if url in seen: continue
        seen.add(url)
        lp,data=save(url)
        # Parse same-host assets from HTML as we go.
        if lp and lp.suffix.lower() in {'.html','.htm'}:
            html=(data if data is not None else lp.read_bytes()).decode('utf-8','ignore')
            parser=LinkParser(); parser.feed(html)
            for link in parser.links:
                if not link or link.startswith(('#','mailto:','tel:','javascript:')): continue
                full,_=urldefrag(urljoin(url, link))
                p=urlparse(full)
                if p.netloc in EXTERNAL_HOSTS_SKIP: continue
                if p.netloc and p.netloc != HOST: continue
                save(full)
    print(f"Mirrored {len(seen)} sitemap/core URLs into {ROOT}")
if __name__ == '__main__':
    main()
