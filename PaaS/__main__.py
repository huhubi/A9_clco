from datetime import datetime

import pulumi
from pulumi import Config, Output
from pulumi_azure_native import resources, network, cognitiveservices, web
import pulumi_azure_native as azure_native
from pulumi_random import random_string
import pulumi_azure_native.consumption as consumption

# Configuration variables
config = Config()
azure_location = config.get("azure-native:location") or "uksouth"

#defined_repo_url = config.get("my:repoUrl") or "https://github.com/huhubi/flaskwebapp"
defined_repo_url = config.get("my:repoUrl") or "https://github.com/huhubi/clco-demo/"
defined_branch = config.get("my:branch") or "main"
start = datetime(2024, 12, 1).strftime('%Y-%m-%dT%H:%M:%SZ')  # Startdatum: 1. November 2024
end = datetime(2025, 2, 28).strftime('%Y-%m-%dT%H:%M:%SZ')
mail_matthias ="wi22b112@technikum-wien.at"
mail_gregoire ="wi22b060@technikum-wien.at"
subscription_id = "5bb64e70-0225-40e2-b87c-ede62684f322"


# Resource Group
resource_group = resources.ResourceGroup('PaaSResourceGroup',
    resource_group_name='PaaSResourceGroup',
    location=azure_location
)

# Use random strings to give the Webapp unique DNS names
webapp_name_label1 = random_string.RandomString(
    "flaskwebapp-",  # Prefix for the random string
    length=8,  # Length of the random string
    upper=False,  # Use lowercase letters
    special=False,  # Do not use special characters
).result.apply(lambda result: f"{web_app}-{result}")  # Format the result with the web app name

# Virtual Network
virtual_network = network.VirtualNetwork('virtualNetwork',
    resource_group_name=resource_group.name,  # Name of the resource group
    location=azure_location,  # Location of the virtual network
    address_space=network.AddressSpaceArgs(
        address_prefixes=['10.0.0.0/16']  # Address space for the virtual network
    ),
    virtual_network_name='PaaSVNet'  # Name of the virtual network
)

# App Subnet
app_subnet = network.Subnet('applicationSubnet',
    resource_group_name=resource_group.name,  # Name of the resource group
    virtual_network_name=virtual_network.name,  # Name of the virtual network
    subnet_name='applicationSubnet',  # Name of the subnet
    address_prefix='10.0.0.0/24',  # Address prefix for the subnet
    delegations=[
        network.DelegationArgs(
            name='delegation',  # Name of the delegation
            service_name='Microsoft.Web/serverfarms',  # Service name for the delegation
        )
    ],
    private_endpoint_network_policies='Enabled'  # Enable network policies for private endpoints
)

# Endpoint Subnet
endpoint_subnet = network.Subnet('endpointSubnet',
    resource_group_name=resource_group.name,  # Name of the resource group
    virtual_network_name=virtual_network.name,  # Name of the virtual network
    subnet_name='endpointSubnet',  # Name of the subnet
    address_prefix='10.0.1.0/24',  # Address prefix for the subnet
    private_endpoint_network_policies='Disabled'  # Disable network policies for private endpoints
)

# Private DNS Zone
dns_zone = network.PrivateZone('dnsZone',
    resource_group_name=resource_group.name,  # Name of the resource group
    location='global',  # Location of the DNS zone
    private_zone_name='privatelink.cognitiveservices.azure.com'  # Name of the private DNS zone
)

# Cognitive Services Account
language_account = azure_native.cognitiveservices.Account(
    "languageAccount",
    resource_group_name=resource_group.name,  # Name of the resource group
    account_name="PaaSLanguageServiceProject",  # Name of the Cognitive Services account
    location=azure_location,  # Location of the account
    kind="TextAnalytics",  # Type of the Cognitive Services account
    sku=azure_native.cognitiveservices.SkuArgs(
        name="F0"  # SKU name
    ),
    properties=azure_native.cognitiveservices.AccountPropertiesArgs(
        public_network_access="Disabled",  # Disable public network access
        custom_sub_domain_name="PaaSLanguageServiceProject",  # Custom sub-domain name
        restore=True  # Restore the account (remark: for new deployment comment this line)
    ),
    identity=azure_native.cognitiveservices.IdentityArgs(
        type="SystemAssigned"  # Use system-assigned identity
    )
)
"""
HOWTO Access API from Unix

connect to web ssh of https://paasflaskwebapp.scm.azurewebsites.net/webssh/host

curl -X POST "https://paaslanguageserviceproject.cognitiveservices.azure.com/text/analytics/v3.0/sentiment" \
-H "AZ_KEY" \
-H "Content-Type: application/json" \
-d '{
    "documents": [
        {"id": "1", "language": "en", "text": "Azure Cognitive Services is amazing!"}
    ]
}'

Response is in this case 
{"documents":[{"id":"1","sentiment":"positive","confidenceScores":{"positive":1.0,"neutral":0.0,"negative":0.0},"sentences":[{"sentiment":"positive","confidenceScores":{"positive":1.0,"neutral":0.0,"negative":0.0},"offset":0,"length":36,"text":"Azure Cognitive Services is amazing!"}],"warnings":[]}],"errors":[],"modelVersion":"2024-03-01
"""



# Get Account Keys
account_keys = cognitiveservices.list_account_keys_output(
    resource_group_name=resource_group.name,  # Name of the resource group
    account_name=language_account.name  # Name of the Cognitive Services account
)

# DNS Zone Virtual Network Link
dns_zone_vnet_link = network.VirtualNetworkLink('dnsZoneVirtualNetworkLink',
    resource_group_name=resource_group.name,  # Name of the resource group
    private_zone_name=dns_zone.name,  # Name of the private DNS zone
    location='global',  # Location of the DNS zone link
    virtual_network=network.SubResourceArgs(
        id=virtual_network.id  # ID of the virtual network
    ),
    registration_enabled=False,  # Disable registration
    virtual_network_link_name='cognitiveservices-zonelink'  # Name of the virtual network link
)
# Create a Private Endpoint for the Cognitive Services account
private_endpoint = network.PrivateEndpoint('privateEndpoint',
    resource_group_name=resource_group.name,  # Name of the resource group
    location=azure_location,  # Location of the private endpoint
    private_endpoint_name='languagePrivateEndpoint',  # Name of the private endpoint
    subnet=network.SubnetArgs(
        id=endpoint_subnet.id  # ID of the endpoint subnet
    ),
    # Functional Requirement 3 - Private endpoint for the Cognitive Services account is established.
    private_link_service_connections=[
        network.PrivateLinkServiceConnectionArgs(
            name='languageServiceConnection',  # Name of the private link service connection
            private_link_service_id=language_account.id,  # ID of the private link service
            group_ids=['account']  # Group IDs associated with the private link service
        )
    ]
)
# Private DNS Zone Group
private_dns_zone_group = network.PrivateDnsZoneGroup('privateDnsZoneGroup',
    resource_group_name=resource_group.name,  # Name of the resource group
    private_endpoint_name=private_endpoint.name,  # Name of the private endpoint
    private_dns_zone_group_name='languagePrivateDnsZoneGroup',  # Name of the Private DNS Zone Group
    private_dns_zone_configs=[
        network.PrivateDnsZoneConfigArgs(
            name='config',  # Configuration name
            private_dns_zone_id=dns_zone.id  # ID of the private DNS zone
        )
    ]
)

# App Service Plan
app_service_plan = web.AppServicePlan('appServicePlan',
    resource_group_name=resource_group.name,
    name='myWebApp-plan',
    location=azure_location,
    sku=web.SkuDescriptionArgs(
        name='B1',
        tier='Basic',
        capacity=3 # Set the capacity to 3
        #Verify command: az webapp list-instances --resource-group PaaSResourceGroup --name PaaSflaskwebapp
    ),
    kind='linux',
    reserved=True
)

# Web App
web_app = web.WebApp('webApp',
    resource_group_name=resource_group.name,  # Name of the resource group
    name="PaaSflaskwebapp",  # Name of the web app
    location=azure_location,  # Location of the web app
    server_farm_id=app_service_plan.id,  # ID of the associated App Service Plan
    https_only=True,  # Enforce HTTPS-only traffic
    kind='app,linux',  # Type of the web app
    site_config=web.SiteConfigArgs(
        linux_fx_version='PYTHON|3.9',  # Runtime stack for the web app
        app_settings=[
            web.NameValuePairArgs(
                name='AZ_ENDPOINT',  # Application setting for Azure endpoint
                value=pulumi.Output.concat("https://", language_account.name, ".cognitiveservices.azure.com/")
            ),
            web.NameValuePairArgs(
                name='AZ_KEY',  # Application setting for Azure key
                value=account_keys.key1
            ),
            web.NameValuePairArgs(
                name='WEBSITE_RUN_FROM_PACKAGE',  # Application setting to run from package
                value='0'
            ),
        ],
        always_on=True,  # Keep the web app always on
        ftps_state='Disabled'  # Disable FTPS
    )
)

# VNet Integration
vnet_integration = web.WebAppSwiftVirtualNetworkConnection('vnetIntegration',
    name=web_app.name,
    resource_group_name=resource_group.name,
    subnet_resource_id=app_subnet.id
)

source_control = azure_native.web.WebAppSourceControl("sourceControl",
    name=web_app.name,
    resource_group_name=resource_group.name,
    repo_url=defined_repo_url,  # Replace with your repository URL
    branch=defined_branch,  # Replace with your branch name
    is_manual_integration=True,
    deployment_rollback_enabled=False
)
# Create a budget for the specified resource group
budget = resource_group.name.apply(lambda rg_name: consumption.Budget(
    resource_name="PaaS-Budget",  # Name of the budget resource
    scope=f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}",  # Scope limited to the resource group
    amount=50,  # Budget amount
    time_grain="Monthly",  # Budget reset interval
    time_period={
        "startDate": start,  # Start date of the budget
        "endDate": end,  # End date of the budget
    },
    notifications={
        "Actual2Percent": {  # Notification when 2% of the budget is reached
            "enabled": True,
            "operator": "GreaterThan",  # Condition: Budget exceeded
            "threshold": 2,  # 2% of the budget
            "contact_emails": [mail_matthias, mail_gregoire],  # Email addresses for notifications
            "contact_roles": [],  # No specific roles
            "notification_language": "en-US",  # Notification language
        },
        "Actual50Percent": {  # Notification when 50% of the budget is reached
            "enabled": True,
            "operator": "GreaterThan",
            "threshold": 50,  # 50% of the budget
            "contact_emails": [mail_matthias, mail_gregoire],
            "contact_roles": [],
            "notification_language": "en-US",
        },
    },
    category="Cost",  # Budget category for cost monitoring
))


# Export the Web App hostname as a Markdown link
pulumi.export("hostname", pulumi.Output.concat("[Web App](http://", web_app.default_host_name, ")"))