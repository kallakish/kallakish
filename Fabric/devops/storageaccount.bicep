targetScope = 'resourceGroup'

@description('Resource location (defaults to RG location)')
param location string = resourceGroup().location

@description('Storage account name: 3–24 lowercase alphanumerics, globally unique')
param storageAccountName string

@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_RAGRS'
  'Standard_ZRS'
  'Premium_LRS'
  'Premium_ZRS'
])
@description('SKU for the storage account')
param skuName string = 'Standard_LRS'

@description('Enable Data Lake Gen2 (Hierarchical Namespace)')
param isHnsEnabled bool = true

@description('Allow public blob access (usually false)')
param allowBlobPublicAccess bool = false

resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: skuName
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: allowBlobPublicAccess
    supportsHttpsTrafficOnly: true
    isHnsEnabled: isHnsEnabled
    encryption: {
      keySource: 'Microsoft.Storage'
      services: {
        blob: { enabled: true }
        file: { enabled: true }
      }
    }
    publicNetworkAccess: 'Enabled'
  }
}

output storageAccountId string = sa.id
output storageAccountNameOut string = sa.name
