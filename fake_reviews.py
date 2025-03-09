import pandas as pd
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from nltk.corpus import stopwords
import spacy
import random
from scipy.stats import iqr,zscore,skew
from sklearn.neighbors import LocalOutlierFactor

# Load SpaCy model for English
nlp = spacy.load('en_core_web_sm')

# Download necessary NLTK resources
nltk.download('vader_lexicon', quiet=True)
nltk.download('stopwords', quiet=True)

# Load stopwords once
stop_words = set(stopwords.words('english'))

# Function to read data from JSON file
def load_reviews_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# Text preprocessing function using SpaCy
def preprocess_text(text):
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if token.is_alpha and token.text not in stop_words]
    return ' '.join(tokens)

# Modified function for sentiment analysis using threading
def analyze_sentiment_threaded(reviews):
    sia = SentimentIntensityAnalyzer()
    with ThreadPoolExecutor() as executor:
        sentiment_scores = list(executor.map(lambda review: sia.polarity_scores(review)['compound'], reviews))
    return sentiment_scores

def calculate_contamination_factor(features):
    skew_set = random.uniform(0,0.2)
    contamination_factors = []

    # Adaptive Z-Score Threshold based on Skewness
    def adaptive_z_threshold(feature):
        # Calculate skewness of the feature
        feature_skewness = skew(feature)
        if abs(feature_skewness) > 1:  # If skew is high, use a stricter threshold
            return 2  # Stricter threshold for highly skewed features
        else:
            return 3  # Standard threshold for normally distributed features

    # Outlier Detection Using IQR and Z-scores
    for feature in features.T:
        feature_iqr = iqr(feature)
        if feature_iqr != 0:  # Avoid division by zero
            # Calculate IQR-based outlier contamination
            lower_bound = np.percentile(feature, 25) - 0.75 * feature_iqr
            upper_bound = np.percentile(feature, 75) + 0.75 * feature_iqr
            iqr_outliers = np.sum((feature < lower_bound) | (feature > upper_bound)) / len(feature)
            contamination_factors.append(iqr_outliers)

        # Calculate contamination using Z-scores with adaptive threshold
        z_threshold = adaptive_z_threshold(feature)
        z_scores = np.abs(zscore(feature))
        z_outliers = np.sum(z_scores > z_threshold) / len(feature)
        contamination_factors.append(z_outliers + skew_set)

    # Density-Based Outlier Detection Using LOF
    lof = LocalOutlierFactor(n_neighbors=20, contamination=contamination_factors[-1])
    lof_outliers = lof.fit_predict(features)
    lof_outliers_fraction = np.sum(lof_outliers == -1) / len(lof_outliers)  # -1 indicates an outlier
    contamination_factors.append(lof_outliers_fraction + skew_set)

    # Calculate the average contamination factor from all methods
    contamination_factor = np.mean(contamination_factors)
    
    # Apply a dynamic minimum threshold to avoid zero contamination
    contamination_factor = max(contamination_factor, 0.05)  # Minimum threshold to avoid zero contamination

    return contamination_factor

# Function to analyze reviews for any product category
def analyze_reviews(file_path):
    data = load_reviews_from_json(file_path)
    reviews_df = pd.DataFrame(data['reviews'])

    # Preprocess review text concurrently for speed
    with ThreadPoolExecutor() as executor:
        cleaned_reviews = list(executor.map(preprocess_text, reviews_df['review_body']))
    reviews_df['cleaned_review'] = cleaned_reviews

    # Analyze sentiment concurrently
    sentiment_scores = analyze_sentiment_threaded(reviews_df['cleaned_review'])
    reviews_df['sentiment'] = sentiment_scores

    # Add review length as a feature
    reviews_df['review_length'] = reviews_df['cleaned_review'].apply(len)

    # Prepare features for anomaly detection
    vectorizer = TfidfVectorizer(ngram_range=(1, 4))  # Adjusted n-gram range for balance between speed and accuracy
    review_vectors = vectorizer.fit_transform(reviews_df['cleaned_review'])
    features = np.hstack((reviews_df[['review_rating', 'sentiment', 'review_length']].values, review_vectors.toarray()))

    # Scale numerical features
    scaler = StandardScaler()
    features[:, :3] = scaler.fit_transform(features[:, :3])
    
    contamination_factor = calculate_contamination_factor(features)
    
    # Function to detect anomalies using Isolation Forest
    def detect_anomalies(features):
        model = IsolationForest(contamination=contamination_factor, random_state=42, n_estimators=500, max_samples='auto', bootstrap=True)
        model.fit(features)
        return model.predict(features)

    # Detect anomalies
    anomalies = detect_anomalies(features)
    reviews_df['anomaly'] = anomalies

    # Identify fake reviews
    suspected_fake_reviews = reviews_df[reviews_df['anomaly'] == -1]

    # Calculate total reviews and suspected fake reviews
    total_reviews = len(reviews_df)
    fake_reviews_count = len(suspected_fake_reviews)
    fake_reviews_percentage = (fake_reviews_count / total_reviews) * 100 if total_reviews > 0 else 0

    # Write suspected fake reviews to a JSON file
    suspected_fake_reviews_output_file = 'suspected_fake_reviews_output.json'
    suspected_fake_reviews[['review_body', 'review_rating', 'sentiment']].to_json(
        suspected_fake_reviews_output_file, 
        orient='records', 
        lines=False,
        indent=4
    )

    print(f"{fake_reviews_percentage:.2f}")

# Example usage with the path to your JSON file
analyze_reviews('cleaned_reviews_output.json')
