import scrapy

class CleverlebenScraperItem(scrapy.Item):
    
    """ Defines the data fields to be scraped, based on the assignment PDF. """
    
    product_url = scrapy.Field()
    product_name = scrapy.Field()
    price = scrapy.Field()
    image = scrapy.Field()
    product_description = scrapy.Field()
    unique_id = scrapy.Field()
    ingredients = scrapy.Field()
    details = scrapy.Field()
    currency = scrapy.Field()
    product_id = scrapy.Field()