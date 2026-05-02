import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:earl@localhost/hotel_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JAVA_RECEIPT_URL = 'http://localhost:8080/receipt'

    # Email configuration (for verification)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'salvadorearl8@gmail.com'          # Replace with your Gmail
    MAIL_PASSWORD = 'vrvczfhnxmimnwmu'             # Replace with your app password
    MAIL_DEFAULT_SENDER = 'salvadorearl8@gmail.com'

# PayMongo Configuration
PAYMONGO_SECRET_KEY = 'sk_test_xxxxx'   # replace with your actual secret key
PAYMONGO_PUBLIC_KEY = 'pk_test_xxxxx'   # replace if needed
PAYMONGO_WEBHOOK_SECRET = 'whsec_xxxxx' # if you set a webhook secret