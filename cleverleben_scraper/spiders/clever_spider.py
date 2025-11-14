# This code follows PEP8 standards
import scrapy
import json
from cleverleben_scraper.items import CleverlebenScraperItem


class CleverSpiderSpider(scrapy.Spider):
    """
    This spider crawls cleverleben.at to extract product data
    based on the Datahut assignment.
    It uses the website's internal API for crawling
    and scrapes product data from the product page.
    """
    name = 'clever_spider'
    allowed_domains = ['cleverleben.at', 'clv-product-api.billa.at']

    # 1. Start by calling the API for main categories
    def start_requests(self):
        """
        Starts the crawl from the main category API.
        """
        yield scrapy.Request(
            url='https://clv-product-api.billa.at/api/v1/product-categories/root',
            callback=self.parse_main_categories
        )

    # 2. Parse the API response for main categories
    def parse_main_categories(self, response):
        """
        Parses the JSON response for main categories (Lebensmittel, etc.)
        and follows their links.
        """
        data = response.json()
        
        # Loop through each main category found in the JSON
        for category in data.get('subCategories', []):
            category_slug = category.get('slug')
            if category_slug:
                # Build the URL for the next API call (sub-categories)
                subcategory_url = f'https://clv-product-api.billa.at/api/v1/product-categories/{category_slug}'
                yield response.follow(subcategory_url, callback=self.parse_sub_categories)

    # 3. Parse the API response for sub-categories
    def parse_sub_categories(self, response):
        """
        Parses the JSON response for sub-categories (Brot & Backware, etc.).
        If no sub-categories, it calls the product list parser.
        """
        data = response.json()
        subcategories = data.get('subCategories', [])

        if subcategories:
            # Found sub-categories, loop through them
            for subcat in subcategories:
                subcat_slug = subcat.get('slug')
                if subcat_slug:
                    # Build the URL for the product list API
                    product_list_url = f'https://clv-product-api.billa.at/api/v1/product-search/{subcat_slug}?page=1&size=24'
                    yield response.follow(product_list_url, callback=self.parse_product_list)
        else:
            # No sub-categories, this page IS the product list.
            # We call the product list parser on the *current* response's URL.
            # We just need to change 'product-categories' to 'product-search'
            product_list_url = response.url.replace(
                'product-categories', 'product-search'
            ) + '?page=1&size=24'
            yield response.follow(product_list_url, callback=self.parse_product_list)

    # 4. Parse the product list API and handle pagination
    def parse_product_list(self, response):
        """
        Parses the product list JSON, follows links to product pages,
        and handles pagination by calling itself.
        """
        data = response.json()

        # 4.1. Get all product URLs on the current page
        for product in data.get('products', []):
            product_url = product.get('productUrl')
            if product_url:
                # Follow the link to the HTML product page
                yield response.follow(
                    f'https://www.cleverleben.at{product_url}',
                    callback=self.parse_product_details
                )

        # 4.2. Find the 'Next Page' for pagination
        pagination = data.get('pagination', {})
        current_page = pagination.get('page', 1)
        total_pages = pagination.get('totalPages', 1)

        if current_page < total_pages:
            # Build the URL for the next page
            next_page = current_page + 1
            # response.url already contains '?page=...'. We replace it.
            next_page_url = response.url.replace(
                f'page={current_page}', f'page={next_page}'
            )
            yield response.follow(next_page_url, callback=self.parse_product_list)

    # 5. This is the PARSER. Extract the final data from the HTML page.
    def parse_product_details(self, response):
        """
        This is the final parser. It's on a product detail page
        and extracts all 10 required data fields.
        
        The data is in a <script> tag as a JSON object. We will
        use XPath to find the script, then parse the JSON.
        """
        
        # This XPath finds the correct, large data script
        script_data = response.xpath(
            "//script[contains(., 'window.__NUXT__') and contains(., 'productDetail')]/text()"
        ).get()

        if not script_data:
            self.logger.error(f"Could not find __NUXT__ data on {response.url}")
            return

        # Clean the data (it starts with 'window.__NUXT__=' and ends with ';')
        json_string = script_data.split('window.__NUXT__=')[1].strip(';')
        
        try:
            # Parse the string as JSON
            nuxt_data = json.loads(json_string)
            
            # The product data is buried deep inside
            product = nuxt_data.get('data', [{}])[0].get('productDetail', {})

            if not product:
                self.logger.error(f"Could not find productDetail in JSON on {response.url}")
                return

            # --- All 10 fields are now filled in ---
            item = CleverlebenScraperItem()
            item['product_url'] = response.url
            item['product_name'] = product.get('name')
            item['price'] = product.get('price', {}).get('value')
            item['currency'] = product.get('price', {}).get('currencyIso')
            item['image'] = [img.get('url') for img in product.get('images', [])]
            item['product_description'] = product.get('description')
            item['unique_id'] = product.get('code')
            item['ingredients'] = product.get('ingredients')
            item['details'] = product.get('productInformation')
            item['product_id'] = product.get('code')
            # --- End of fields ---

            yield item

        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON on {response.url}")