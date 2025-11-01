targetScope = 'subscription'

@description('Resource group name to create or update')
param resourceGroupName string

@description('Region for the resource group and resources')
param location string = 'uksouth'

@description('Globally unique storage account name (3–24 lowercase letters/numbers)')
param storageAccountName string

@description('SKU for the storage account')
@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_RAGRS'
  'Standard_ZRS'
  'Premium_LRS'
  'Premium_ZRS'
])
param skuName string = 'Standard_LRS'

@description('Enable Data Lake Gen2 (hierarchical namespace)')
param isHnsEnabled bool = true

@description('Allow public blob access')
param allowBlobPublicAccess bool = false

// ---------------------------------------------------
// 1️⃣ Create the Resource Group
// ---------------------------------------------------
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: {
    environment: 'dev'
    owner: 'data-team'
  }
}

// ---------------------------------------------------
// 2️⃣ Deploy the Storage Account inside the RG
// ---------------------------------------------------
resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  scope: resourceGroup(rg.name)
  name: storageAccountName
  location: location
  sku: {
    name: skuName
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: allowBlobPublicAccess
    supportsHttpsTrafficOnly: true
    isHnsEnabled: isHnsEnabled
    minimumTlsVersion: 'TLS1_2'
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

output resourceGroupName string = rg.name
output storageAccountId string = sa.id
output storageAccountName string = sa.name
