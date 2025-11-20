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



// Using existing capacity :

param location string
param capacityName string

@description('If true, do NOT create a new capacity; use an existing one with this name.')
param reuseExistingCapacity bool = false

// Reference an existing capacity (used when reuseExistingCapacity = true)
resource capExisting 'Microsoft.Fabric/capacities@2023-11-01' existing = if (reuseExistingCapacity) {
  name: capacityName
}

// Create a new capacity (used when reuseExistingCapacity = false)
resource cap 'Microsoft.Fabric/capacities@2023-11-01' = if (!reuseExistingCapacity) {
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

// Always output an ID – choose existing vs new
output capacityId string = reuseExistingCapacity ? capExisting.id : cap.id
