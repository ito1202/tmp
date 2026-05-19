output "resource_group_name" {
  description = "リソースグループ名"
  value       = azurerm_resource_group.main.name
}

output "vnet_id" {
  description = "VNet の ID"
  value       = azurerm_virtual_network.main.id
}

output "vpn_gateway_public_ip" {
  description = "VPN Gateway のパブリックIP（オンプレ側の設定に使用）"
  value       = azurerm_public_ip.vpn_gateway.ip_address
}

output "frontend_principal_id" {
  description = "Frontend マネージドID の Principal ID（IAM ロール付与に使用）"
  value       = azurerm_linux_web_app.frontend.identity[0].principal_id
}

output "backend_principal_id" {
  description = "Backend マネージドID の Principal ID（IAM ロール付与に使用）"
  value       = azurerm_linux_web_app.backend.identity[0].principal_id
}

output "frontend_private_ip" {
  description = "Frontend Private Endpoint の IP（オンプレのDNS設定に使用）"
  value       = azurerm_private_endpoint.frontend.private_service_connection[0].private_ip_address
}

output "backend_private_ip" {
  description = "Backend Private Endpoint の IP"
  value       = azurerm_private_endpoint.backend.private_service_connection[0].private_ip_address
}

output "functions_principal_id" {
  description = "Functions マネージドID の Principal ID（AI Search / Storage へのロール付与に使用）"
  value       = azurerm_linux_function_app.main.identity[0].principal_id
}

output "ai_search_principal_id" {
  description = "AI Search マネージドID の Principal ID（Storage へのロール付与に使用）"
  value       = azurerm_search_service.main.identity[0].principal_id
}

output "storage_account_name" {
  description = "Storage Account 名（RAG ファイルアップロード先）"
  value       = azurerm_storage_account.main.name
}
