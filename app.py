import streamlit as st
import numpy as np
import pickle
import requests
from urllib.parse import urlparse
from datetime import datetime
import re
from requests.exceptions import SSLError, Timeout
import ipaddress

def get_domain(url):  
    domain = urlparse(url).netloc
    if domain.startswith("www."):
        domain = domain.replace("www.", "")
    return domain

def having_ip(url):
    try:
        ipaddress.ip_address(url)
        return 1
    except ValueError:
        return 0

def have_at_sign(url):
    return 1 if "@" in url else 0

def get_length(url):
    return 1 if len(url) >= 54 else 0

def get_depth(url):
    return len([segment for segment in urlparse(url).path.split('/') if segment])

def redirection(url):
    return 1 if url.rfind('//') > 6 else 0

def http_domain(url):
    return 1 if 'https' in urlparse(url).netloc else 0

def tiny_url(url):
    shortening_services = r"bit\.ly|goo\.gl|tinyurl|t\.co|is\.gd|ow\.ly|buff\.ly"
    return 1 if re.search(shortening_services, url) else 0

def prefix_suffix(url):
    return 1 if '-' in urlparse(url).netloc else 0

def web_traffic(url):
    try:
        response = requests.get(f"https://www.alexa.com/siteinfo/{url}", timeout=5)
        return 1 if response.status_code == 200 else 0
    except requests.RequestException:
        return 0

def iframe(response):
    return 0 if response and re.findall(r"<iframe>|<frameBorder>", response.text) else 1

def mouse_over(response):
    return 1 if response and re.findall(r"<script>.+onmouseover.+</script>", response.text) else 0

def right_click(response):
    return 0 if response and re.findall(r"event.button ?== ?2", response.text) else 1

def forwarding(response):
    return 1 if response and len(response.history) > 2 else 0

def get_http_response(url):
    try:
        return requests.get(url, timeout=5)
    except requests.RequestException:
        return None

def extract_features(url):
    features = [
        having_ip(url),
        have_at_sign(url),
        get_length(url),
        get_depth(url),
        redirection(url),
        http_domain(url),
        tiny_url(url),
        prefix_suffix(url),
        0, 0, 0,  # Placeholder for domain-based features
        web_traffic(url)
    ]
    response = get_http_response(url)
    features.extend([
        iframe(response),
        mouse_over(response),
        right_click(response),
        forwarding(response)
    ])
    return features

def predict_phishing(features):
    with open('mlp_model.pkl', 'rb') as file:
        model = pickle.load(file)
    return model.predict([features])[0]

def main():
    st.title('Phishing URL Detector')
    st.write("Enter a URL to check if it's phishing or not.")
    
    url = st.text_input("Enter URL:")
    if st.button("Check"):
        if url:
            st.write("Extracting features...")
            features = extract_features(url)
            
            st.write("Predicting...")
            prediction = predict_phishing(features)
            
            if prediction == 1:
                st.error("Phishing Alert! This URL is classified as phishing.")
            else:
                st.success("No Phishing Detected. This URL seems safe.")
        else:
            st.warning("Please enter a valid URL.")
    
if __name__ == '__main__':
    main()
