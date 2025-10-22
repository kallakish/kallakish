param location string
param resourceGroupName string
param storageAccountName string
param dataFactoryName string
param capacityName string
param workspaceName string

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: resourceGroupName
  location: location
}

resource stg 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {}
}

resource adf 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: dataFactoryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

resource fabricCapacity 'Microsoft.Fabric/capacities@2023-11-01' = {
  name: capacityName
  location: location
  sku: {
    name: 'F2'
    tier: 'Fabric'
  }
  properties: {
    administration: {
      members: []
    }
  }
}

resource fabricWorkspace 'Microsoft.Fabric/workspaces@2023-11-01' = {
  name: workspaceName
  location: location
  properties: {
    capacityId: fabricCapacity.id
  }
}

output storageAccountId string = stg.id
output dataFactoryId string = adf.id
output fabricWorkspaceId string = fabricWorkspace.id