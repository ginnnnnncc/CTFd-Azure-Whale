# CTFd-Azure-Whale
A plugin for CTFd which allow your users to launch a standalone instance with **Azure Container Instance** for challenges. Special for internal practice or competition of small teams composed of **students**, and help you reduce the burden on servers due to running a large number of docker containers. If you have a **student subscription** to Azure, then this plugin is very suitable for you.

Adapted from [CTFd-Whale](https://github.com/glzjin/CTFd-Whale) and [Dynamic Value Challenges for CTFd](https://github.com/CTFd/CTFd/tree/master/CTFd/plugins/dynamic_challenges).

## Feature
- Because of the complex Azure Cli SDK of Python, this plugins use [Az.Cli](https://github.com/MarkWarneke/Az.Cli) to control the containers. 
- Choose Automatically the Azure Resource Group by CPU usage. (Servicing for students, this plugin set the maximum CPU limit for each resource group to 6)
- Provide container usage tacking. (Mark the container `Deleted` instead of deleting the container record)

## Usage

### Before Installation

1. Install Azure CLI and finish the authentication.
   
   [How to install the Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) -> [Create an Azure service principal](https://learn.microsoft.com/en-us/cli/azure/azure-cli-sp-tutorial-1?tabs=bash) -> [Sign in with a service principal](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-service-principal)

2. Create one or more resource groups, and grant service principal the authority. If you have more resource groups, just grant the main resource group authority to access other groups.

    [Check access for a user to a single Azure resource](https://learn.microsoft.com/en-us/azure/role-based-access-control/check-access)

3. Create Azure Container Registry. 

    [Create an Azure container registry using the Azure portal](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-get-started-portal?tabs=azure-cli)

### Installation

1. Copy this folder to your ctfd plugins folder. **Make sure the folder name is 'ctfd-whale'.**

2. Restart the CTFd docker container. Install the Azure CLI in the container, and login it.

    ```bash
    docker exec -it <id> /bin/bash
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash
    az login --service-principal -u <app-id> -p <password-or-cert> --tenant <tenant>
    ```

3. The function of editing resource group online is not supported, so you need insert the records in database directly in `resource_group` table. This table contains columns of `id`, `name`, `region`, `priority`, `used`. Resource group with smaller priority will be used first.

### Create Challenges

1. Build your images locally and push them to container registey. [With a single image](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-tutorial-prepare-app) / [With multiple images](https://learn.microsoft.com/en-us/azure/container-instances/tutorial-docker-compose)

2. Deploy a YAML file, even though you just use a single image. [Deploy a multi-container group using a YAML file](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-multi-container-yaml). You can check the YAML file rules on [YAML reference](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-reference-yaml). **Importantly, replace `name` with `#CONTAINER_NAME#` to prevent container group name dumplicated.** Also, you can set the `FLAG` environment by `#FLAG#` that will be replaced before container running.

3. Create dynamic docker challenge. The fields of the form is explained on the website.

## Some Tips

The CPU usage limit for student subscribed resource groups is limited to 6 cores. Every container group is limited to 4 cores and 16GB memory in total.
