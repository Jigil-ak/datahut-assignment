# This code follows PEP8 standards
import scrapy
from cleverleben_scraper.items import CleverlebenScraperItem


class CleverSpiderSpider(scrapy.Spider):
    """
    This spider crawls cleverleben.at to extract product data
    based on the Datahut assignment.
    """
    name = 'clever_spider'
    allowed_domains = ['cleverleben.at']

    def start_requests(self):
        """
        Starts the crawl from the main product selection page.
        """
        # 1. Start from the required Start URL 
        yield scrapy.Request(
            url='https://www.cleverleben.at/produktauswahl',
            callback=self.parse_main_categories
        )

    def parse_main_categories(self, response):
        """
        Parses the main categories page (Lebensmittel, Getränke, etc.)
        and follows their links. 
        """
        # 2. Find all category links
        # YOUR TASK: Find the XPath that selects the main category links
        category_links = response.xpath("...").getall()
        
        for link in category_links:
            yield response.follow(link, callback=self.parse_sub_categories)

    def parse_sub_categories(self, response):
        """
        Parses a main category page to find sub-categories
        (e.g., Brot & Backware). 
        If no sub-categories exist, it treats the page as a product list.
        """
        # 3. Find all sub-category links
        # YOUR TASK: Find the XPath for sub-category links
        subcategory_links = response.xpath("...").getall()

        if subcategory_links:
            # Found sub-categories, follow them
            for link in subcategory_links:
                yield response.follow(link, callback=self.parse_product_list)
        else:
            # No sub-categories found, this must be a product list page
            # We call the product list parser on the *current* response
            yield from self.parse_product_list(response)

    def parse_product_list(self, response):
        """
        Parses a product list page to find all product links 
        and finds the 'next page' link for pagination. 
        """
        # 4.1. Get all product URLs on the current page
        # YOUR TASK: Find the XPath for all the product links
        product_links = response.xpath("...").getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_product_details)

        # 4.2. Find the 'Next Page' link for pagination 
        # YOUR TASK: Find the XPath for the 'Next Page' button/link
        next_page = response.xpath("...").get()
        
        if next_page:
            yield response.follow(next_page, callback=self.parse_product_list)

    def parse_product_details(self, response):
        """
        This is the final parser. It's on a product detail page 
        and extracts all 10 required data fields. [cite: 161]
        """
        # Create a new item to fill with data
        item = CleverlebenScraperItem()

        # 5. Extract all data fields using XPath [cite: 21]
        # YOUR TASK: Fill in all the XPaths for the 10 items
        # Use the example PDF image as your guide! [cite: 109-153]

        item['product_url'] = response.url
        item['product_name'] = response.xpath("...").get()
        item['price'] = response.xpath("...").get()
        item['image'] = response.xpath("...").getall() # Use .getall() for images
        item['product_description'] = response.xpath("...").getall()
        item['unique_id'] = response.xpath("...").get()
        item.setdefault('ingredients', None) # Set a default for optional fields
        item['ingredients'] = response.xpath("...").get()
        item.setdefault('details', None) # Set a default for optional fields
        item['details'] = response.xpath("...").get()
        item['currency'] = response.xpath("...").get()
        item['product_id'] = response.xpath("...").get()

        yield item