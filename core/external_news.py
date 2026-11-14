"""Server-side adapters for permitted headline metadata from news providers."""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.utils.dateparse import parse_datetime


class NewsProviderError(Exception):
    pass


def canonical_url(url: str) -> str:
    """Remove tracking params so a publisher URL remains a stable target."""
    parsed = urlparse(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query) if not key.lower().startswith(('utm_', 'fbclid', 'gclid'))]
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip('/'), '', urlencode(query), ''))


def external_id(url: str) -> str:
    return f'ext_{hashlib.sha256(canonical_url(url).encode()).hexdigest()[:40]}'


def _request_json(url: str, headers: dict[str, str] | None = None, timeout: float = 4) -> dict:
    request = Request(url, headers={'User-Agent': 'TheGlobalChronicle/1.0', **(headers or {})})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise NewsProviderError(str(exc)) from exc


def _as_datetime(value):
    return parse_datetime(value) if value else None


def _normalise(provider: str, item: dict, category: str) -> dict | None:
    url = item.get('url')
    title = (item.get('title') or '').strip()
    if not url or not title or title == '[Removed]':
        return None
    normal_url = canonical_url(url)
    source = item.get('source') or {}
    source_name = source.get('name') if isinstance(source, dict) else str(source)
    description = (item.get('description') or '').strip()[:1000]
    return {
        'id': external_id(normal_url),
        'external_id': external_id(normal_url),
        'kind': 'external',
        'provider': provider,
        'source': {'id': source.get('id') if isinstance(source, dict) else provider, 'name': source_name or provider.title()},
        'title': title[:500],
        'description': description,
        # Never treat provider snippets as canonical full text.
        'content': description,
        'url': normal_url,
        'urlToImage': item.get('urlToImage') or item.get('image') or '',
        'publishedAt': item.get('publishedAt') or '',
        'category': category or 'general',
        'tag': f'{provider.upper()} • External',
        'readTime': 'External link',
    }


def _from_newsapi(query: str, category: str, country: str, page: int, page_size: int) -> list[dict]:
    if not settings.NEWS_API_KEY:
        return []
    params = {'language': 'en', 'page': page, 'pageSize': min(page_size, 100)}
    endpoint = 'everything'
    if query:
        params.update({'q': query, 'sortBy': 'publishedAt'})
    else:
        endpoint = 'top-headlines'
        params['country'] = country or 'us'
        if category and category != 'all':
            params['category'] = category
    url = f"https://newsapi.org/v2/{endpoint}?{urlencode(params)}"
    payload = _request_json(url, {'X-Api-Key': settings.NEWS_API_KEY})
    if payload.get('status') != 'ok':
        raise NewsProviderError(payload.get('message', 'NewsAPI request failed'))
    return [article for item in payload.get('articles', []) if (article := _normalise('newsapi', item, category))]


def _from_gnews(query: str, category: str, country: str, page: int, page_size: int) -> list[dict]:
    if not settings.GNEWS_API_KEY:
        return []
    endpoint = 'search' if query else 'top-headlines'
    params = {'lang': 'en', 'max': min(page_size, 10), 'page': page, 'apikey': settings.GNEWS_API_KEY}
    if query:
        params['q'] = query
    else:
        params['country'] = country or 'us'
        if category and category != 'all':
            params['category'] = category
    # GNews must not hold up the combined feed when its edge is unreachable.
    payload = _request_json(f'https://gnews.io/api/v4/{endpoint}?{urlencode(params)}', timeout=2)
    return [article for item in payload.get('articles', []) if (article := _normalise('gnews', item, category))]


def fetch_external_news(*, query='', category='general', country='us', page=1, page_size=15):
    """Return a short-lived cached list and non-sensitive provider errors.

    A failed provider is deliberately non-fatal: callers can still render local reporting.
    """
    cache_payload = json.dumps(
        [query, category, country, page, page_size],
        ensure_ascii=True,
        separators=(',', ':'),
    )
    cache_key = f"chronicle:feed:{hashlib.sha256(cache_payload.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    articles, errors = [], []
    providers = (_from_newsapi, _from_gnews)
    # Independent provider requests run concurrently: one slow provider must not
    # delay a healthy one or hide original Chronicle reporting.
    with ThreadPoolExecutor(max_workers=len(providers)) as executor:
        requests = {provider: executor.submit(provider, query, category, country, page, page_size) for provider in providers}
        for provider in providers:
            try:
                articles.extend(requests[provider].result())
            except NewsProviderError:
                errors.append(provider.__name__.removeprefix('_from_'))

    unique = {article['external_id']: article for article in articles}
    result = (list(unique.values())[:page_size], errors)
    cache.set(cache_key, result, timeout=300)
    return result


def persist_external_article(item: dict):
    """Save only the stable interaction metadata, never provider full text."""
    from .models import ExternalArticle

    published = _as_datetime(item.get('publishedAt'))
    return ExternalArticle.objects.update_or_create(
        external_id=item['external_id'],
        defaults={
            'provider': item.get('provider', 'external'),
            'canonical_url': item['url'],
            'title': item['title'],
            'source_name': item.get('source', {}).get('name', ''),
            'description': item.get('description', '')[:1000],
            'image_url': item.get('urlToImage', ''),
            'category': item.get('category', 'general'),
            'published_at': published,
        },
    )[0]
