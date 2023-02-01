docker build -t platform .
az acr login -n slothmq
docker tag platform:latest slothmq.azurecr.io/slothmq/platform
docker push slothmq.azurecr.io/slothmq/platform
