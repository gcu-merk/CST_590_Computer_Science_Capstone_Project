# First, backup the original SSH config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Disable password authentication
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Disable challenge response authentication
sudo sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config

# Disable PAM authentication
sudo sed -i 's/#UsePAM yes/UsePAM no/' /etc/ssh/sshd_config
sudo sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

# Ensure public key authentication is enabled
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Restart SSH service to apply changes
sudo systemctl restart ssh

# Verify the configuration
echo "Configuration applied. Current relevant SSH settings:"
sudo grep -E "^(Password|Pubkey|Challenge|UsePAM)" /etc/ssh/sshd_config