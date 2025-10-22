param location string
param workspaceName string
param capacityId string

resource ws 'Microsoft.Fabric/workspaces@2023-11-01' = {
  name: workspaceName
  location: location
  properties: {
    capacityId: capacityId
  }
}

output fabricWorkspaceId string = ws.id