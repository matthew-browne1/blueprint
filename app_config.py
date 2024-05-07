import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.client import Redis
from redis.exceptions import (
    BusyLoadingError,
    ConnectionError,
    TimeoutError
)


keyvault_url = "https://acblueprint-vault.vault.azure.net/"
credential = DefaultAzureCredential(managed_identity_client_id='e80b105d-e738-49e0-93be-6fda83ee5301')
secret_client = SecretClient(vault_url=keyvault_url, credential=credential)

CLIENT_ID = secret_client.get_secret("CLIENT-ID").value
CLIENT_SECRET = secret_client.get_secret("CLIENT-SECRET").value
authority = secret_client.get_secret("authority").value

DB_USERNAME = secret_client.get_secret("db-username").value
DB_PASSWORD = secret_client.get_secret("db-password").value

redis_pw = secret_client.get_secret("REDIS-PASSWORD").value
redis_url = secret_client.get_secret("REDIS-URL").value

retry = Retry(ExponentialBackoff(), 3)
SESSION_REDIS = Redis.from_url(redis_url)

b2c_tenant = "acblueprint"
signupsignin_user_flow = "B2C_1_BP_STANDARD_USER_SIGN_IN"
editprofile_user_flow = "B2C_1_profileediting1"

resetpassword_user_flow = "B2C_1_passwordreset1"  # Note: Legacy setting.

authority_template = "{authority}/{user_flow}"

AUTHORITY = authority_template.format(
    authority=authority, user_flow=signupsignin_user_flow)
B2C_PROFILE_AUTHORITY = authority_template.format(
    authority=authority, user_flow=editprofile_user_flow)

B2C_RESET_PASSWORD_AUTHORITY = authority_template.format(
    authority=authority, user_flow=resetpassword_user_flow)

REDIRECT_PATH = "/auth/redirect"

# This is the API resource endpoint
ENDPOINT = 'https://acblueprint.onmicrosoft.com/b21e87b3-d133-44cf-a043-3d5886e86f17' # Application ID URI of app registration in Azure portal

# These are the scopes you've exposed in the web API app registration in the Azure portal
SCOPE = ["https://acblueprint.onmicrosoft.com/b21e87b3-d133-44cf-a043-3d5886e86f17/Files.write", "https://acblueprint.onmicrosoft.com/b21e87b3-d133-44cf-a043-3d5886e86f17/Files.read"]  # Example with two exposed scopes: ["demo.read", "demo.write"]

SESSION_TYPE = "redis"  # Specifies the token cache should be stored in server-side session