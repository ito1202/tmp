terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  # TODO: リモートステート（Azure Storage）に切り替える
  # backend "azurerm" {}
}

provider "azurerm" {
  features {}
}

# ============================================================
# リソースグループ
# ============================================================
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# ============================================================
# ネットワーク
# ============================================================
resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.resource_group_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = [var.vnet_address_space]
  tags                = var.tags
}

resource "azurerm_subnet" "app" {
  name                 = "subnet-app"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_app_prefix]

  delegation {
    name = "app-service-delegation"
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

# GatewaySubnet: 名前は Azure の仕様で固定
resource "azurerm_subnet" "gateway" {
  name                 = "GatewaySubnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_gateway_prefix]
}

# ============================================================
# NSG（ホワイトリスト）
# ============================================================
resource "azurerm_network_security_group" "app" {
  name                = "nsg-app"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags

  security_rule {
    name                       = "allow-onprem-https"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefixes    = var.allowed_ip_ranges
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "443"
  }

  security_rule {
    name                       = "deny-all-inbound"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "app" {
  subnet_id                 = azurerm_subnet.app.id
  network_security_group_id = azurerm_network_security_group.app.id
}

# ============================================================
# VPN Gateway
# ============================================================
resource "azurerm_public_ip" "vpn_gateway" {
  name                = "pip-vpn-gateway"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_virtual_network_gateway" "main" {
  name                = "vpngw-main"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  type                = "Vpn"
  vpn_type            = "RouteBased"
  sku                 = var.vpn_gateway_sku
  tags                = var.tags

  ip_configuration {
    name                          = "vpn-ip-config"
    public_ip_address_id          = azurerm_public_ip.vpn_gateway.id
    private_ip_address_allocation = "Dynamic"
    subnet_id                     = azurerm_subnet.gateway.id
  }
}

# TODO: オンプレミスのVPNデバイス情報が確定したら追加
# resource "azurerm_local_network_gateway" "onprem" {}
# resource "azurerm_virtual_network_gateway_connection" "onprem" {}

# ============================================================
# App Service Plan（Frontend と Backend で共有）
# ============================================================
resource "azurerm_service_plan" "main" {
  name                = "asp-main"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = var.app_service_plan_sku
  tags                = var.tags
}

# ============================================================
# App Service — Frontend
# ============================================================
resource "azurerm_linux_web_app" "frontend" {
  name                      = var.app_service_fe_name
  location                  = azurerm_resource_group.main.location
  resource_group_name       = azurerm_resource_group.main.name
  service_plan_id           = azurerm_service_plan.main.id
  public_network_access_enabled = false # Private Endpoint のみでアクセス
  tags                      = var.tags

  site_config {
    always_on = false # B1 SKU では true 不可
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_app_service_virtual_network_swift_connection" "frontend" {
  app_service_id = azurerm_linux_web_app.frontend.id
  subnet_id      = azurerm_subnet.app.id
}

# ============================================================
# App Service — Backend
# ============================================================
resource "azurerm_linux_web_app" "backend" {
  name                      = var.app_service_be_name
  location                  = azurerm_resource_group.main.location
  resource_group_name       = azurerm_resource_group.main.name
  service_plan_id           = azurerm_service_plan.main.id
  public_network_access_enabled = false # Private Endpoint のみでアクセス
  tags                      = var.tags

  site_config {
    always_on = false
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_app_service_virtual_network_swift_connection" "backend" {
  app_service_id = azurerm_linux_web_app.backend.id
  subnet_id      = azurerm_subnet.app.id
}

# ============================================================
# Private Endpoint — Frontend
# ============================================================
resource "azurerm_private_endpoint" "frontend" {
  name                = "pe-${var.app_service_fe_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.app.id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${var.app_service_fe_name}"
    private_connection_resource_id = azurerm_linux_web_app.frontend.id
    subresource_names              = ["sites"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-fe"
    private_dns_zone_ids = [azurerm_private_dns_zone.app_service.id]
  }
}

# ============================================================
# Private Endpoint — Backend
# ============================================================
resource "azurerm_private_endpoint" "backend" {
  name                = "pe-${var.app_service_be_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.app.id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${var.app_service_be_name}"
    private_connection_resource_id = azurerm_linux_web_app.backend.id
    subresource_names              = ["sites"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-be"
    private_dns_zone_ids = [azurerm_private_dns_zone.app_service.id]
  }
}

# ============================================================
# Private DNS Zone（VNet 内での名前解決）
# ============================================================
resource "azurerm_private_dns_zone" "app_service" {
  name                = "privatelink.azurewebsites.net"
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "app_service" {
  name                  = "dns-link-vnet"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.app_service.name
  virtual_network_id    = azurerm_virtual_network.main.id
  tags                  = var.tags
}
