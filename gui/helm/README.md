Deploy manually thru helm

```bash

helm upgrade --install chainflow-landing  helm/app --wait --timeout 10m -n prod --set imageTag=74 --set appName=app --set kubeNamespace=prod~~

``
