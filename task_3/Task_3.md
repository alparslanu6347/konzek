# Installing Kubernetes on `Ubuntu` running on AWS EC2 Instances

***Instead of following the steps in Part 1, Part 2, and Part 3, a Kubernetes cluster can be set up using the Terraform tool. For this, the module I have published in my Terraform Registry account can be used.***

[https://registry.terraform.io/modules/alparslanu6347/ks8-cluster/aws/latest]

## Part 1 - Setting Up Kubernetes Environment on `All Nodes`

- We will prepare two nodes for Kubernetes on `Ubuntu 24.04`. One of the node will be configured as the `Master node`, the other will be the `worker node`. Following steps should be executed on all nodes. *Note: It is recommended to install Kubernetes on machines with `2 CPU Core` and `2GB RAM` at minimum to get it working efficiently. For this reason, we will select `t3a.medium` as EC2 instance type, which has `2 CPU Core` and `4 GB RAM`.*

- `Required ports` (https://kubernetes.io/docs/reference/networking/ports-and-protocols/)  for Kubernetes. 

- Create two security groups. Name the first security group as `master-sec-group` and apply the following Control-plane (Master) Node(s) table to your master node.

- Name the second security group as `worker-sec-group`, and apply the following Worker Node(s) table to your worker nodes.

### Control-plane (Master) Node(s)

|Protocol|Direction|Port Range|                  Purpose                 |       Used By      |
|--------|---------|----------|------------------------------------------|--------------------|
|  TCP   | Inbound |   6443   |Kubernetes API server                     |        All         |
|  TCP   | Inbound |2379-2380 |`etcd` server client API                  |kube-apiserver, etcd|
|  TCP   | Inbound |  10250   |Kubelet API                               |Self, Control plane |
|  TCP   | Inbound |  10259   |kube-scheduler                            |        Self        |
|  TCP   | Inbound |  10257   |kube-controller-manager                   |        Self        |
|  TCP   | Inbound |    22    |remote access with ssh                    |        Self        |
|  UDP   | Inbound |   8472   |Cluster-Wide Network Comm. - Flannel VXLAN|        Self        |

### Worker Node(s)

|Protocol|Direction|Port Range |                Purpose                   |      Used By       |
|--------|---------|-----------|------------------------------------------|--------------------|
|  TCP   | Inbound |   10250   |               Kubelet API                |Self, Control plane |
|  TCP   | Inbound |   10256   |               Kube-proxy                 |Self, Load balancers|
|  TCP   | Inbound |30000-32767|               NodePort Services          |        All         |
|  TCP   | Inbound |    22     |               Remote access with ssh     |        Self        |
|  UDP   | Inbound |   8472    |Cluster-Wide Network Comm. - Flannel VXLAN|        Self        |

> ***SWAP OFF***
During Kubernetes setup, it is necessary to disable swap. Kubernetes is incompatible with swap, and when swap is active, Kubernetes nodes (workers) may not function properly. Kubernetes, by default, manages memory and resource allocation for pods, and it prevents writing to the swap space. Therefore, it is important to disable swap for Kubernetes to work correctly.
> Why Swap is Incompatible with Kubernetes
Kubernetes manages memory directly on the node's memory. If swap space is active, Kubernetes' memory management and resource allocation strategies do not function properly, leading to the following issues:
> 1. Pod Resource Limits: The proper calculation of pod memory usage (memory limits) may not work. Kubernetes relies on the memory limits set for pods, and with swap enabled, it cannot properly enforce these limits.
> 2. Memory Requests and Limits: Kubernetes sets memory limits for each pod. If swap is active, the operating system will begin writing to the swap space when memory is insufficient, which can cause Kubernetes to mismanage workloads as it cannot correctly track memory usage.
> 3. Performance Issues: Swap uses disk storage, which is much slower than memory access. As a result, the use of swap can lead to performance degradation for pods running on Kubernetes. When the system starts using swap, pod performance can be severely impacted, leading to slower response times and instability in workloads.
> Conclusion
Disabling swap is critical for Kubernetes to function properly. Kubernetes cannot manage nodes and pods efficiently if swap is enabled, leading to incorrect resource allocation, performance degradation, and potential instability in the cluster. Therefore, it's a best practice to disable swap when setting up Kubernetes.

> **Ignore this section for AWS instances. But, it must be applied for real servers/workstations.**
>
> - Find the line in `/etc/fstab` referring to swap, and comment out it as following.
>
> ```bash
> # Swap a usb extern (3.7 GB):
> #/dev/sdb1 none swap sw 0 0
>```
>
> or,
>
> - Disable swap from command line
>
> ```bash
> free -m
> sudo swapoff -a && sudo sed -i '/ swap / s/^/#/' /etc/fstab
> ```
>

- Hostname change of the nodes, so we can discern the roles of each nodes. For example, you can name the nodes (instances) like `kube-master, kube-worker-1`

```bash (master & worker)
sudo hostnamectl set-hostname kube-master
sudo hostnamectl set-hostname kube-worker-1
bash
```

### Install Container Runtimes

- We install required container runtimes according to [kubernetes Container Runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/) documentation.

#### Install and configure prerequisites

- Forwarding IPv4 and letting iptables see bridged traffic:

```bash (master & worker)
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl params required by setup, params persist across reboots
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply sysctl params without reboot
sudo sysctl --system
```

- Verify that the br_netfilter, overlay modules are loaded by running the following commands:

```bash (master & worker)
lsmod | grep br_netfilter
lsmod | grep overlay
```

- Verify that the net.bridge.bridge-nf-call-iptables, net.bridge.bridge-nf-call-ip6tables, and net.ipv4.ip_forward system variables are set to 1 in your sysctl config by running the following command:

```bash (master & worker)
sysctl net.bridge.bridge-nf-call-iptables net.bridge.bridge-nf-call-ip6tables net.ipv4.ip_forward
```

#### Install containerd on ubuntu (https://docs.docker.com/engine/install/ubuntu/)

- Set up Docker's apt repository.

```bash (master & worker)
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

- Install containerd.

```bash (master & worker)
sudo apt-get install containerd.io
```

- Check the containerd.

```bash (master & worker)
sudo systemctl status containerd
```

- Test the containerd.

```bash (master & worker)
sudo ctr images pull docker.io/library/redis:alpine
sudo ctr run -d docker.io/library/redis:alpine redis
sudo ctr container ls
```

#### Install `nerdctl` (Optional)

- While the ctr tool is bundled together with containerd, it should be noted the ctr tool is solely made for debugging containerd. The `nerdctl` tool provides stable and human-friendly user experience.

- Download the nerdctl binary from nerdctl github page. (https://github.com/containerd/nerdctl/releases)

- Download `nerdctl-full-*-linux-amd64.tar.gz` release.

```bash (master & worker)
wget https://github.com/containerd/nerdctl/releases/download/v1.7.6/nerdctl-full-1.7.6-linux-amd64.tar.gz
```

- Extract the archive to a path like `/usr/local`.

```bash (master & worker)
sudo tar xvf nerdctl-full-1.7.6-linux-amd64.tar.gz -C /usr/local
```

- Test the `nerdctl`.

```bash (master & worker)
sudo nerdctl run -d --name redis redis:alpine
sudo nerdctl container ls
```

#### `cgroup drivers` [https://kubernetes.io/docs/setup/production-environment/container-runtimes/]

- On Linux, control groups are used to constrain resources that are allocated to processes.

- Both the kubelet and the underlying container runtime need to interface with control groups to enforce resource management for pods and containers and set resources such as cpu/memory requests and limits. To interface with control groups, the kubelet and the container runtime need to use a cgroup driver. `It's critical that the kubelet and the container runtime use the same cgroup driver and are configured the same`.

- There are two cgroup drivers available:

  cgroupfs
  `systemd`

#### Configuring the `systemd` cgroup driver for containerd.

- Configure containerd so that it starts using systemd as cgroup.

```bash (master & worker)
sudo containerd config default | sudo tee /etc/containerd/config.toml >/dev/null 2>&1
sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml
```

Restart and enable containerd service

```bash (master & worker)
sudo systemctl restart containerd
sudo systemctl enable containerd
```

### Install kubeadm (https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)

- Install helper packages for Kubernetes.

```bash (master & worker)
# Update the apt package index and install packages needed to use the Kubernetes apt repository:

sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Download the Google Cloud public signing key:

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add the Kubernetes apt repository:

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

- Update apt package index, install kubelet, kubeadm and kubectl, and pin their version:

```bash (master & worker)
sudo apt-get update

sudo apt-get install kubectl kubeadm kubelet kubernetes-cni

sudo apt-mark hold kubelet kubeadm kubectl
```

## Part 2 - Setting Up `Master Node` for Kubernetes (https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)

***Following commands should be executed on Master Node only.***

- Pull the packages for Kubernetes beforehand

```bash (master)
sudo kubeadm config images pull
```

- Let `kubeadm` prepare the environment for you. Note: Do not forget to change `<ec2-private-ip>` with your master node private IP.

```bash (master)
sudo kubeadm init --apiserver-advertise-address=<ec2-private-ip> --pod-network-cidr=10.244.0.0/16
```

- After successful initialization, you should see something similar to the following output (shortened version).

```bash (master)
...
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join 172.31.32.92:6443 --token 6grb8s.6jjyof8xi8vtxztb \
        --discovery-token-ca-cert-hash sha256:32d1c906fddc50a865b533f909377b2219ef650373ca1b7d4310de025817a00b
```

> Note down the `kubeadm join ...` part in order to connect your worker nodes to the master node. Remember to run this command with `sudo`.

- Run following commands to set up local `kubeconfig` on master node.

```bash (master)
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

- Activate the `Flannel` pod networking, network add-ons on : `https://kubernetes.io/docs/concepts/cluster-administration/addons/`.

```bash (master)
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

- Master node (also named as Control Plane) should be ready, show existing pods created by user. Since we haven't created any pods, list should be empty.

```bash (master)
kubectl get nodes
```

- Show the list of the pods created for Kubernetes service itself. Note that pods of Kubernetes service are running on the master node.

```bash (master)
kubectl get pods -n kube-system
```

- Show the details of pods in `kube-system` namespace. Note that pods of Kubernetes service are running on the master node.

```bash (master)
kubectl get pods -n kube-system -o wide
```

- We can also see containers with `nerdctl` command.

```bash (master)
sudo nerdctl --namespace k8s.io ps -a
```

- Get the services available. Since we haven't created any services yet, we should see only Kubernetes service.

```bash (master)
kubectl get services
```

## Part 3 - Adding the `Worker Nodes` to the Cluster

- Show the list of nodes. Since we haven't added worker nodes to the cluster, we should see only master node itself on the list.

```bash (Worker Nodes)
kubectl get nodes
```

- Get the kubeadm `join command` on `master node`.

```bash (master)
kubeadm token create --print-join-command
```

- Run `sudo kubeadm join...` command to have them join the cluster on `worker node`.

```bash (Worker Nodes)
sudo kubeadm join 172.31.3.109:6443 --token 1aiej0.kf0t4on7c7bm2hpa \
    --discovery-token-ca-cert-hash sha256:0e2abfb56733665c0e6204217fef34be2a4f3c4b8d1ea44dff85666ddf722c02
```

- Go to the master node. Get the list of nodes. Now, we should see the new worker nodes in the list.

```bash (master)
kubectl get nodes
```

- Get the details of the nodes.

```bash (master)
kubectl get nodes -o wide
```

## Part 4 - Create the image and prepare the YAML files.

- Deployment

```bash (master)
cd konzek
nano Dockerfile
```

```Dockerfile
# We are using Python as the base image.
FROM python:3.9-slim

# We are setting the working directory.
WORKDIR /app

# We are copying the Python application and its dependencies into the container.
COPY my_server.py /app/

# Install the necessary dependencies (you can use requirements.txt if needed).
RUN pip install --no-cache-dir --upgrade pip

# We are running the application on port 8080.
EXPOSE 8080

# The application startup command.
CMD ["python", "my_server.py"]
```

```bash
docker build -t my-app:1.0 .
# Log in to your Docker Hub account and push your image:
# Log in to Docker Hub.
docker login

# Tag the Docker image.
docker tag my-app:1.0 <your-dockerhub-username>/my-app:1.0

# Push the Docker image.
docker push <your-dockerhub-username>/my-app:1.0
```

```bash
nano deployment.yaml
nano my-service.yaml
nano my-ingress.yaml
```

```yaml (deployment.yaml)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    name: konzek
    app: my-app
spec:
  replicas: 2  # 2 pods
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
        image: <your-dockerhub-username>/my-app:1.0  # Use your Docker Hub image
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

- Service

```yaml (my-service.yaml)
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
  labels:
    name: konzek
    app: my-app
spec:
  selector:
    app: my-app
  type: LoadBalancer  # We are using LoadBalancer and AWS support for external access. Check on the Console; a Load Balancer will be created.
  ports:
    - name: http
      protocol: TCP
      port: 80  # Service port
      targetPort: 8080  # Pod port
```

-  Ingress (Optional)

***Ingress is used to route HTTP and HTTPS requests to specific services. To do this, you need to install an Ingress Controller***

```yaml (my-ingress.yaml)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: my-app.example.com  # Your domain name
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app-service
            port:
              number: 80
```

Apply the YAML files.

```bash
# Create a Deployment.
kubectl apply -f my-deployment.yaml

# Create a Service
kubectl apply -f my-service.yaml

# (Optional) create an Ingress
kubectl apply -f my-ingress.yaml
```

- Check the readiness of nodes at the cluster on master node.

```bash
kubectl get nodes
```

- Show the list of existing pods.

```bash
# Check the status of the Pods.
kubectl get pods

# Check the status of the Service.
kubectl get service my-app-service

# (Optional) Check the status of the Ingress.
kubectl get ingress my-app-ingress
```

- Test the application.

   - Access via LoadBalancer.
    ***Since the Service is of type `LoadBalancer`, find the external IP address using the following command:***

- Check the services.
```bash
kubectl get svc
# kubectl get service my-app-service
```
- You will see an output like this

```text
NAME                 TYPE           CLUSTER-IP       EXTERNAL-IP                                                               PORT(S)          AGE
kubernetes           ClusterIP      10.100.0.1       <none>                                                                    443/TCP          120m
my-app-service       LoadBalancer   10.100.59.43     a2a513b28b46b4a20848f8303294e90f-1926642410.us-east-2.elb.amazonaws.com   80:31860/TCP     22m
```
***TYPE --->>>  Since the Service type is LoadBalancer and the DNS name is assigned to the LoadBalancer in AWS Console, you can access the application by entering the LoadBalancer DNS in your browser with :80 appended at the end.***

```bash
curl http://<LOAD_BALANCER_EXTERNAL-IP>
curl a2a513b28b46b4a20848f8303294e90f-1926642410.us-east-2.elb.amazonaws.com:80
### OR Browser
http://<LOAD_BALANCER_EXTERNAL-IP>
```

   - Access via Ingress (Optional)
   ***If you're using Ingress, you can access the application using the domain name provided by the Ingress Controller***

```bash
curl http://my-app.example.com
### Veya Browser
# http://<your-domain-name>/
http://my-app.example.com
```


## Part 5 - Rolling Updates Demonstration

- Update the Docker Image

```bash
docker build -t my-app:2.0 .
docker tag my-app:2.0 <your-dockerhub-username>/my-app:2.0
docker push <your-dockerhub-username>/my-app:2.0
```

- Update the Deployment

```yaml
spec:
  template:
    spec:
      containers:
      - name: my-app-container
        image: <your-dockerhub-username>/my-app:2.0
```

- Reapply

```bash
kubectl apply -f my-deployment.yaml
```

- Monitor the rolling update process

```bash
kubectl rollout status deployment/my-app
```

## Part 6 - Monitor logs and status

```bash
# Check the Pod logs
kubectl logs <POD_NAME>
```

- Get the list of pods in default namespace on master and check the status and readyness of `my-app-container`

```bash
kubectl get pods -o wide
```

- Get the list of services and show the newly created service of `my-app-service`

```bash
kubectl get service -o wide
```

- Get the list of ingresses and show the newly created ingress of `my-app-ingress`

```bash
kubectl get ingress -o wide
```

- Clean the service and pod from the cluster.

```bash
kubectl delete service my-app-service
kubectl delete pods my-app-container
```

- Check there is no pod left in default namespace.

```bash
kubectl get pods
```

