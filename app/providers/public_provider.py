"""Public API provider using free endpoints (CoinGecko)."""

import re
from datetime import datetime, timedelta
from typing import Any
from xml.etree import ElementTree

import httpx

from app.providers.base import MarketProvider
from app.providers.mock_provider import MockMarketProvider
from app.utils.logger import logger

# CoinGecko API endpoints (free, no API key required)
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_SIMPLE_PRICE = f"{COINGECKO_API_BASE}/simple/price"
COINGECKO_COINS = f"{COINGECKO_API_BASE}/coins"

# RSS Feed sources for cryptocurrency news
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]

# Symbol mapping: our symbols -> CoinGecko IDs
SYMBOL_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "AVAX": "avalanche-2",
}


class PublicProvider(MarketProvider):
    """Provider using public APIs (CoinGecko) for real market data."""

    def __init__(self):
        """Initialize public provider with fallback to mock."""
        self._fallback_provider = MockMarketProvider()
        self._http_timeout = 10.0

    async def get_spot_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get spot market snapshot from CoinGecko API.

        Args:
            symbols: List of cryptocurrency symbols.

        Returns:
            Dictionary with spot market data, or fallback to mock if API fails.
        """
        try:
            # Map symbols to CoinGecko IDs
            coin_ids = []
            symbol_map = {}  # coin_id -> symbol
            for symbol in symbols:
                symbol_upper = symbol.upper()
                if symbol_upper in SYMBOL_TO_COINGECKO_ID:
                    coin_id = SYMBOL_TO_COINGECKO_ID[symbol_upper]
                    coin_ids.append(coin_id)
                    symbol_map[coin_id] = symbol_upper

            if not coin_ids:
                logger.warning("No valid symbols found, using fallback")
                return await self._fallback_provider.get_spot_snapshot(symbols)

            # Fetch data from CoinGecko
            async with httpx.AsyncClient(timeout=self._http_timeout) as client:
                # Get simple price data
                params = {
                    "ids": ",".join(coin_ids),
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true",
                    "include_24hr_high": "true",
                    "include_24hr_low": "true",
                }

                response = await client.get(COINGECKO_SIMPLE_PRICE, params=params)
                response.raise_for_status()
                price_data = response.json()

            # Transform CoinGecko data to our format
            result: dict[str, Any] = {}
            for coin_id, data in price_data.items():
                if coin_id not in symbol_map:
                    continue

                symbol = symbol_map[coin_id]
                result[symbol] = {
                    "price": data.get("usd", 0.0),
                    "change_24h": data.get("usd_24h_change", 0.0) or 0.0,
                    "volume_24h": data.get("usd_24h_vol", 0.0) or 0.0,
                    "market_cap": data.get("usd_market_cap", 0.0) or 0.0,
                    "high_24h": data.get("usd_24h_high", 0.0) or 0.0,
                    "low_24h": data.get("usd_24h_low", 0.0) or 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            if result:
                logger.info(
                    f"Successfully fetched spot data for {len(result)} symbols from CoinGecko"
                )
                return result
            else:
                logger.warning("No data returned from CoinGecko, using fallback")
                return await self._fallback_provider.get_spot_snapshot(symbols)

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"CoinGecko API returned error: {e.response.status_code}, using fallback"
            )
            return await self._fallback_provider.get_spot_snapshot(symbols)
        except httpx.RequestError as e:
            logger.warning(f"CoinGecko API request failed: {str(e)}, using fallback")
            return await self._fallback_provider.get_spot_snapshot(symbols)
        except Exception as e:
            logger.warning(f"Unexpected error fetching from CoinGecko: {str(e)}, using fallback")
            return await self._fallback_provider.get_spot_snapshot(symbols)

    async def get_derivatives_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get derivatives snapshot (fallback to mock).

        Args:
            symbols: List of cryptocurrency symbols.

        Returns:
            Dictionary with derivatives data from mock provider.
        """
        logger.info("Derivatives data not available from public API, using mock fallback")
        return await self._fallback_provider.get_derivatives_snapshot(symbols)

    async def get_news_snapshot(self, keywords: list[str]) -> list[dict[str, Any]]:
        """
        Get news snapshot from RSS feeds and CoinGecko.

        Args:
            keywords: List of keywords to filter news.

        Returns:
            List of news items, or fallback to mock if all sources fail.
        """
        try:
            # Try RSS feeds first
            news_items = await self._fetch_news_from_rss(keywords)
            
            if news_items:
                logger.info(f"Successfully fetched {len(news_items)} news items from RSS feeds")
                return news_items[:10]  # Limit to 10 items
            
            # If RSS fails, try CoinGecko news API
            news_items = await self._fetch_news_from_coingecko(keywords)
            
            if news_items:
                logger.info(f"Successfully fetched {len(news_items)} news items from CoinGecko")
                return news_items[:10]
            
            # Fallback to mock
            logger.warning("All news sources failed, using mock fallback")
            return await self._fallback_provider.get_news_snapshot(keywords)
            
        except Exception as e:
            logger.warning(f"Error fetching news: {str(e)}, using mock fallback")
            return await self._fallback_provider.get_news_snapshot(keywords)

    async def _fetch_news_from_rss(self, keywords: list[str]) -> list[dict[str, Any]]:
        """
        Fetch news from RSS feeds.

        Args:
            keywords: List of keywords to filter news.

        Returns:
            List of news items.
        """
        news_items: list[dict[str, Any]] = []
        keywords_lower = [k.lower() for k in keywords]
        
        async with httpx.AsyncClient(timeout=self._http_timeout, follow_redirects=True) as client:
            for feed_url in RSS_FEEDS:
                try:
                    logger.debug(f"Fetching RSS feed: {feed_url}")
                    response = await client.get(feed_url)
                    response.raise_for_status()
                    
                    # Parse RSS XML
                    try:
                        root = ElementTree.fromstring(response.content)
                    except ElementTree.ParseError as e:
                        logger.warning(f"Failed to parse XML from {feed_url}: {str(e)}")
                        continue
                    
                    # Handle different RSS namespaces
                    namespaces = {
                        'atom': 'http://www.w3.org/2005/Atom',
                        'rss': 'http://purl.org/rss/1.0/',
                        'content': 'http://purl.org/rss/1.0/modules/content/',
                        'dc': 'http://purl.org/dc/elements/1.1/',
                    }
                    
                    # Find items (try different possible structures)
                    # Try channel/item first (standard RSS 2.0), then .//item (anywhere), then Atom entry
                    items = []
                    channel = root.find('channel')
                    if channel is not None:
                        items = channel.findall('item')
                    if not items:
                        items = root.findall('.//item')
                    if not items:
                        items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                    
                    logger.debug(f"Found {len(items)} items in {feed_url}")
                    
                    items_processed = 0
                    items_added = 0
                    for item in items[:20]:  # Limit per feed
                        try:
                            items_processed += 1
                            # Extract title (try multiple ways)
                            title_elem = item.find('title')
                            if title_elem is None:
                                title_elem = item.find('{http://www.w3.org/2005/Atom}title')
                            if title_elem is None or title_elem.text is None:
                                logger.debug(f"Skipping item {items_processed}: no title (tag: {item.tag})")
                                continue
                            title = title_elem.text.strip()
                            if not title:
                                logger.debug(f"Skipping item {items_processed}: empty title")
                                continue
                            
                            # Extract link (try multiple ways)
                            link_elem = item.find('link')
                            url = ""
                            if link_elem is not None:
                                # RSS 2.0: link is text content
                                url = link_elem.text or ""
                                # Atom: link might have href attribute
                                if not url:
                                    url = link_elem.get('href', '')
                            
                            # Try Atom link format if RSS link didn't work
                            if not url:
                                link_elem = item.find('{http://www.w3.org/2005/Atom}link')
                                if link_elem is not None:
                                    url = link_elem.get('href', '') or link_elem.text or ''
                            
                            if not url:
                                logger.debug(f"Skipping item {items_processed}: no URL (title: {title[:50]})")
                                continue
                            
                            url = url.strip()
                            
                            # Extract description
                            desc_elem = item.find('description') or item.find('{http://purl.org/rss/1.0/modules/content/}encoded') or item.find('{http://www.w3.org/2005/Atom}summary')
                            description = ""
                            if desc_elem is not None and desc_elem.text:
                                description = desc_elem.text.strip()
                                # Remove HTML tags (do this early for keyword matching)
                                description = re.sub(r'<[^>]+>', '', description)
                                # Clean up extra whitespace
                                description = re.sub(r'\s+', ' ', description).strip()
                            
                            # Extract published date
                            pub_elem = item.find('pubDate') or item.find('{http://purl.org/dc/elements/1.1/}date') or item.find('{http://www.w3.org/2005/Atom}published')
                            published_at = datetime.utcnow().isoformat()
                            if pub_elem is not None and pub_elem.text:
                                try:
                                    # Try parsing various date formats
                                    date_str = pub_elem.text.strip()
                                    # Common RSS date format: "Mon, 01 Jan 2024 12:00:00 GMT"
                                    for fmt in [
                                        "%a, %d %b %Y %H:%M:%S %Z",
                                        "%a, %d %b %Y %H:%M:%S %z",
                                        "%Y-%m-%dT%H:%M:%S%z",
                                        "%Y-%m-%dT%H:%M:%SZ",
                                    ]:
                                        try:
                                            dt = datetime.strptime(date_str, fmt)
                                            published_at = dt.isoformat()
                                            break
                                        except ValueError:
                                            continue
                                except Exception:
                                    pass
                            
                            # Extract source
                            source_elem = item.find('source') or item.find('{http://purl.org/dc/elements/1.1/}publisher')
                            source = "Unknown"
                            if source_elem is not None and source_elem.text:
                                source = source_elem.text.strip()
                            else:
                                # Extract from feed URL
                                if 'coindesk' in feed_url:
                                    source = "CoinDesk"
                                elif 'cointelegraph' in feed_url:
                                    source = "Cointelegraph"
                                elif 'decrypt' in feed_url:
                                    source = "Decrypt"
                            
                            # Filter by keywords (case-insensitive, relaxed matching)
                            # Clean title and description for matching
                            title_clean = re.sub(r'[^\w\s]', ' ', title).lower()
                            desc_clean = description.lower() if description else ""
                            text_to_check = f"{title_clean} {desc_clean}"
                            
                            # If keywords provided, check if any keyword matches
                            # Use relaxed matching: check for partial matches and common crypto terms
                            if keywords_lower:
                                # Common crypto-related terms that should always pass
                                crypto_terms = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency', 
                                               'blockchain', 'defi', 'nft', 'web3', 'altcoin', 'token', 'coin',
                                               'mining', 'wallet', 'exchange', 'trading', 'market']
                                
                                # Check if text contains any crypto term or keyword
                                has_crypto_term = any(term in text_to_check for term in crypto_terms)
                                has_keyword = any(kw in text_to_check for kw in keywords_lower)
                                
                                # Pass if it has crypto term OR keyword match
                                if not (has_crypto_term or has_keyword):
                                    logger.debug(f"Skipping news item (no keyword/crypto match): {title[:50]}...")
                                    continue
                            
                            # Determine sentiment (simple heuristic)
                            sentiment = "neutral"
                            positive_words = ['surge', 'rally', 'gain', 'up', 'bullish', 'rise', 'growth', 'positive', 'approval', 'adoption']
                            negative_words = ['crash', 'drop', 'fall', 'down', 'bearish', 'decline', 'loss', 'negative', 'rejection', 'ban']
                            
                            if any(word in text_to_check for word in positive_words):
                                sentiment = "positive"
                            elif any(word in text_to_check for word in negative_words):
                                sentiment = "negative"
                            
                            news_item = {
                                "title": title,
                                "source": source,
                                "published_at": published_at,
                                "url": url,
                                "sentiment": sentiment,
                                "keywords": keywords,
                                "summary": description[:200] if description else "",  # Limit summary length
                            }
                            
                            news_items.append(news_item)
                            items_added += 1
                            
                        except Exception as e:
                            logger.debug(f"Error parsing RSS item {items_processed} from {feed_url}: {str(e)}")
                            continue
                    
                    logger.info(f"Processed {items_processed} items, added {items_added} news items from {feed_url}")
                            
                except httpx.RequestError as e:
                    logger.warning(f"Failed to fetch RSS feed {feed_url}: {str(e)}")
                    continue
                except Exception as e:
                    logger.warning(f"Error parsing RSS feed {feed_url}: {str(e)}")
                    continue
        
        # Sort by published_at (newest first)
        news_items.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        return news_items

    async def _fetch_news_from_coingecko(self, keywords: list[str]) -> list[dict[str, Any]]:
        """
        Fetch news from CoinGecko news API (if available).

        Args:
            keywords: List of keywords.

        Returns:
            List of news items.
        """
        # CoinGecko doesn't have a public news API endpoint in v3
        # This is a placeholder for future implementation
        # For now, return empty list to fallback to RSS
        return []

    def is_available(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True (public API is always available, though may fail at runtime).
        """
        return True

