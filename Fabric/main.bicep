param location string
param resourceGroupName string
param storageAccountName string
param keyVaultName string
param dataFactoryName string
param capacityName string
param workspaceName string

module rg './modules/resourceGroup.bicep' = {
  name: 'rgDeploy'
  params: {
    location: location
    resourceGroupName: resourceGroupName
  }
}

module st './modules/storageAccount.bicep' = {
  name: 'stDeploy'
  scope: resourceGroup(rg.outputs.resourceGroupName)
  params: {
    location: location
    storageAccountName: storageAccountName
  }
}

module kv './modules/keyVault.bicep' = {
  name: 'kvDeploy'
  scope: resourceGroup(rg.outputs.resourceGroupName)
  params: {
    location: location
    keyVaultName: keyVaultName
  }
}

module adf './modules/dataFactory.bicep' = {
  name: 'adfDeploy'
  scope: resourceGroup(rg.outputs.resourceGroupName)
  params: {
    location: location
    dataFactoryName: dataFactoryName
  }
}

module cap './modules/fabricCapacity.bicep' = {
  name: 'capDeploy'
  params: {
    location: location
    capacityName: capacityName
  }
}

module ws './modules/fabricWorkspace.bicep' = {
  name: 'wsDeploy'
  params: {
    location: location
    workspaceName: workspaceName
    capacityId: cap.outputs.capacityId
  }
}


module rbac './modules/rbacAssignments.bicep' = {
  name: 'rbacAssign'
  scope: resourceGroup(rg.name)
  params: {
    adminGroupObjectId: adminGroupObjectId
    storageAccountId: storage.outputs.storageAccountId
    keyVaultId: kv.outputs.keyVaultId
    dataFactoryId: adf.outputs.dataFactoryId
  }
}

output storageAccountId string = st.outputs.storageAccountId
output dataFactoryId string = adf.outputs.dataFactoryId
output keyVaultId string = kv.outputs.keyVaultId
output fabricWorkspaceId string = ws.outputs.fabricWorkspaceId
