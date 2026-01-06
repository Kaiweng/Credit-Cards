import os
import sys

print(f"Current Working Directory: {os.getcwd()}")
print(f"Script Location (__file__): {__file__}")
print(f"Dirname of __file__: {os.path.dirname(__file__)}")

scraper_path = os.path.join(os.path.dirname(__file__), "bank_offers_scraper.py")
print(f"Calculated Scraper Path: {scraper_path}")

if os.path.exists(scraper_path):
    print("SUCCESS: bank_offers_scraper.py found at calculated path.")
else:
    print("FAILURE: bank_offers_scraper.py NOT found.")
