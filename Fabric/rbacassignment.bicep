targetScope = 'resourceGroup'

param adminGroupObjectId string
param storageAccountId string
param keyVaultId string
param dataFactoryId string

// Assign group as Contributor on all
resource storageContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountId, adminGroupObjectId, 'StorageContributor')
  scope: resourceId('Microsoft.Storage/storageAccounts', last(split(storageAccountId, '/')))
  properties: {
    principalId: adminGroupObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c') // Contributor
  }
}

resource keyVaultContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVaultId, adminGroupObjectId, 'KVContributor')
  scope: resourceId('Microsoft.KeyVault/vaults', last(split(keyVaultId, '/')))
  properties: {
    principalId: adminGroupObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7') // Key Vault Contributor
  }
}

resource adfContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(dataFactoryId, adminGroupObjectId, 'ADFContributor')
  scope: resourceId('Microsoft.DataFactory/factories', last(split(dataFactoryId, '/')))
  properties: {
    principalId: adminGroupObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c') // Contributor
  }
}




targetScope = 'resourceGroup'

@description('Object ID of the Entra ID group to assign roles to')
param adminGroupObjectId string

@description('Resource ID of the Storage Account')
param storageAccountId string

@description('Resource ID of the Key Vault')
param keyVaultId string

@description('Resource ID of the Data Factory')
param dataFactoryId string

// 1️⃣ Bring the real resources into scope as "existing"
resource st 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: last(split(storageAccountId, '/'))
}

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: last(split(keyVaultId, '/'))
}

resource adf 'Microsoft.DataFactory/factories@2018-06-01' existing = {
  name: last(split(dataFactoryId, '/'))
}

// 2️⃣ Role assignments with resource-typed scopes

// Storage Account - Contributor
resource storageContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(st.id, adminGroupObjectId, 'StorageContributor')
  scope: st             // 👈 this is now a *resource*, not string
  properties: {
    principalId: adminGroupObjectId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'b24988ac-6180-42a0-ab88-20f7382dd24c' // Contributor
    )
  }
}

// Key Vault - Key Vault Contributor
resource keyVaultContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(kv.id, adminGroupObjectId, 'KVContributor')
  scope: kv            // 👈 resource
  properties: {
    principalId: adminGroupObjectId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'b86a8fe4-44ce-4948-aee5-eccb2c155cd7' // Key Vault Contributor
    )
  }
}

// Data Factory - Contributor
resource adfContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(adf.id, adminGroupObjectId, 'ADFContributor')
  scope: adf           // 👈 resource
  properties: {
    principalId: adminGroupObjectId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'b24988ac-6180-42a0-ab88-20f7382dd24c' // Contributor
    )
  }
}

