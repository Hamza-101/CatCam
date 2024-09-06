# Turn wifi on start up

import subprocess
import time
import os

class WiFiManager:
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.profile_path = "wifi_profile.xml"
        self.ssid = None
        self.password = None
        self.load_credentials()

    def load_credentials(self):
        """Load credentials from the specified file."""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")

        with open(self.credentials_path, 'r') as file:
            for line in file:
                name, value = line.strip().split('=')
                if name == "SSID":
                    self.ssid = value
                elif name == "PASSWORD":
                    self.password = value

        if not self.ssid or not self.password:
            raise ValueError("SSID or Password is missing in the credentials file.")

    def check_interface_status(self):
        """Check and enable the Wi-Fi interface if needed."""
        try:
            result = subprocess.run(["netsh", "interface", "show", "interface", "Wi-Fi"], capture_output=True, text=True)
            print(result.stdout)
            if "Disabled" in result.stdout:
                print("Wi-Fi interface is disabled, enabling it...")
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=enable"], check=True)
                time.sleep(5)  # Wait a bit to ensure the interface is fully enabled
            elif "Connected" not in result.stdout:
                print("Wi-Fi interface is not connected, ensuring it's active...")
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=enable"], check=True)
                time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"Failed to check or enable Wi-Fi interface: {e}")

    def create_wifi_profile(self):
        """Create a Wi-Fi profile XML file."""
        profile = f"""
        <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
            <name>{self.ssid}</name>
            <SSIDConfig>
                <SSID>
                    <name>{self.ssid}</name>
                </SSID>
            </SSIDConfig>
            <connectionType>ESS</connectionType>
            <connectionMode>auto</connectionMode>
            <MSM>
                <security>
                    <authEncryption>
                        <authentication>WPA2PSK</authentication>
                        <encryption>AES</encryption>
                        <useOneX>false</useOneX>
                    </authEncryption>
                    <sharedKey>
                        <keyType>passPhrase</keyType>
                        <protected>false</protected>
                        <keyMaterial>{self.password}</keyMaterial>
                    </sharedKey>
                </security>
            </MSM>
            <MacRandomization xmlns="http://www.microsoft.com/networking/WLAN/profile/v3">
                <enableRandomization>false</enableRandomization>
            </MacRandomization>
        </WLANProfile>
        """
        with open(self.profile_path, 'w') as file:
            file.write(profile)

    def connect(self):
        """Connect to the specified Wi-Fi network."""
        try:
            # Check and ensure the Wi-Fi interface is properly enabled
            self.check_interface_status()

            # Create the Wi-Fi profile XML
            self.create_wifi_profile()

            # Add the Wi-Fi profile and connect
            subprocess.run(["netsh", "wlan", "add", "profile", f"filename={self.profile_path}"], check=True)
            subprocess.run(["netsh", "wlan", "connect", self.ssid], check=True)
            print(f"Connected to {self.ssid}")

            # Check if the connection was successful
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
            if self.ssid in result.stdout:
                return 1  # Connection successful
            else:
                return 0  # Connection failed

        except subprocess.CalledProcessError as e:
            print(f"Failed to connect to {self.ssid}: {e}")
            return 0  # Connection failed

if __name__ == "__main__":
    try:
        wifi_manager = WiFiManager('..\Repository\AccessControl\WiFiDevices.txt')
        connection_status = wifi_manager.connect()
        print(f"Connection status: {connection_status}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Also make it all into a class where I can have a way to just call something and it does all this rerturning 1 if connected