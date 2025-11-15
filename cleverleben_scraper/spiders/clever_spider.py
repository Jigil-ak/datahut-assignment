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
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 1,
        'AUTOTHROTTLE_ENABLED': True,
    }

    def parse(self, response):
        """
        Parse the main produktauswahl page and extract category links
        """
        self.logger.info(f"Parsing main page: {response.url}")
        
        # Extract the main category links we found
        main_categories = [
            '/lebensmittel',
            '/getraenke', 
            '/haushalt-hygiene',
            '/tiernahrung'
        ]
        
        for category_path in main_categories:
            category_url = urljoin(response.url, category_path)
            self.logger.info(f"Processing category: {category_url}")
            
            yield scrapy.Request(
                url=category_url,
                callback=self.parse_category,
                meta={'category': category_path.replace('/', '')}
            )

    def parse_category(self, response):
        """
        Parse category page and extract product links with pagination
        """
        self.logger.info(f"Parsing category: {response.url}")
        
        # Extract product links - try multiple selectors
        product_selectors = [
            '//a[contains(@href, "/produkt/")]/@href',
            '//a[contains(@href, "produkt")]/@href',
        ]
        
        product_links = []
        for selector in product_selectors:
            links = response.xpath(selector).getall()
            if links:
                product_links.extend(links)
        
        # Clean and deduplicate product links
        product_links = list(set([urljoin(response.url, link) for link in product_links if link]))
        
        self.logger.info(f"Found {len(product_links)} product links on {response.url}")
        
        for product_link in product_links:
            yield scrapy.Request(
                url=product_link,
                callback=self.parse_product,
                meta={'category': response.meta.get('category', 'Unknown')}
            )
        
        # Handle pagination - try multiple selectors
        next_selectors = [
            '//a[contains(@class, "next")]/@href',
            '//a[contains(@rel, "next")]/@href',
            '//a[contains(text(), "Weiter")]/@href',
            '//a[contains(text(), "Next")]/@href',
            '//a[@aria-label="Next"]/@href'
        ]
        
        for selector in next_selectors:
            next_page = response.xpath(selector).get()
            if next_page:
                full_next_url = urljoin(response.url, next_page)
                self.logger.info(f"Found next page: {full_next_url}")
                yield scrapy.Request(
                    url=full_next_url,
                    callback=self.parse_category,
                    meta={'category': response.meta.get('category', 'Unknown')}
                )
                break

    def parse_product(self, response):
        """
        Parse individual product page and extract all required fields
        """
        item = CleverlebenItem()
        
        # Extract product URL
        item['product_url'] = response.url
        
        # Extract product name
        name_selectors = [
            '//h1//text()',
            '//title/text()',
            '//meta[@property="og:title"]/@content'
        ]
        
        for selector in name_selectors:
            product_name = response.xpath(selector).get()
            if product_name and product_name.strip():
                item['product_name'] = product_name.strip()
                break
        
        # Extract price
        price_selectors = [
            '//span[contains(@class, "price")]//text()',
            '//meta[@property="product:price:amount"]/@content',
            '//div[contains(@class, "price")]//text()',
            '//*[contains(@class, "currency")]/preceding-sibling::text()'
        ]
        
        for selector in price_selectors:
            price_text = response.xpath(selector).get()
            if price_text:
                # Clean price - extract numbers and decimals
                price_match = re.search(r'(\d+[.,]\d+|\d+)', price_text)
                if price_match:
                    item['price'] = price_match.group(1).replace(',', '.')
                    break
        
        # Extract images
        image_selectors = [
            '//img[contains(@src, "produkt")]/@src',
            '//img[contains(@alt, "product")]/@src',
            '//div[contains(@class, "product-image")]//img/@src',
            '//meta[@property="og:image"]/@content'
        ]
        
        images = []
        for selector in image_selectors:
            found_images = response.xpath(selector).getall()
            if found_images:
                images.extend(found_images)
        
        item['image'] = [urljoin(response.url, img) for img in set(images) if img]
        
        # Extract product description
        desc_selectors = [
            '//meta[@name="description"]/@content',
            '//div[contains(@class, "description")]//text()',
            '//p[contains(@class, "description")]//text()'
        ]
        
        description_parts = []
        for selector in desc_selectors:
            descriptions = response.xpath(selector).getall()
            for desc in descriptions:
                if desc and desc.strip():
                    description_parts.append(desc.strip())
        
        if description_parts:
            item['product_description'] = ' '.join(description_parts)
        
        # Extract unique_id from URL
        unique_id_match = re.search(r'-(\d+)$', response.url) or re.search(r'/(\d+)$', response.url)
        if unique_id_match:
            item['unique_id'] = unique_id_match.group(1)
        else:
            # Fallback: use last part of URL
            item['unique_id'] = response.url.split('/')[-1]
        
        # Extract ingredients
        ingredients_selectors = [
            '//td[contains(text(), "Zutaten")]/following-sibling::td//text()',
            '//div[contains(text(), "Zutaten")]/following-sibling::div//text()',
            '//h3[contains(text(), "Zutaten")]/following-sibling::p//text()',
            '//*[contains(text(), "Zutaten")]/following::text()[1]'
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
        
        # Only yield if we have at least a product name
        if item.get('product_name'):
            self.logger.info(f"Successfully extracted product: {item['product_name']}")
            yield item
        else:
            self.logger.warning(f"No product name found for {response.url}")