import re

class CleverlebenScraperPipeline:
    def process_item(self, item, spider):
        # Clean all string fields
        for field in ['product_name', 'product_description', 'ingredients', 'details']:
            if field in item and item[field]:
                item[field] = self.clean_text(item[field])
        
        # Clean price field
        if 'price' in item and item['price']:
            item['price'] = self.clean_price(item['price'])
        
        # Ensure unique_id is present
        if not item.get('unique_id'):
            # Extract from URL as fallback
            url = item.get('product_url', '')
            match = re.search(r'(\d+)(?=[^/]*$)', url)
            if match:
                item['unique_id'] = match.group(1)
        
        # Ensure product_id is present
        if not item.get('product_id'):
            item['product_id'] = item.get('unique_id', '')
        
        return item
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if isinstance(text, str):
            # Remove extra whitespace
            text = ' '.join(text.split())
            # Remove special characters but keep essential ones
            text = re.sub(r'[^\w\s€.,!?%-]', '', text)
        return text
    
    def clean_price(self, price):
        """Clean price string"""
        if isinstance(price, str):
            # Extract numbers and decimals
            price_match = re.search(r'(\d+[.,]\d+|\d+)', price)
            if price_match:
                clean_price = price_match.group(1)
                # Replace comma with dot for decimal
                clean_price = clean_price.replace(',', '.')
                return clean_price
        return price