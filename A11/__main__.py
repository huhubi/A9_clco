import pulumi
from pulumi_azure_native import compute, network, resources
from pulumi_random import random_string

# Configuration
config = pulumi.Config()
vm_name = config.get("vm1", "my-server1")
vm_size = config.get("vmSize", "Standard_B2ts_v2")
os_image = config.get("osImage", "Debian:debian-11:11:latest")
admin_username = config.get("azureuser", "pulumiuser")
admin_password = config.require("adminPassword")  # in fact not needeed since port 22 ist disabled
service_port = config.get("servicePort", "80")

# Generate a unique domain name label
random_label = random_string.RandomString(
    "domain-label",
    length=8,
    upper=False,
    special=False,
).result

domain_name_label = random_label.apply(lambda result: f"{vm_name}-{result}")

# Create a resource group
resource_group = resources.ResourceGroup("resourcegroup", location="uksouth")

# Create a virtual network and subnet
vnet = network.VirtualNetwork(
    "vnet",
    resource_group_name=resource_group.name,
    address_space={"address_prefixes": ["10.0.0.0/16"]},
    subnets=[{
        "name": f"{vm_name}-subnet",
        "address_prefix": "10.0.1.0/24",
    }],
)

# Create a network security group with an HTTP rule
security_group = network.NetworkSecurityGroup(
    "http-nsg",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    security_rules=[{
        "name": "allow-http",
        "priority": 100,
        "direction": "Inbound",
        "access": "Allow",
        "protocol": "Tcp",
        "source_port_range": "*",
        "destination_port_range": "80",
        "source_address_prefix": "*",
        "destination_address_prefix": "*",
    }],
)

# Create a public IP address
public_ip = network.PublicIPAddress(
    "public-ip",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    public_ip_allocation_method="Dynamic",
    dns_settings={"domain_name_label": domain_name_label},
)

# Create a network interface
nic = network.NetworkInterface(
    "nic",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    network_security_group={"id": security_group.id},
    ip_configurations=[{
        "name": "ipconfig1",
        "private_ip_allocation_method": "Dynamic",
        "subnet": {"id": vnet.subnets.apply(lambda subnets: subnets[0].id)},
        "public_ip_address": {"id": public_ip.id},
    }],
)

# Create a virtual machine
vm = compute.VirtualMachine(
    "vm",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    vm_name=vm_name,
    hardware_profile=compute.HardwareProfileArgs(vm_size=vm_size),
    storage_profile=compute.StorageProfileArgs(
        os_disk=compute.OSDiskArgs(
            create_option="FromImage"
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher="Canonical",
            offer="0001-com-ubuntu-server-jammy",
            sku="22_04-lts",
            version="latest"
        ),
    ),
    os_profile=compute.OSProfileArgs(
        computer_name=vm_name,
        admin_username=admin_username,
        admin_password=admin_password,
    ),
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[compute.NetworkInterfaceReferenceArgs(
            id=nic.id
        )],
    ),
)

# Add a VM extension to install Nginx and configure the web server
vm_extension = compute.VirtualMachineExtension(
    "vm-extension",
    resource_group_name=resource_group.name,
    vm_name=vm.name,
    publisher="Microsoft.Azure.Extensions",
    type="CustomScript",
    type_handler_version="2.1",
    auto_upgrade_minor_version=True,
    settings={
        "commandToExecute": "sudo apt-get update && sudo apt-get install -y nginx && "
                             "echo '<head><title>Hello World</title></head><body><h1>Web Portal</h1><p>Hello World</p></body>' "
                             "| sudo tee /var/www/html/index.nginx-debian.html && sudo systemctl restart nginx"
    },
)

# Export the public IP address
public_ip.ip_address.apply(lambda ip: print(f'Public IP Address: {ip}'))
