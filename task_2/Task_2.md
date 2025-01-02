# Part 1 - Launch en EC2 instance, install python and install Docker & Docker Compose

- Launch an EC2 instance using the Amazon Linux 2023 AMI with security group allowing SSH connections.
***`instance type` : t2.micro ; `Security Group Ports` = 22 (Allow SSH (port 22) only for your own IP address.), 80, 8080 (HTTP (port 80) and Custom TCP Rule (port 8080) for 0.0.0.0/0)***

- Connect to your instance with SSH.

```bash (pwd : home/ec2-user)
ssh -i .ssh/"key-pair.pem" ec2-user@your-ec2-public-ip
# ssh -i "key-pair.pem" ec2-user@your-ec2-public-ip
```

- Update the installed packages and package cache on your instance.

```bash (pwd : home/ec2-user)
sudo dnf update -y
```

- Install python and pip3 ***Python is usually pre-installed on Amazon Linux 2023. However, if needed, follow the steps below:***

```bash (pwd : home/ec2-user)
# Verify that Python and pip are installed correctly by checking their versions.
python3 --version
pip3 --version

# Install python 3
sudo dnf install python3 -y

# sudo dnf install python3-pip -y
sudo dnf install python3-pip -y
```

- Install the most recent Docker Community Edition package.

```bash (pwd : home/ec2-user)
sudo dnf install docker -y
```

- Start docker service.

- Init System: Init (short for initialization) is the first process started during booting of the computer system. It is a daemon process that continues running until the system is shut down. It also controls services at the background. For starting docker service, init system should be informed.

```bash (pwd : home/ec2-user)
sudo systemctl start docker
```

- Enable docker service so that docker service can restart automatically after reboots.

```bash (pwd : home/ec2-user)
sudo systemctl enable docker
```

- Check if the docker service is up and running.

```bash (pwd : home/ec2-user)
sudo systemctl status docker
```

- Add the `ec2-user` to the `docker` group to run docker commands without using `sudo`.

```bash (pwd : home/ec2-user)
sudo usermod -a -G docker ec2-user
```

- Normally, the user needs to re-login into bash shell for the group `docker` to be effective, but `newgrp` command can be used activate `docker` group for `ec2-user`, not to re-login into bash shell.

```bash (pwd : home/ec2-user)
newgrp docker
```

- Check the docker version without `sudo`.

```bash (pwd : home/ec2-user)
$ docker version
Client:
 Version:           25.0.3
 API version:       1.44
 Go version:        go1.20.12
 Git commit:        4debf41
 Built:             Mon Feb 12 00:00:00 2024
 OS/Arch:           linux/amd64
 Context:           default

Server:
 Engine:
  Version:          25.0.3
  API version:      1.44 (minimum version 1.24)
  Go version:       go1.20.12
  Git commit:       f417435
  Built:            Mon Feb 12 00:00:00 2024
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          1.7.11
  GitCommit:        64b8a811b07ba6288238eefc14d898ee0b5b99ba
 runc:
  Version:          1.1.11
  GitCommit:        4bccb38cc9cf198d52bebf2b3a90cd14e7af8c06
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
```

- Check the docker info without `sudo`.

```bash (pwd : home/ec2-user)
$ docker info
Client:
 Version:    25.0.3
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.0.0+unknown
    Path:     /usr/libexec/docker/cli-plugins/docker-buildx

Server:
 Containers: 0
  Running: 0
  Paused: 0
  Stopped: 0
 Images: 3
 Server Version: 25.0.3
 Storage Driver: overlay2
  Backing Filesystem: xfs
  Supports d_type: true
  Using metacopy: false
  Native Overlay Diff: true
  userxattr: false
 Logging Driver: json-file
 Cgroup Driver: systemd
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 Swarm: inactive
 Runtimes: io.containerd.runc.v2 runc
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: 64b8a811b07ba6288238eefc14d898ee0b5b99ba
 runc version: 4bccb38cc9cf198d52bebf2b3a90cd14e7af8c06
 init version: de40ad0
 Security Options:
  seccomp
   Profile: builtin
  cgroupns
 Kernel Version: 6.1.79-99.167.amzn2023.x86_64
 Operating System: Amazon Linux 2023.4.20240319
 OSType: linux
 Architecture: x86_64
 CPUs: 1
 Total Memory: 949.6MiB
 Name: ip-172-31-89-214.ec2.internal
 ID: 6d116b23-6d49-4a92-852b-08483d90be43
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Experimental: false
 Insecure Registries:
  127.0.0.0/8
 Live Restore Enabled: false
```

- Install Docker Compose

- For Linux systems, after installing Docker, you need install Docker Compose separately. But, Docker Desktop App for Mac and Windows includes `Docker Compose` as a part of those desktop installs.

- Download the current stable release of `Docker Compose` executable.

```bash (pwd : home/ec2-user)
sudo curl -SL https://github.com/docker/compose/releases/download/v2.28.1/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
```

- Apply executable permissions to the binary:

```bash (pwd : home/ec2-user)
sudo chmod +x /usr/local/bin/docker-compose
```

- Check if the `Docker Compose`is working. Should see something like `Docker Compose version v2.26.0`

```bash (pwd : home/ec2-user)
docker-compose --version
```

# Part 2 - Create a Dockerfile :

- Create and save the Python application:

```bash (pwd :/home/ec2-user)
mkdir konzek && cd konzek
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

- Create a Docker Image `my-python-server`:

```bash (pwd :/home/ec2-user/konzek)
docker build -t my-python-server .
```

# Part 3 - Create a docker-compose.yml file

```bash (pwd :/home/ec2-user/konzek)
nano docker-compose.yml
```

```yaml   (docker-compose.yml)
version: '3.8'

services:
  app:
    image: my-python-server
    build:
      context: .
    ports:
      - "8080:8080"
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
    networks:
      - my-network

  proxy:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    networks:
      - my-network

networks:
  my-network:
    driver: bridge
```

# Part 4 - NGINX Reverse Proxy Configuration

- Create a `nginx.conf` file

```bash (pwd :/home/ec2-user/konzek)
nano nginx.conf
```

```sh (nginx.conf)
events {}

http {
    upstream app_servers {
        server app:8080;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://app_servers;
        }
    }
}
```

# Part 5 - Run Containers

- To start containers for both the application and the proxy, run the following commands in the terminal

- Verify the running containers

```bash (pwd :/home/ec2-user/konzek)
# docker-compose -f /path to your/docker-compose.yml up --build -d
docker-compose up --build -d
docker ps
```
