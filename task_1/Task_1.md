# Part 1 - Launch en EC2 instance and install python

- Launch an EC2 instance using the Amazon Linux 2023 AMI with security group allowing SSH connections.
***`instance type` : t2.micro ; `Security Group Ports` = 22 (Allow SSH (port 22) only for your own IP address.), 80, 8080 (HTTP (port 80) and Custom TCP Rule (port 8080) for 0.0.0.0/0)***

- Connect to your instance with SSH.

```bash (pwd :/home/ec2-user)
ssh -i .ssh/"key-pair.pem" ec2-user@your-ec2-public-ip
# ssh -i "key-pair.pem" ec2-user@your-ec2-public-ipD
```

- Update the installed packages and package cache on your instance.

```bash (pwd :/home/ec2-user)
sudo dnf update -y
```

- Install python and pip3 ***Python is usually pre-installed on Amazon Linux 2023. However, if needed, follow the steps below:***

```bash (pwd :/home/ec2-user)
# Verify that Python and pip are installed correctly by checking their versions.
python3 --version
pip3 --version

# Install python 3
sudo dnf install python3 -y

# sudo dnf install python3-pip -y
sudo dnf install python3-pip -y
```

- Creating Log Files and Setting Permissions:

```bash (pwd : home/ec2-user)
sudo touch /var/log/my_service.log
sudo touch /var/log/my_service_error.log
sudo chown ec2-user:ec2-user /var/log/my_service.log /var/log/my_service_error.log
sudo chmod 644 /var/log/my_service.log /var/log/my_service_error.log
```

# Part 2 - Writing the Python Application :

- Create and save the Python application:

```bash (pwd :/home/ec2-user)
mkdir konzek && cd konzek
nano my_server.py
```

- Here is a simple example of a Python HTTP server:

```py   (my_server.py)
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Send an HTTP 200 response
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Hello, World! This is a Python HTTP server made by Alparslan.")

if __name__ == "__main__":
    # Start the server on port 8080
    server = HTTPServer(("0.0.0.0", 8080), SimpleHandler)
    print("Starting server on port 8080...")
    server.serve_forever()
```

# Part 3 - Writing a Systemd Unit File

***We will create a systemd unit file to run as a service.***

- Systemd Dosyasını (my_service.service) Oluştur:

```bash (pwd : home-ec2-user)
sudo nano /etc/systemd/system/my_service.service
```

- Write the following content to a file:

***`ExecStart`: Specify the full path of the Python application.***
***`User`: Specify the user under which the service will run. Enter your username.***
***`StandardOutput ve StandardError`: It saves the exit logs to the specified files.***

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

# Part 4 -  Running and Testing the Service

- Reload systemd and enable the service:

```bash (pwd :/home/ec2-user)
sudo systemctl daemon-reload
sudo systemctl enable my_service.service
```

- Start the service

```bash (pwd :/home/ec2-user)
sudo systemctl start my_service.service
```

- (Optional) Restart the service if any configuration changes were made:

```bash (pwd :/home/ec2-user)
sudo systemctl restart my_service.service
```

- Check the status of the service

```bash (pwd :/home/ec2-user)
sudo systemctl status my_service.service
```

# Part 5 - Test the connection in the Security Group.

- Make sure port 8080 is open in the EC2 security group.

- AWS Console → EC2 → Instance Settings → Security Groups → Edit Inbound Rules.

- Allow port 8080.

- Test using a browser or curl:

- Browser : http://your-ec2-public-ip:8080

- Curl    : ***You should see `Hello, World! This is a Python HTTP server.` as the output.***

``` bash
curl http://your-ec2-public-ip:8080
```

# Part 6 - Check the log files

- Check the exit logs:

```bash (pwd :/home/ec2-user)
cat /var/log/my_service.log
```

- Check the error logs (if any):

```bash (pwd :/home/ec2-user)
cat /var/log/my_service_error.log
```
