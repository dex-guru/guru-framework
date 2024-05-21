# chainflow-engine
ChainFlow Engine


### Build docker:

```
docker-compose up -d
```

### Deploy using helm

If you downloaded config from rancher
```
 export KUBECONFIG=~/Downloads/stage-k8s.yaml 
 helm upgrade --install chainflow-engine ./helm/engine  --wait -n stage --set imageTag=1 --set appName=chainflow-engine --set kubeNamespace=stage
```
Available at:

Application: http://localhost:8080/camunda/app/welcome/default/
API: http://localhost:8080/engine-rest
