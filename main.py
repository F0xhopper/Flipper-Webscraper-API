from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/scrape*": {"origins": "*"}})

def scrape_sold_listings(item_name):
    # Setup Chrome webdriver with Selenium
    options = Options()
    options.headless = True  # Run in headless mode for API
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument('--window-size=1280x1024')

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')
    # Ensure ChromeDriver is in your PATH
    service = Service()  
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Navigate to eBay's sold listings page
        driver.get(f"https://www.ebay.co.uk/sch/i.html?_nkw={item_name}&_ipg=200&_sop=12")

        # Wait for the page to load
        time.sleep(2)  # You can adjust the waiting time as necessary

        # Accept GDPR banner if present
    
        gdpr_banner_accept_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept all')]")
        gdpr_banner_accept_button.click()
        time.sleep(2)
      

        # Click on the "Sold Items" filter
        sold_filter = driver.find_element(By.XPATH, "//span[contains(text(), 'Sold items')]")
        sold_filter.click()

        # Wait for the sold listings to load
        time.sleep(2)  # Adjust as necessary

        auction_filter = driver.find_element(By.CSS_SELECTOR, '.fake-tabs__item > a')
        auction_filter.click()

        # Extract sold listings data
        time.sleep(1)
        sold_listings = driver.find_elements(By.CSS_SELECTOR, "#srp-river-results > ul > .s-item__pl-on-bottom")

        listings_data = []
        for listing in sold_listings:
            try:
                date_element = listing.find_element(By.CLASS_NAME, "s-item__caption--row")
                date = date_element.text.strip()
                price_element = listing.find_element(By.CLASS_NAME, "s-item__price")
                price_element = price_element.text.strip()  # Example price element text
                price = price_element.lstrip('£')  # Remove the pound sign from the start
                price = price.replace(',', '') 
                price = float(price) 
                # Price
                title_element = listing.find_element(By.CLASS_NAME, "s-item__link")
                title = title_element.text.strip()
                href = title_element.get_attribute('href')

                image_elememt = listing.find_element(By.CSS_SELECTOR, '.s-item__image-wrapper > img')
                image = image_elememt.get_attribute('src')
               

                listing_data = {
                    'title': title,
                    'price': price,
                    'soldDate': date,
                    'url': href,
                    'imageUrl': image
                }
                listings_data.append(listing_data)
                print(listing_data)

                if len(listings_data) >= 150:
                    break
            except Exception as e:
                print(f"Error processing a listing: {e}")
                continue

        return listings_data
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

    finally:
        driver.quit()

@app.route('/scrape', methods=['GET'])
def scrape():
    item_to_search = request.args.get('item')
    if not item_to_search:
        return jsonify({'error': 'No item specified'}), 400
    
    listings = scrape_sold_listings(item_to_search)
    return jsonify(listings)

if __name__ == '__main__':
    app.run(debug=True)