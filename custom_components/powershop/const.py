"""Constants for Powershop integration."""

DOMAIN = "powershop"

# Configuration keys
CONF_EMAIL = "email"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ACCOUNT_NUMBER = "account_number"
CONF_PROPERTY_ID = "property_id"

# Production Firebase config (public values embedded in app bundle)
FIREBASE_API_KEY = "AIzaSyCYCKXQhGmo7haJxAAyO_7mIPrV7jtxsK8" # used for custom token exchange to get Firebase ID token for Powershop API auth
FIREBASE_SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
FIREBASE_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"

# Powershop auth + API endpoints
EMAIL_CONNECTOR_URL = "https://auth.powershop.nz/cf/email-connector"
OTP_VALIDATOR_URL = "https://auth.powershop.nz/cf/email-otp-authenticator"
GRAPHQL_URL = "https://api.powershop.nz/v1/graphql/"
BRAND = "powershop"  # used in auth endpoint payloads
BRAND_GQL = "POWERSHOP"  # GraphQL BrandChoices enum value