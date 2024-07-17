import paramiko
import os
import google.auth
from google.cloud import secretmanager
import io

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "aid-warehouse-prd-3c076acc2985.json"

try:
    credentials, project = google.auth.default()
    print("AUTHENTICATED TO GCP")
except google.auth.exceptions.DefaultCredentialsError:
    print("FAILED AUTHENCTICATION CHECK YOUR SA")

secretClient = secretmanager.SecretManagerServiceClient()
secretProjectID = "13748414480"

def fetch_secret(secretName, secretProjectID, secretClient):
  try:
      request = {"name": f"projects/{secretProjectID}/secrets/{secretName}/versions/latest"}
      return secretClient.access_secret_version(request).payload.data.decode("UTF-8")
  except:
      raise Exception("Secret could not be fetched")  


def sftp_connection(entity):
    print("SFTP CONNECT")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if entity == "algo":
            print("SAT SFTP CONNECTION")
            host = '34.101.131.174'
            username = 'algo_payment'
            password = 'M72JgYUb'
            port = 2202

            # Kalo pake path file di local uncomment 2 baris di bawah trus buka comment yang 3 baris secret gcp 
            # (Kalo dari rumah pake vpn cisco untuk local file)
            # key_file = 'algo_payment.ppk' 
            # private_key = paramiko.RSAKey.from_private_key_file(key_file, password=password)

            # secret gcp
            secretKey = fetch_secret("algo_payment_privkey", secretProjectID, secretClient)
            key_file = io.StringIO(secretKey)
            private_key = paramiko.RSAKey.from_private_key(key_file, password=password)
            
            ssh.connect(hostname=host, port=port, username=username, pkey=private_key)

        else:
            print("BRI SFTP CONNECTION")
            host = '103.63.96.56'
            port = 20022
            username = 'H2H_ALGO_USR2024'
            password = 'husLG764278'

            # Kalo pake path file di local uncomment 2 baris \di bawah trus buka commen 3 baris yang secret gcp 
            # (Kalo dari rumah pake vpn cisco untuk local file)
            key_file = 'bri.pem'
            private_key = paramiko.RSAKey.from_private_key_file(key_file, password=password)
            # private_key = paramiko.RSAKey.from_private_key_file(key_file, password=password)

            # secret gcp
            # secretKey = fetch_secret("algo_bri_b2b_privkey", secretProjectID, secretClient)
            # key_file = io.StringIO(secretKey)
            # private_key = paramiko.RSAKey.from_private_key(key_file, password=password)
            disabled_algorithms = {
                'pubkeys': ['rsa-sha2-512', 'rsa-sha2-256']
            }

            ssh.connect(hostname=host, port=port, username=username, pkey=private_key, disabled_algorithms=disabled_algorithms)
       
        sftp = ssh.open_sftp()
        print("Listing directory:")
        for filename in sftp.listdir('.'):
            print(filename)
            
        local_file_path = "algo_bri.pem"
        remote_file_path = "/ingoing/aaa.pem"
        sftp.put(local_file_path, remote_file_path)

        sftp.close()
        print("SFTP connection closed.")

    except Exception as e:
        sftp = f"Error: {e}"
        print(f"Error: {e}")

    finally:
        ssh.close()
        print("SSH connection closed.")
    
    return f"SFTP - {sftp}"

# Pilih entity algo atau bri
entity = 'bri'
sftp_connection(entity)

# NOTES:
# library yang harus di install klo mau konek ke GCP
# pip install google-cloud-secretmanager
# pip install google-auth