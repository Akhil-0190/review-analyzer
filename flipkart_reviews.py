import scrapy
from scrapy.crawler import CrawlerProcess
import sys
import json

class FlipkartReviewsSpider(scrapy.Spider):
    name = "flipkart_reviews"
    
    def __init__(self, review_link, *args, **kwargs):
        super(FlipkartReviewsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [review_link]
        self.product_reviews = {'reviews': [], 'star_ratings': {}}

    def parse(self, response):
        # Extract product name and details from the page
        product_name = response.css('div.Vu3-9u.eCtPz5::text').get().strip()
        
        product_rating = response.css('div.ipqd2A::text').get().strip()
        
        # Initialize counts
        ratings_count = None
        reviews_count = None
        
        # Extract ratings count
        ratings_text = response.xpath('//div[@class="row j-aW8Z"][1]/div[@class="col-12-12"]/span/text()').get()
        if ratings_text and 'Ratings' in ratings_text:
            ratings_count = ratings_text.split(' ')[0].replace(',', '')

        # Extract reviews count
        reviews_text = response.xpath('//div[@class="row j-aW8Z"][2]/div[@class="col-12-12"]/span/text()').get()
        if reviews_text and 'Reviews' in reviews_text:
            reviews_count = reviews_text.split(' ')[0].replace(',', '')

        # Extract reviews
        reviews_container = response.css('body > div#container > div > div.VLIitu > div.JxFEK3._48O0EI > div.DOjaWF.YJG4Cf.col-12-12 > div.DOjaWF.gdgoEp.col-9-12 > div.cPHDOP.col-12-12 > div.EKFha- > div.col > div.col.EPCmJX.Ma1fCG')

        for review in reviews_container:
            # Extract review rating
            review_rating = review.css('div.row div.XQDdHH.Ga3i8K::text').get()

            # Extract review heading
            review_heading = review.css('div.row > p.z9E0IG::text').get()

            # Extract review body
            review_body = review.css('div.ZmyHeo > div > div::text').getall()
            review_body_cleaned = ' '.join(review_body).strip()

            # Store review data
            self.product_reviews['reviews'].append({
                'rating': review_rating.strip() if review_rating else None,
                'heading': review_heading.strip() if review_heading else None,
                'body': review_body_cleaned,  # Store the cleaned body text
            })

        # Extract star ratings counts
        star_ratings_container = response.css('div.BArk-j')

        # Extract star ratings counts using a list comprehension
        star_ratings_counts = [star_rating.css('div.BArk-j::text').get().replace(',', '') for star_rating in star_ratings_container]

        # Create star keys and store counts in the dictionary
        for i, count in enumerate(star_ratings_counts):
            star_key = f"{5 - i} star"
            self.product_reviews['star_ratings'][star_key] = int(count)
            
        # Check if there's a next page and follow the link if it exists
        next_page_link = response.css('nav.WSL9JP a._9QVEpD:contains("Next")::attr(href)').get()

        if next_page_link:
            next_page_url = response.urljoin(next_page_link)
            yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            # Once all reviews are scraped, save the product details
            self.product_reviews['product_name'] = product_name
            self.product_reviews['product_rating'] = product_rating
            self.product_reviews['ratings_count'] = ratings_count
            self.product_reviews['reviews_count'] = reviews_count

            yield {
                'product_name': self.product_reviews['product_name'],
                'product_rating':self.product_reviews['product_rating'],
                'ratings_count':self.product_reviews['ratings_count'],
                'reviews_count':self.product_reviews['reviews_count'],
                'reviews': self.product_reviews['reviews'],
                'star_ratings': self.product_reviews['star_ratings']
            }

# Function to run the Scrapy spider
def run_reviews_spider(review_link):
    process = CrawlerProcess(settings={
        "FEEDS": {
            "flipkart_reviews_output.json": {
                "format": "json",
                "encoding": "utf8",
                "overwrite": True,
            },
        },
    })

    process.crawl(FlipkartReviewsSpider, review_link=review_link)
    process.start()

# Main execution
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python flipkart_reviews.py <review_page_link>")
        sys.exit(1)

    review_link = sys.argv[1]
    run_reviews_spider(review_link)
