import scrapy

class CleverlebenItem(scrapy.Item):
    # Required fields from the PDF
    product_url = scrapy.Field()
    product_name = scrapy.Field()
    price = scrapy.Field()
    image = scrapy.Field()  # This will be a list
    product_description = scrapy.Field()
    unique_id = scrapy.Field()
    ingredients = scrapy.Field()
    details = scrapy.Field()
    currency = scrapy.Field()
    product_id = scrapy.Field()