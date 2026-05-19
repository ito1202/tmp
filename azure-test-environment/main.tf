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

# App Service の VNet Integration 用（アウトバウンド出口）
# 委任が必要: FE・BE・Functions が同一 App Service Plan なのでこの Subnet を共用できる
resource "azurerm_subnet" "integration" {
  name                 = "subnet-integration"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_integration_prefix]

  delegation {
    name = "app-service-delegation"
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

# Private Endpoint 用（インバウンド受け口）
# FE・BE・Functions・Foundry の PE をすべてここに置く
resource "azurerm_subnet" "pe" {
  name                 = "subnet-pe"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_pe_prefix]
}

# Functions（Flex Consumption）の VNet Integration 用（アウトバウンド出口）
# App Service Plan と Plan が異なるため subnet-integration と共用不可
resource "azurerm_subnet" "func_integration" {
  name                 = "subnet-func-integration"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_func_integration_prefix]

  # Flex Consumption の委任名は App Service Plan と異なる
  delegation {
    name = "functions-flex-delegation"
    service_delegation {
      name    = "Microsoft.App/environments"
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

resource "azurerm_subnet_network_security_group_association" "pe" {
  subnet_id                 = azurerm_subnet.pe.id
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
  subnet_id      = azurerm_subnet.integration.id
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
  subnet_id      = azurerm_subnet.integration.id
}

# ============================================================
# Private Endpoint — Frontend
# ============================================================
resource "azurerm_private_endpoint" "frontend" {
  name                = "pe-${var.app_service_fe_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.pe.id
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
  subnet_id           = azurerm_subnet.pe.id
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

# ============================================================
# Storage Account（RAG 用ファイル置き場）
# ============================================================
resource "azurerm_storage_account" "main" {
  name                          = var.storage_account_name
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  public_network_access_enabled = false
  tags                          = var.tags
}

resource "azurerm_private_endpoint" "storage" {
  name                = "pe-${var.storage_account_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.pe.id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${var.storage_account_name}"
    private_connection_resource_id = azurerm_storage_account.main.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-storage"
    private_dns_zone_ids = [azurerm_private_dns_zone.storage_blob.id]
  }
}

resource "azurerm_private_dns_zone" "storage_blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "storage_blob" {
  name                  = "dns-link-storage-blob"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.storage_blob.name
  virtual_network_id    = azurerm_virtual_network.main.id
  tags                  = var.tags
}

# ============================================================
# Azure AI Search（RAG インデックス・ベクトル検索）
# ============================================================
resource "azurerm_search_service" "main" {
  name                          = var.ai_search_name
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  sku                           = var.ai_search_sku
  public_network_access_enabled = false
  tags                          = var.tags

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_private_endpoint" "ai_search" {
  name                = "pe-${var.ai_search_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.pe.id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${var.ai_search_name}"
    private_connection_resource_id = azurerm_search_service.main.id
    subresource_names              = ["searchService"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-search"
    private_dns_zone_ids = [azurerm_private_dns_zone.ai_search.id]
  }
}

resource "azurerm_private_dns_zone" "ai_search" {
  name                = "privatelink.search.windows.net"
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "ai_search" {
  name                  = "dns-link-search"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.ai_search.name
  virtual_network_id    = azurerm_virtual_network.main.id
  tags                  = var.tags
}

# ============================================================
# Azure Functions（Flex Consumption / RAG ツール）
# ============================================================
resource "azurerm_storage_account" "functions" {
  name                          = "${var.storage_account_name}func"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  public_network_access_enabled = false
  tags                          = var.tags
}

resource "azurerm_linux_function_app" "main" {
  name                          = var.functions_app_name
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  storage_account_name          = azurerm_storage_account.functions.name
  storage_account_access_key    = azurerm_storage_account.functions.primary_access_key
  public_network_access_enabled = false
  tags                          = var.tags

  # Flex Consumption Plan
  service_plan_id = azurerm_service_plan.functions.id

  site_config {}

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_service_plan" "functions" {
  name                = "asp-functions"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "FC1" # Flex Consumption
  tags                = var.tags
}

resource "azurerm_app_service_virtual_network_swift_connection" "functions" {
  app_service_id = azurerm_linux_function_app.main.id
  subnet_id      = azurerm_subnet.func_integration.id
}

resource "azurerm_private_endpoint" "functions" {
  name                = "pe-${var.functions_app_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.pe.id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${var.functions_app_name}"
    private_connection_resource_id = azurerm_linux_function_app.main.id
    subresource_names              = ["sites"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-functions"
    private_dns_zone_ids = [azurerm_private_dns_zone.app_service.id]
  }
}

# ============================================================
# Azure AI Foundry — Private Endpoint
# Hub と Project それぞれに PE が必要
# ============================================================
resource "azurerm_private_dns_zone" "foundry" {
  name                = "privatelink.services.ai.azure.com"
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "foundry" {
  name                  = "dns-link-foundry"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.foundry.name
  virtual_network_id    = azurerm_virtual_network.main.id
  tags                  = var.tags
}

# TODO: Foundry Hub / Project リソースが確定したら PE を追加
# resource "azurerm_private_endpoint" "foundry_hub" { ... }
# resource "azurerm_private_endpoint" "foundry_project" { ... }

# ============================================================
# Log Analytics Workspace（Azure Monitor）
# ============================================================
resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${var.resource_group_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_monitor_diagnostic_setting" "frontend" {
  name                       = "diag-frontend"
  target_resource_id         = azurerm_linux_web_app.frontend.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log { category = "AppServiceHTTPLogs" }
  enabled_log { category = "AppServiceAppLogs" }
  metric { category = "AllMetrics" }
}

resource "azurerm_monitor_diagnostic_setting" "backend" {
  name                       = "diag-backend"
  target_resource_id         = azurerm_linux_web_app.backend.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log { category = "AppServiceHTTPLogs" }
  enabled_log { category = "AppServiceAppLogs" }
  metric { category = "AllMetrics" }
}

resource "azurerm_monitor_diagnostic_setting" "functions" {
  name                       = "diag-functions"
  target_resource_id         = azurerm_linux_function_app.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log { category = "FunctionAppLogs" }
  metric { category = "AllMetrics" }
}

resource "azurerm_monitor_diagnostic_setting" "ai_search" {
  name                       = "diag-ai-search"
  target_resource_id         = azurerm_search_service.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log { category = "OperationLogs" }
  metric { category = "AllMetrics" }
}
