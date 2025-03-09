import json

def clean_and_flatten_review_data(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            reviews_data = json.load(file)

        if not reviews_data:
            print("Input file is empty or has no data.")
            return
        
        for product in reviews_data:
            product_name = product.get("product_name")
            product_rating = float(product.get("product_rating", 0))
            ratings_count = int(product.get("ratings_count", 0))
            reviews_count = int(product.get("reviews_count", 0))
            reviews = []
            
            # Extract and clean star ratings
            star_ratings = product.get("star_ratings", {})
            cleaned_star_ratings = {
                "5 star": int(star_ratings.get("5 star", 0)),
                "4 star": int(star_ratings.get("4 star", 0)),
                "3 star": int(star_ratings.get("3 star", 0)),
                "2 star": int(star_ratings.get("2 star", 0)),
                "1 star": int(star_ratings.get("1 star", 0))
            }
            
            # Check if reviews exist
            if 'reviews' in product and product['reviews']:
                for review in product.get('reviews', []):
                    flattened_review = {
                        "review_rating": int(review.get("rating", 0)),  # Default to 0 if not found
                        "review_heading": review.get("heading", ""),  # Default to empty string
                        "review_body": review.get("body", "")  # Default to empty string
                    }
                    reviews.append(flattened_review)

            # Create the cleaned product entry with flattened reviews
            cleaned_product = {
                "product_name": product_name,
                "product_rating": product_rating,
                "ratings_count": ratings_count,
                "reviews_count": reviews_count,
                "star_ratings": cleaned_star_ratings,
                "reviews": reviews  # Add flattened reviews here
            }

        # Check if any products were processed
        if not cleaned_product:
            print("No products found to clean.")
            return

        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump(cleaned_product, outfile, ensure_ascii=False, indent=4)

        print(f"Cleaned and flattened data saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    clean_and_flatten_review_data('flipkart_reviews_output.json', 'cleaned_reviews_output.json')
