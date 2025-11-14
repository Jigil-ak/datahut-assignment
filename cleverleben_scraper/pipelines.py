# This code follows PEP8 standards
import re

class CleverlebenScraperPipeline:
    """
    This pipeline cleans the data for each item.
    - Cleans product_description to remove extra whitespace.
    - Converts price from string to a float.
    - Ensures image is a list.
    """

    def process_item(self, item, spider):
        
        # --- Clean product_description ---
        # It's a string, so we can clean it.
        description = item.get('product_description')
        if description:
            # Join all parts (if it's a list) and strip whitespace
            clean_desc = " ".join(str(description).split()).strip()
            item['product_description'] = clean_desc

        # --- Clean Price ---
        # The API gives price as a number (e.g., 2.49), so it's good.
        # But if it were a string "2,49", we would clean it like this:
        price = item.get('price')
        if price:
            try:
                # Convert price to a floating-point number (decimal)
                item['price'] = float(price)
            except ValueError:
                # If conversion fails, keep the original
                pass 

        # --- Clean Image ---
        # The PDF requires 'image' to be a list [cite: 161]
        image_list = item.get('image')
        if image_list:
            # Our spider already makes it a list, but this is a good check.
            # We also remove any empty or null links from the list.
            item['image'] = [url for url in image_list if url]
        else:
            # If no image, set it to an empty list
            item['image'] = []

        return item