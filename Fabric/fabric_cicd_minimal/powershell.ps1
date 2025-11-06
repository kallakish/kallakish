GROUP_ID=$(az ad group show --group "<Your-Security-Group-Name>" --query objectId -o tsv)

# Get Service Principal Object ID
SPN_ID=$(az ad sp show --id "<Your-SPN-Application-Id-or-Name>" --query objectId -o tsv)

# Add SPN to Security Group
az ad group member add --group $GROUP_ID --member-id $SPN_ID
