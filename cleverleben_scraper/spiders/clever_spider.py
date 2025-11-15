import scrapy
from cleverleben_scraper.items import CleverlebenItem
from urllib.parse import urljoin
import re
import json

class CleverSpider(scrapy.Spider):
    name = 'clever_spider'
    allowed_domains = ['cleverleben.at']
    start_urls = ['https://www.cleverleben.at/produktauswahl']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 0.3,
        'AUTOTHROTTLE_ENABLED': True,
    }

    def parse(self, response):
        """
        Parse the main produktauswahl page and extract ALL category links
        """
        self.logger.info(f"Parsing main page: {response.url}")
        
        # Extract ALL category links automatically
        category_selectors = [
            '//nav//a/@href',
            '//header//a/@href',
            '//a[contains(@href, "/lebensmittel")]/@href',
            '//a[contains(@href, "/getraenke")]/@href',
            '//a[contains(@href, "/haushalt")]/@href',
            '//a[contains(@href, "/tiernahrung")]/@href',
            '//a[contains(@class, "category")]/@href',
            '//div[contains(@class, "category")]//a/@href'
        ]
        
        category_links = []
        for selector in category_selectors:
            links = response.xpath(selector).getall()
            if links:
                category_links.extend(links)
        
        # Also get all links and filter for category patterns
        all_links = response.xpath('//a/@href').getall()
        category_patterns = [
            link for link in all_links 
            if link and not link.startswith('http') and len(link) > 1 
            and not link.startswith('#') 
            and any(keyword in link for keyword in ['lebensmittel', 'getraenke', 'haushalt', 'tiernahrung', 'kategorie', 'category'])
        ]
        category_links.extend(category_patterns)
        
        # Clean and deduplicate
        category_links = list(set([urljoin(response.url, link) for link in category_links if link]))
        
        self.logger.info(f"Found {len(category_links)} total category links")
        
        # Process all discovered categories
        for category_link in category_links:
            yield scrapy.Request(
                url=category_link,
                callback=self.parse_main_category,
                meta={'category_url': category_link}
            )

    def parse_main_category(self, response):
        """
        Parse main category page and extract ALL SUBcategory links
        """
        self.logger.info(f"Parsing main category: {response.url}")
        
        # Extract subcategory links using multiple strategies
        subcategory_selectors = [
            '//a[contains(@href, "/produkte/")]/@href',
            '//div[contains(@class, "category")]//a/@href',
            '//nav//a/@href',
            '//a[contains(@class, "subcategory")]/@href',
            '//div[contains(@class, "grid")]//a/@href',
            '//section//a/@href'
        ]
        
        subcategory_links = []
        for selector in subcategory_selectors:
            links = response.xpath(selector).getall()
            if links:
                subcategory_links.extend(links)
        
        # Also look for any links that might be subcategories
        all_links = response.xpath('//a/@href').getall()
        potential_subcategories = [
            link for link in all_links 
            if '/produkte/' in link 
            and not link.startswith('http')
            and len(link) > 10  # Filter out very short links
        ]
        subcategory_links.extend(potential_subcategories)
        
        # Clean and deduplicate
        subcategory_links = list(set([urljoin(response.url, link) for link in subcategory_links if link]))
        
        self.logger.info(f"Found {len(subcategory_links)} subcategories in {response.url}")
        
        for subcategory_link in subcategory_links:
            yield scrapy.Request(
                url=subcategory_link,
                callback=self.parse_subcategory,
                meta={'main_category_url': response.url}
            )

    def parse_subcategory(self, response):
        """
        Parse subcategory page and extract INDIVIDUAL PRODUCT links with aggressive pagination
        """
        self.logger.info(f"Parsing subcategory: {response.url}")
        
        # Extract individual product links using multiple strategies
        product_selectors = [
            '//a[contains(@href, "/produkt/")]/@href',
            '//article//a/@href',
            '//div[contains(@class, "product")]//a/@href',
            '//div[contains(@class, "item")]//a/@href',
            '//div[contains(@class, "card")]//a/@href',
            '//li[contains(@class, "product")]//a/@href'
        ]
        
        product_links = []
        for selector in product_selectors:
            links = response.xpath(selector).getall()
            if links:
                product_links.extend(links)
        
        # Also check all links for product patterns
        all_links = response.xpath('//a/@href').getall()
        product_patterns = [
            link for link in all_links 
            if '/produkt/' in link 
            and not '/produkte/' in link
            and len(link) > 10  # Filter out very short links
        ]
        product_links.extend(product_patterns)
        
        # Clean and deduplicate
        product_links = list(set([urljoin(response.url, link) for link in product_links if link]))
        
        self.logger.info(f"Found {len(product_links)} individual product links on {response.url}")
        
        for product_link in product_links:
            yield scrapy.Request(
                url=product_link,
                callback=self.parse_product,
                meta={'subcategory_url': response.url}
            )
        
        # More aggressive pagination handling
        pagination_selectors = [
            '//a[contains(@class, "next")]/@href',
            '//a[contains(@rel, "next")]/@href',
            '//a[contains(text(), "Weiter")]/@href',
            '//a[contains(text(), "Next")]/@href',
            '//a[@aria-label="Next"]/@href',
            '//a[contains(text(), "›")]/@href',
            '//a[contains(text(), ">")]/@href',
            '//link[@rel="next"]/@href',
            '//a[contains(@class, "pagination")]/@href',
            '//nav//a[contains(@href, "page")]/@href',
            '//a[contains(@href, "?page")]/@href'
        ]
        
        for selector in pagination_selectors:
            next_pages = response.xpath(selector).getall()
            for next_page in next_pages:
                if next_page and next_page.strip():
                    full_next_url = urljoin(response.url, next_page.strip())
                    # Avoid infinite loops by checking if we've seen this URL pattern
                    if full_next_url != response.url and not full_next_url.endswith('#'):
                        self.logger.info(f"Found next page: {full_next_url}")
                        yield scrapy.Request(
                            url=full_next_url,
                            callback=self.parse_subcategory,
                            meta={'main_category_url': response.meta.get('main_category_url')}
                        )

    def parse_product(self, response):
        """
        Parse INDIVIDUAL PRODUCT page and extract all required fields
        """
        item = CleverlebenItem()
        
        # Extract product URL
        item['product_url'] = response.url
        
        # Extract product name
        name_selectors = [
            '//h1[@itemprop="name"]/text()',
            '//h1[contains(@class, "product")]/text()',
            '//h1/text()',
            '//title/text()',
            '//meta[@property="og:title"]/@content'
        ]
        
        for selector in name_selectors:
            product_name = response.xpath(selector).get()
            if product_name and product_name.strip():
                clean_name = product_name.strip()
                if '|' in clean_name:
                    clean_name = clean_name.split('|')[0].strip()
                item['product_name'] = clean_name
                break
        
        # Extract price
        price_selectors = [
            '//span[@itemprop="price"]/text()',
            '//meta[@property="product:price:amount"]/@content',
            '//span[contains(@class, "price")]//text()',
            '//div[contains(@class, "price")]//text()'
        ]
        
        for selector in price_selectors:
            price_texts = response.xpath(selector).getall()
            for price_text in price_texts:
                if price_text:
                    price_match = re.search(r'(\d+[.,]\d+|\d+)', price_text)
                    if price_match:
                        item['price'] = price_match.group(1).replace(',', '.')
                        break
            if item.get('price'):
                break
        
        # Extract images
        image_selectors = [
            '//img[@itemprop="image"]/@src',
            '//meta[@property="og:image"]/@content',
            '//div[contains(@class, "product-image")]//img/@src',
            '//img[contains(@class, "product")]/@src'
        ]
        
        images = []
        for selector in image_selectors:
            found_images = response.xpath(selector).getall()
            if found_images:
                images.extend(found_images)
        
        item['image'] = [urljoin(response.url, img) for img in set(images) if img and not img.startswith('data:')]
        
        # Extract product description
        desc_selectors = [
            '//div[@itemprop="description"]//text()',
            '//meta[@name="description"]/@content',
            '//div[contains(@class, "description")]//text()'
        ]
        
        description_parts = []
        for selector in desc_selectors:
            descriptions = response.xpath(selector).getall()
            for desc in descriptions:
                if desc and desc.strip():
                    clean_desc = ' '.join(desc.strip().split())
                    if clean_desc and len(clean_desc) > 10:
                        if clean_desc not in description_parts:
                            description_parts.append(clean_desc)
        
        if description_parts:
            item['product_description'] = ' | '.join(description_parts[:2])
        
        # Extract unique_id from URL
        unique_id_match = re.search(r'-(\d+)$', response.url) or re.search(r'/(\d+)$', response.url)
        if unique_id_match:
            item['unique_id'] = unique_id_match.group(1)
        else:
            item['unique_id'] = response.url.split('/')[-1]
        
        # Extract ingredients
        ingredients_selectors = [
            '//td[contains(text(), "Zutaten")]/following-sibling::td//text()',
            '//div[contains(text(), "Zutaten")]/following-sibling::div//text()',
            '//h3[contains(text(), "Zutaten")]/following-sibling::p//text()'
        ]
        
        for selector in ingredients_selectors:
            ingredients = response.xpath(selector).get()
            if ingredients and ingredients.strip():
                item['ingredients'] = ingredients.strip()
                break
        
        # Extract details
        details_selectors = [
            '//td[contains(text(), "Produktinformation")]/following-sibling::td//text()',
            '//div[contains(text(), "Produktinformation")]/following-sibling::div//text()',
            '//h2[contains(text(), "Produktinformation")]/following-sibling::p//text()'
        ]
        
        for selector in details_selectors:
            details = response.xpath(selector).get()
            if details and details.strip():
                item['details'] = details.strip()
                break
        
        # Default values
        item['currency'] = '€'
        item['product_id'] = item.get('unique_id', '')
        
        # Only yield if we have a product name and it doesn't look like a category
        if (item.get('product_name') and 
            len(item['product_name']) > 5 and
            not any(word in item['product_name'].lower() for word in ['kategorie', 'category', 'übersicht', 'alle '])):
            
            self.logger.info(f"Successfully extracted PRODUCT: {item['product_name']}")
            yield item
        else:
            self.logger.warning(f"Skipping - appears to be category page: {response.url}")