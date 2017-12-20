""" Keys and passwords
Add to server's env var
The default value is for local dev only, do not commit or expose them
"""
import os

# Email and username here, to be used to send emails from via SMTP
EMAIL = {
    'USERNAME': os.getenv('SECRET_EMAIL_USERNAME', ''),
    'PASSWORD': os.getenv('SECRET_EMAIL_PASSWORD', ''),
}

# Binance APIKEY and APISECRET here
BINANCE = {
    'API_KEY': os.getenv('SECRET_BI_APIKEY', ''),
    'API_SECRET': os.getenv('SECRET_BI_APISECRET', '')
}