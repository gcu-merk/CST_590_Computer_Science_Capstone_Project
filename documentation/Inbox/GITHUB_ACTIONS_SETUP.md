# GitHub Actions Setup Guide for Raspberry Pi Deployment

This guide will help you set up automated deployment to your Raspberry Pi using GitHub Actions.

## 🎯 Overview

The deployment workflow automatically:
1. **Triggers** when the Docker build completes successfully on main branch
2. **Downloads** the latest docker-compose.yml from your repository
3. **Deploys** the latest Docker images to your Raspberry Pi
4. **Installs** Pi-specific packages (camera, GPIO, etc.)
5. **Verifies** the deployment was successful

## 📋 Prerequisites

### On Your Raspberry Pi

1. **Docker and Docker Compose installed**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo apt update
   sudo apt install docker-compose-plugin
   
   # Verify installation
   docker --version
   docker compose --version
   ```

2. **GitHub CLI installed** (for easier runner setup)
   ```bash
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh
   ```

## 🏃‍♂️ Setting Up Self-Hosted Runner

### Step 1: Create Runner on GitHub

1. Go to your repository: `https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project`
2. Click **Settings** → **Actions** → **Runners**
3. Click **New self-hosted runner**
4. Select **Linux** and **ARM64**
5. Follow the download and configuration instructions

### Step 2: Configure Runner on Raspberry Pi

```bash
# Create runner directory
mkdir actions-runner && cd actions-runner

# Download (replace with URL from GitHub)
curl -o actions-runner-linux-arm64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-arm64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-arm64-2.311.0.tar.gz

# Configure (use token from GitHub)
./config.sh --url https://github.com/gcu-merk/CST_590_Computer_Science_Capstone_Project --token YOUR_TOKEN_HERE

# Install as service
sudo ./svc.sh install

# Start service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

### Step 3: Verify Runner

1. Go back to **Settings** → **Actions** → **Runners**
2. You should see your Raspberry Pi listed as "Online"

## 🔐 Repository Secrets (If Needed)

If your Docker images are private, add these secrets in **Settings** → **Secrets and variables** → **Actions**:

- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token

## 🧪 Testing the Deployment

### Option 1: Automatic Trigger
1. Push changes to the `main` branch
2. The build workflow will run first
3. If successful, the deploy workflow will trigger automatically

### Option 2: Manual Trigger
1. Go to **Actions** → **Deploy to Raspberry Pi**
2. Click **Run workflow**
3. Check **Force deployment regardless of branch** if needed
4. Click **Run workflow**

## 📊 Monitoring Deployment

### GitHub Actions Dashboard
1. Go to the **Actions** tab in your repository
2. Click on the latest **Deploy to Raspberry Pi** workflow
3. Monitor progress in real-time

### On Raspberry Pi
```bash
# Check runner logs
sudo journalctl -u actions.runner.* -f

# Check Docker containers
docker ps

# Check container logs
cd ~/traffic-monitor-deploy
docker compose logs -f

# Check system resources
htop
docker stats
```

## 🔧 Troubleshooting

### Runner Not Starting
```bash
# Check runner service
sudo systemctl status actions.runner.*

# Restart runner service
sudo ./svc.sh stop
sudo ./svc.sh start

# Check logs
sudo journalctl -u actions.runner.* -n 50
```

### Deployment Failures
```bash
# Check disk space
df -h

# Check Docker daemon
sudo systemctl status docker

# Manual deployment test
cd ~/traffic-monitor-deploy
docker compose down
docker compose pull
docker compose up -d
```

### Container Issues
```bash
# Check container health
docker compose ps
docker compose logs

# Restart containers
docker compose restart

# Clean up and redeploy
docker compose down --volumes
docker system prune -f
docker compose up -d
```

## 📁 Deployment Directory Structure

The deployment creates this structure on your Pi:
```
/home/username/traffic-monitor-deploy/
├── docker-compose.yml    # Downloaded from repository
└── (Docker volumes and data)
```

## 🌐 Access Your Application

After successful deployment:
- **Dashboard**: `http://[PI-IP]:5000`
- **API Health**: `http://[PI-IP]:5000/api/health`
- **Logs**: `docker compose logs -f`

## 🔄 Workflow Details

### Build Workflow (`docker-build-push.yml`)
- Builds Docker image for ARM64
- Pushes to Docker Hub
- Triggers deployment on success

### Deploy Workflow (`deploy-to-pi.yml`)
- Runs on self-hosted Raspberry Pi
- Downloads latest configuration
- Deploys containers with health checks
- Installs Pi-specific packages

## 📝 Next Steps

1. **Set up the self-hosted runner** following Step 2
2. **Test manual deployment** using the workflow dispatch
3. **Push to main branch** to test automatic deployment
4. **Monitor the dashboard** for successful operation

## 🆘 Support

If you encounter issues:
1. Check the **Actions** tab for detailed logs
2. SSH into your Pi and check container status
3. Review the troubleshooting section above
4. Check repository issues or create a new one

---

**Happy Deploying! 🚀**
