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
