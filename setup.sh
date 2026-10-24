# Fix 1: Added -r so pip reads the file instead of searching for a package named "requirements.txt"
python3 -m pip install -r requirements.txt --break-system-packages

echo "What is your printer's IP, Access Code and serial number? Separate by Return, finish by ^D."
cat > cfg.txt
python3 back.py &

read -n 1 -s -r -p "Set up Pizza Lab as a systemd service? "
echo "" # Prints a clean newline after your prompt

SERVICE_FILE="/etc/systemd/system/pizzalab.service"
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=There is always Pizza in this Lab.
After=network.target

[Service]
Type=simple
# Fix 2: Tells systemd where your code lives so it can find cfg.txt and templates/
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/back.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set standard permissions
chmod 644 "$SERVICE_FILE"

# Reload systemd so it instantly detects the new file you just created
systemctl daemon-reload

systemctl enable pizzalab
echo "Pizza Lab has been set up as a systemd service."
