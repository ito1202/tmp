variable "location" {
  description = "Azureリージョン"
  type        = string
  default     = "japaneast"
}

variable "resource_group_name" {
  description = "リソースグループ名"
  type        = string
}

variable "vnet_address_space" {
  description = "VNet のアドレス空間"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_integration_prefix" {
  description = "VNet Integration 用 Subnet のアドレス範囲（App Service のアウトバウンド出口）"
  type        = string
  default     = "10.0.1.0/24"
}

variable "subnet_pe_prefix" {
  description = "Private Endpoint 用 Subnet のアドレス範囲（App Service へのインバウンド受け口）"
  type        = string
  default     = "10.0.2.0/24"
}

variable "subnet_func_integration_prefix" {
  description = "Functions（Flex Consumption）VNet Integration 用 Subnet のアドレス範囲"
  type        = string
  default     = "10.0.4.0/24"
}

variable "subnet_gateway_prefix" {
  description = "VPN Gateway 用 Subnet のアドレス範囲（名前は GatewaySubnet 固定）"
  type        = string
  default     = "10.0.255.0/27"
}

variable "allowed_ip_ranges" {
  description = "オンプレミスのグローバルIP（NSGホワイトリスト）"
  type        = list(string)
}

variable "app_service_plan_sku" {
  description = "App Service Plan の SKU"
  type        = string
  default     = "B1"
}

variable "app_service_fe_name" {
  description = "Frontend App Service 名（Azure 全体でユニークである必要あり）"
  type        = string
}

variable "app_service_be_name" {
  description = "Backend App Service 名（Azure 全体でユニークである必要あり）"
  type        = string
}

variable "functions_app_name" {
  description = "Azure Functions 名（Azure 全体でユニークである必要あり）"
  type        = string
}

variable "storage_account_name" {
  description = "Storage Account 名（Azure 全体でユニーク・小文字英数字のみ・24文字以内）"
  type        = string
}

variable "ai_search_name" {
  description = "Azure AI Search 名（Azure 全体でユニークである必要あり）"
  type        = string
}

variable "ai_search_sku" {
  description = "Azure AI Search の SKU（basic / standard / standard2）"
  type        = string
  default     = "basic"
}

variable "vpn_gateway_sku" {
  description = "VPN Gateway の SKU"
  type        = string
  default     = "VpnGw1"
}

variable "tags" {
  description = "全リソースに付与するタグ"
  type        = map(string)
  default     = {}
}
