param location string
param dataFactoryName string

resource adf 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: dataFactoryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

output dataFactoryId string = adf.id



targetScope = 'resourceGroup'

param location string
param dataFactoryName string

// Factory with system-assigned identity
resource adf 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: dataFactoryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
}

// Self-hosted IR placeholder (actual compute is your VM/host)
resource shir 'Microsoft.DataFactory/factories/integrationRuntimes@2018-06-01' = {
  name: 'IR-js01'     // <-- your IR name
  parent: adf
  properties: {
    type: 'SelfHosted'
    description: 'Self-hosted IR for private network sources'
  }
}

output dataFactoryId string = adf.id
output integrationRuntimeId string = shir.id
