

#  A.9 Storage: Setup shared disks & VMs + Backup

## Objective
You have completed the workshop if
• a shared data disk has been added to the virtual machines
• a backup plan has been set up

## Used commands
1. Create a new project(only if folder hasnt been creeated yet):
    ```bash
    $ pulumi new A9test
    ```
1. Create a new stack:

    ```bash
    $ pulumi stack init A9test
    ```

1. Login to Azure CLI (you will be prompted to do this during deployment if you forget this step):

    ```bash
    $ az login
    ```
   
1. Specify the Azure location to use(TBD):

    ```bash
    $ pulumi config set location uksouth

    ```
   
1. Config Disks like in monograph:

    ```bash
    $ pulumi config set diskSize 1024
    $ pulumi config set diskSku Permium_LRS

    ```


1. Specify the Azure location to use:

    ```bash
    $ pulumi config set azure-native:location northeurope
    ```

1. Define Storage Account Name:

    ```bash
    $ pulumi config set azure-resources:storageAccountName mystorageaccount123huma
    ```

1. Specify SKU for the Storage Account:

    ``` bash
    $ pulumi config set azure-resources:skuName Standard_LRS
    ```

1. Set Ressource group name:

   ```bash
   $ pulumi config set azure-resources:resourceGroupName myResourceGroup123huma
   ```
1. pulumi up (-y to skip confirmation):

    ```bash
   $ pulumi up -y
         Previewing update (dev)
 
             Type                                     Name                 Plan
         +   pulumi:pulumi:Stack                      azure-resources-dev  create
         +   ├─ azure-native:resources:ResourceGroup  resourceGroup        create                                                                                                                                                           
         +   └─ azure-native:storage:StorageAccount   storageAccount       create                                                                                                                                                           
         Resources:
         + 3 to create
   
         Updating (dev)
   
         Type                                     Name                 Status
         +   pulumi:pulumi:Stack                      azure-resources-dev  created (39s)
         +   ├─ azure-native:resources:ResourceGroup  resourceGroup        created (6s)
         +   └─ azure-native:storage:StorageAccount   storageAccount       created (21s)
         Resources:
         + 3 created

         Duration: 40s
        ```
   
## Cleanup pulumi

1. Destroy stack(-y to skip confirmation) :
   ```bash
    $ pulumi destroy -y
   Previewing destroy (dev)


     Type                                     Name                 Plan                                                                                                                                                             
   -   pulumi:pulumi:Stack                      azure-resources-dev  delete                                                                                                                                                           
   -   ├─ azure-native:storage:StorageAccount   storageAccount       delete                                                                                                                                                           
   -   └─ azure-native:resources:ResourceGroup  resourceGroup        delete                                                                                                                                                           
   Resources:
   - 3 to delete

   Destroying (dev)

     Type                                     Name                 Status
    -   pulumi:pulumi:Stack                      azure-resources-dev  deleted (0.93s)
    -   ├─ azure-native:storage:StorageAccount   storageAccount       deleted (12s)
    -   └─ azure-native:resources:ResourceGroup  resourceGroup        deleted (17s)
    Resources:
    - 3 deleted

   Duration: 34s
    ```

1. If pulumi is messed up:
   ```bash
    $ pulumi cancel
    ```

1. Delte pulumi stack after excercise:
   ```bash
    $ pulumi stack rm dev
    ```

## Outputs
1. Shared disk output :
    ```bash
    $ pulumi stack output storageAccountName
    ```