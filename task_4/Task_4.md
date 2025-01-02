# Debugging and Troubleshooting

## Scenario 1: Misconfigured systemd Service `Service File (Misconfigured Example)`

### Example Problem : A my_service.service file is provided but fails to start.

- Service File (Misconfigured)

```sh   (my_service.service)
[Unit]
Description=Python HTTP Server
After=network.target

[Service]
ExecStart=python /app/my_server.py  # Missing Python path
Restart=always
WorkingDirectory=/home/ec2-user/app
StandardOutput=append:/var/log/my_service.log
StandardError=append:/var/log/my_service_error.log
User=root  # Potential security issue
```

### Troubleshooting Process :

#### Step 1: Check the Service Status

```bash
sudo systemctl status my_service.service
```

- Identify error messages like :

```text
ExecStart failed: No such file or directory
WorkingDirectory not found
Permission denied
```

#### Step 2: Inspect Logs

- Use journalctl to see detailed logs:

```bash
sudo journalctl -u my_service.service
```

#### Step 3: Fix Configuration Issues

- Provide Full Path to Python Executable: Replace python with `/usr/bin/python3`.

- Fix Working Directory: Ensure `/home/ec2-user/konzek/my_server.py` exists.

- Change User to a Non-Root User: Replace User=root with `ec2-user`.

- Corrected Service File :

```sh   (my_service.service)
[Unit]
Description=Python HTTP Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/ec2-user/konzek/my_server.py
Restart=always
User=ec2-user
WorkingDirectory=/home/ec2-user/konzek
StandardOutput=append:/var/log/my_service.log
StandardError=append:/var/log/my_service_error.log
TimeoutSec=30

[Install]
WantedBy=multi-user.target
```

#### Step 4: Reload and Restart the Service

```bash
sudo systemctl daemon-reload
sudo systemctl restart my_service.service
sudo systemctl status my_service.service
```

## Scenario 2: Misconfigured Kubernetes Deployment `Deployment File (Misconfigured Example)`

### Example Problem : A Kubernetes Deployment file is provided, but pods fail to start or behave unexpectedly.

- Deployment File (Misconfigured)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    name: konzek
    app: my-app
spec:
  replicas: 2 
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app-container
        image: my-app:latest  # Image tag issue
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"  # Unused
        resources:
          limits:
            memory: "128Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "250m"
```

### Troubleshooting Process :

#### Step 1: Check Pod Status

```bash
kubectl get pods
```

- Common errors include:
    - ImagePullBackOff: Incorrect image name or tag.
    - CrashLoopBackOff: Application crashes repeatedly.
    - Pending: Insufficient resources.

#### Step 2: Describe Pod

```bash
kubectl describe pod <POD_NAME>
```

- Look for issues like:
    - Image pull errors: Failed to pull image.
    - Environment variable mismatches.
    - Resource constraints leading to scheduling failures.


#### Step 3: Inspect Logs

- If the pod starts but crashes, check the logs:

```bash
kubectl logs <POD_NAME>
```

#### Step 4: Fix Configuration Issues

- Fix Image Tag: Replace my-app:latest with a valid tag like my-app:1.0.

- Ensure Port Alignment: Remove unused environment variable PORT.

- Resource Requests and Limits: Verify they match node capacity.

- Corrected Deployment File :

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    name: konzek
    app: my-app
spec:
  replicas: 2 
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app-container
        image: my-app:1.0
        ports:
        - containerPort: 8080
        resources:
          limits:
            memory: "256Mi"
            cpu: "1"
          requests:
            memory: "128Mi"
            cpu: "500m"
```

#### Step 5: Apply and Verify

- Apply the updated Deployment


```bash
kubectl apply -f my-deployment.yaml
```

- Monitor rolling updates and pod status

```bash
kubectl rollout status deployment/my-app
kubectl get pods
```