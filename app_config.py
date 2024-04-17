import os

b2c_tenant = "acblueprint"
signupsignin_user_flow = "B2C_1_signupsignin1_mfa"
editprofile_user_flow = "B2C_1_profileediting1"

resetpassword_user_flow = "B2C_1_passwordreset1"  # Note: Legacy setting.

authority_template = "https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{user_flow}"

# CLIENT_ID = "b21e87b3-d133-44cf-a043-3d5886e86f17" # Application (client) ID of app registration

# CLIENT_SECRET = "nCc8Q~QQxVOx~Su9PBw2pB1QaKxPV6gOYxghsbEw" # Application secret.

# AUTHORITY = authority_template.format(
#     tenant=b2c_tenant, user_flow=signupsignin_user_flow)
B2C_PROFILE_AUTHORITY = authority_template.format(
    tenant=b2c_tenant, user_flow=editprofile_user_flow)

B2C_RESET_PASSWORD_AUTHORITY = authority_template.format(
    tenant=b2c_tenant, user_flow=resetpassword_user_flow)

REDIRECT_PATH = "/auth/redirect"

# This is the API resource endpoint
ENDPOINT = 'https://acblueprint.onmicrosoft.com/b21e87b3-d133-44cf-a043-3d5886e86f17' # Application ID URI of app registration in Azure portal

# These are the scopes you've exposed in the web API app registration in the Azure portal
SCOPE = ["https://acblueprint.onmicrosoft.com/b21e87b3-d133-44cf-a043-3d5886e86f17/Files.write", "https://acblueprint.onmicrosoft.com/b21e87b3-d133-44cf-a043-3d5886e86f17/Files.read"]  # Example with two exposed scopes: ["demo.read", "demo.write"]

SESSION_TYPE = "filesystem"  # Specifies the token cache should be stored in server-side session