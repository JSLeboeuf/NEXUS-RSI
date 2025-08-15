"""
Multi-Source Scraper pour NEXUS-RSI
Veille technologique continue H24
"""

import asyncio
import aiohttp
import feedparser
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import time

class MultiSourceScraper:
    """Scraper multi-source pour veille continue"""
    
    def __init__(self):
        self.sources = self._load_sources()
        self.cache_dir = Path("scrapers/cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.seen_items = set()
        self.new_discoveries = []
        
    def _load_sources(self) -> Dict[str, List[str]]:
        """Charge les sources à surveiller"""
        return {
            "github": [
                "https://github.com/trending",
                "https://api.github.com/repos/langchain-ai/langchain/releases",
                "https://api.github.com/repos/microsoft/autogen/releases",
                "https://api.github.com/repos/joaomdmoura/crewAI/releases"
            ],
            "arxiv": [
                "http://arxiv.org/rss/cs.AI",
                "http://arxiv.org/rss/cs.LG",
                "http://arxiv.org/rss/cs.CL"
            ],
            "reddit": [
                "https://www.reddit.com/r/MachineLearning/.rss",
                "https://www.reddit.com/r/artificial/.rss",
                "https://www.reddit.com/r/LocalLLaMA/.rss"
            ],
            "hackernews": [
                "https://hnrss.org/newest?q=AI+OR+LLM+OR+agents",
                "https://hnrss.org/best"
            ],
            "twitter": [
                # Twitter API endpoints (nécessite auth)
            ],
            "discord": [
                # Discord webhooks
            ]
        }
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Fetch une URL de manière asynchrone"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        "url": url,
                        "content": content,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success"
                    }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
        return None
    
    async def scrape_all_sources(self) -> List[Dict]:
        """Scrape toutes les sources en parallèle"""
        results = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # GitHub
            for url in self.sources.get("github", []):
                tasks.append(self.fetch_url(session, url))
            
            # ArXiv RSS
            for url in self.sources.get("arxiv", []):
                tasks.append(self.process_rss_feed(url))
            
            # Reddit RSS
            for url in self.sources.get("reddit", []):
                tasks.append(self.process_rss_feed(url))
            
            # HackerNews
            for url in self.sources.get("hackernews", []):
                tasks.append(self.process_rss_feed(url))
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*tasks)
            
        return [r for r in results if r is not None]
    
    async def process_rss_feed(self, feed_url: str) -> Dict:
        """Process RSS feeds"""
        try:
            feed = feedparser.parse(feed_url)
            items = []
            
            for entry in feed.entries[:10]:  # Limite aux 10 derniers
                item_hash = hashlib.md5(entry.link.encode()).hexdigest()
                
                if item_hash not in self.seen_items:
                    self.seen_items.add(item_hash)
                    items.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", "")[:500],
                        "source": feed_url,
                        "hash": item_hash,
                        "discovered_at": datetime.now().isoformat()
                    })
                    self.new_discoveries.append(entry.title)
            
            return {
                "source": feed_url,
                "items": items,
                "count": len(items),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "source": feed_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_discoveries(self) -> Dict:
        """Analyse les nouvelles découvertes"""
        analysis = {
            "total_new": len(self.new_discoveries),
            "sources_active": len([s for s in self.sources.values() if s]),
            "categories": {}
        }
        
        # Catégorisation simple
        for discovery in self.new_discoveries:
            discovery_lower = discovery.lower()
            
            if "llm" in discovery_lower or "language model" in discovery_lower:
                analysis["categories"]["llm"] = analysis["categories"].get("llm", 0) + 1
            elif "agent" in discovery_lower:
                analysis["categories"]["agents"] = analysis["categories"].get("agents", 0) + 1
            elif "ai" in discovery_lower or "artificial" in discovery_lower:
                analysis["categories"]["ai"] = analysis["categories"].get("ai", 0) + 1
            else:
                analysis["categories"]["other"] = analysis["categories"].get("other", 0) + 1
        
        return analysis
    
    def save_discoveries(self):
        """Sauvegarde les découvertes dans le cache"""
        cache_file = self.cache_dir / f"discoveries_{datetime.now():%Y%m%d_%H%M%S}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "discoveries": self.new_discoveries,
            "analysis": self.analyze_discoveries(),
            "seen_count": len(self.seen_items)
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return cache_file
    
    async def continuous_monitoring(self, interval_minutes: int = 15):
        """Monitoring continu avec intervalle configurable"""
        print(f"🔍 Starting continuous monitoring (interval: {interval_minutes} min)")
        
        while True:
            try:
                print(f"\n📡 Scanning sources at {datetime.now():%H:%M:%S}")
                
                # Scrape all sources
                results = await self.scrape_all_sources()
                
                # Analyze and save
                if self.new_discoveries:
                    analysis = self.analyze_discoveries()
                    cache_file = self.save_discoveries()
                    
                    print(f"✨ Found {len(self.new_discoveries)} new items!")
                    print(f"📊 Categories: {analysis['categories']}")
                    print(f"💾 Saved to: {cache_file}")
                    
                    # Reset for next iteration
                    self.new_discoveries = []
                else:
                    print("ℹ️ No new discoveries this iteration")
                
                # Wait for next iteration
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error


async def main():
    """Main function"""
    scraper = MultiSourceScraper()
    
    # Test single scrape
    print("🚀 Testing single scrape...")
    results = await scraper.scrape_all_sources()
    print(f"📊 Scraped {len(results)} sources")
    
    # Start continuous monitoring
    await scraper.continuous_monitoring(interval_minutes=15)


if __name__ == "__main__":
    asyncio.run(main())