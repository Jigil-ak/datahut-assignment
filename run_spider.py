#!/usr/bin/env python3
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os
import json
import pandas as pd
from datetime import datetime
import sys

def run_spider():
    print("Setting up Cleverleben spider...")
    
    # Configure settings
    settings = get_project_settings()
    
    # Set output files
    json_file = 'output_data.json'
    csv_file = 'output_data.csv'
    
    # Remove existing files
    for file in [json_file, csv_file]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed existing {file}")
    
    # Configure feed exports
    settings.set('FEED_URI', json_file)
    settings.set('FEED_FORMAT', 'jsonlines')
    settings.set('FEED_EXPORT_ENCODING', 'utf-8')
    
    process = CrawlerProcess(settings)
    
    print("Starting Cleverleben spider...")
    print("This may take a while as we need to extract 1000+ products...")
    
    try:
        process.crawl('clever_spider')
        process.start()
        
        # Check results after spider finishes
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f)
            print(f"Final count: {line_count} items")
            
            # Convert to CSV
            if line_count > 0:
                data = []
                with open(json_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
                
                df = pd.DataFrame(data)
                df.to_csv(csv_file, index=False, encoding='utf-8')
                print(f"✓ Successfully processed {len(data)} items")
                print(f"✓ JSON file: {json_file}")
                print(f"✓ CSV file: {csv_file}")
                
                if len(data) < 1000:
                    print(f"⚠ Only {len(data)} items extracted. Need at least 1000.")
                else:
                    print(f"🎉 Success: {len(data)} items extracted!")
                    
        else:
            print("❌ No output file created")
            
    except Exception as e:
        print(f"❌ Spider execution failed: {e}")

if __name__ == "__main__":
    print("Cleverleben Data Scraper")
    print("=" * 50)
    run_spider()