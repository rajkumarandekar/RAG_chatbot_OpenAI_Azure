# Azure Deployment: ACR + Container Apps

Deploys the FastAPI backend as a container on Azure Container Apps, pulling the
image from Azure Container Registry. The React frontend can be deployed to
Azure Static Web Apps, or built and served separately — see notes at the end.

Replace every `<...>` placeholder with your actual values.

## 1. Variables (edit these once, reuse below)

```bash
RESOURCE_GROUP="<RESOURCE_GROUP_NAME>"
LOCATION="<AZURE_REGION>"              # e.g. eastus
ACR_NAME="<ACR_NAME>"                  # must be globally unique, lowercase alnum
ACA_ENV_NAME="<CONTAINER_APPS_ENV_NAME>"
ACA_APP_NAME="<CONTAINER_APP_NAME>"
IMAGE_NAME="rag-backend"
IMAGE_TAG="v1"
```

## 2. Create resource group

```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

## 3. Create Azure Container Registry and build the image

```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic

# Build directly in ACR (no local Docker daemon required)
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:$IMAGE_TAG \
  ./backend
```

Alternatively, build locally and push:

```bash
docker build -t $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG ./backend
az acr login --name $ACR_NAME
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG
```

## 4. Create the Container Apps environment

```bash
az extension add --name containerapp --upgrade

az containerapp env create \
  --name $ACA_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

## 5. Deploy the container app

```bash
az containerapp create \
  --name $ACA_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ACA_ENV_NAME \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-identity system \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 --memory 1.0Gi \
  --env-vars \
    AZURE_STORAGE_CONNECTION_STRING=secretref:storage-conn \
    AZURE_STORAGE_CONTAINER_NAME=<AZURE_STORAGE_CONTAINER_NAME> \
    AZURE_OPENAI_ENDPOINT=<AZURE_OPENAI_ENDPOINT> \
    AZURE_OPENAI_API_KEY=secretref:openai-key \
    AZURE_OPENAI_API_VERSION=2024-06-01 \
    AZURE_OPENAI_CHAT_DEPLOYMENT=<AZURE_OPENAI_CHAT_DEPLOYMENT> \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<AZURE_OPENAI_EMBEDDING_DEPLOYMENT> \
    AZURE_SEARCH_ENDPOINT=<AZURE_SEARCH_ENDPOINT> \
    AZURE_SEARCH_API_KEY=secretref:search-key \
    AZURE_SEARCH_INDEX_NAME=<AZURE_SEARCH_INDEX_NAME> \
    ALLOWED_ORIGINS=<FRONTEND_URL>
```

> Note: `az containerapp create` needs matching `--secrets` for anything referenced
> via `secretref:`. Grant ACR pull access first (step 5a) and register secrets
> (step 5b) if creating in one shot doesn't pick these up automatically on your
> CLI version.

### 5a. Allow Container Apps to pull from ACR

```bash
az containerapp registry set \
  --name $ACA_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --server $ACR_NAME.azurecr.io \
  --identity system
```

### 5b. Register secrets (connection strings / API keys)

```bash
az containerapp secret set \
  --name $ACA_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    storage-conn="<AZURE_STORAGE_CONNECTION_STRING>" \
    openai-key="<AZURE_OPENAI_API_KEY>" \
    search-key="<AZURE_SEARCH_API_KEY>"
```

## 6. Update the app with a new image (subsequent deploys)

```bash
az acr build --registry $ACR_NAME --image $IMAGE_NAME:$IMAGE_TAG ./backend

az containerapp update \
  --name $ACA_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG
```

## 7. Get the public backend URL

```bash
az containerapp show \
  --name $ACA_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv
```

Use this URL as `VITE_API_BASE_URL` when building the frontend, and add the
frontend's deployed URL to `ALLOWED_ORIGINS` on the backend.

## 8. Frontend deployment

The simplest option is Azure Static Web Apps:

```bash
cd frontend
npm install
npm run build   # outputs to frontend/dist

az staticwebapp create \
  --name <STATIC_WEB_APP_NAME> \
  --resource-group $RESOURCE_GROUP \
  --location <STATIC_WEB_APP_REGION> \
  --sku Free
```

Then upload `frontend/dist` via the Static Web Apps CLI (`swa deploy`) or
GitHub Actions integration. Any static host (Blob Storage static website,
Azure Storage + CDN, etc.) also works — the frontend is a plain Vite build.

## Prerequisites this doc assumes you already provisioned

- Azure OpenAI resource with a chat deployment and an embedding deployment
- Azure AI Search service, with the index created via `azure/create_index.py`
  (or the `azure/search-index-schema.json` schema)
- Azure Storage account with a blob container for uploaded PDFs
