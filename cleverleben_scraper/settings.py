BOT_NAME = 'cleverleben_scraper'

SPIDER_MODULES = ['cleverleben_scraper.spiders']
NEWSPIDER_MODULE = 'cleverleben_scraper.spiders'

ROBOTSTXT_OBEY = True

# Configure delays to be polite
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True

# Auto throttle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10

# Set user agent
USER_AGENT = 'cleverleben_scraper (+http://www.yourdomain.com)'

# Configure item pipelines
ITEM_PIPELINES = {
    'cleverleben_scraper.pipelines.CleverlebenScraperPipeline': 300,
}

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600

FEED_EXPORT_ENCODING = 'utf-8'

# Set concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8