param location string
param capacityName string

resource cap 'Microsoft.Fabric/capacities@2023-11-01' = {
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

output capacityId string = cap.id