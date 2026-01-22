import pymysql
import os
import logging
import traceback
import socket
import requests
import urllib.request
import json


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DB_HOST = os.environ['DB_HOST']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_NAME = os.environ['DB_NAME']
LAMBDA_AWS_REGION = os.environ['LAMBDA_AWS_REGION']
LAMBDA_AWS_STACK = os.environ['LAMBDA_AWS_STACK']


def get_az():
    try:
        # Lambda metadata endpoint for container info
        token_url = "http://169.254.169.254/latest/api/token"
        token = requests.put(token_url, headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}).text

        # Get AZ
        az_url = "http://169.254.169.254/latest/meta-data/placement/availability-zone"
        
        az = requests.get(az_url, headers={"X-aws-ec2-metadata-token": token}).text

        return az
    except Exception as e:
        return "unknown" + traceback.format_exc()
    

def get_az_urllib():
    try:
        # 1️⃣ Get IMDSv2 token
        token_req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={
                "X-aws-ec2-metadata-token-ttl-seconds": "21600"
            }
        )
        with urllib.request.urlopen(token_req, timeout=1) as response:
            token = response.read().decode()

        # 2️⃣ Use token to get AZ
        az_req = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/placement/availability-zone",
            headers={
                "X-aws-ec2-metadata-token": token
            }
        )
        with urllib.request.urlopen(az_req, timeout=1) as response:
            az = response.read().decode()

        return az

    except Exception:
        return "unknown"

def handler(event, context):

    

    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=5
    )

    try:

        hostname = socket.gethostname()
        logger.info("Hostname (logger): %s", hostname)

        az = get_az()
        az_url_lib = get_az_urllib()
        print(json.dumps(event))
        json_dump = json.dumps(event)


        ec2_metadata = event.get('ec2_metadata', {})

        ec2_az = ec2_metadata.get('availability_zone')
        ec2_region = ec2_metadata.get('region')
        ec2_instance_id = ec2_metadata.get('instance_id')
        ec2_private_ip = ec2_metadata.get('private_ip')

        with connection.cursor() as cursor:
            # 1️⃣ Count rows before insert
            cursor.execute("SELECT COUNT(*) FROM logs")
            before_count = cursor.fetchone()[0]
            logger.info(f"Row count before insert: {before_count}")

            # 2️⃣ Insert log entry
            sql = "INSERT INTO logs(message) VALUES(%s)"
            cursor.execute(sql, ("Lambda invoked",))
            connection.commit()

            # 3️⃣ Count rows after insert
            cursor.execute("SELECT COUNT(*) FROM logs")
            after_count = cursor.fetchone()[0]
            logger.info(f"Row count after insert: {after_count}")

        return {
            "status": "success",
            "row_count_before": before_count,
            "row_count_after": after_count,
            "hostname": hostname,
            "availability_zone_url_lib": az_url_lib,
            "LAMBDA_AWS_REGION": LAMBDA_AWS_REGION,
            "LAMBDA_AWS_STACK": LAMBDA_AWS_STACK,
            "ec2_metadata": {
                "ec2_az": ec2_az,
                "ec2_region": ec2_region,
                "ec2_instance_id": ec2_instance_id,
                "ec2_private_ip": ec2_private_ip
            },
            "json_dump": json_dump,
            "availability_zone": az
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        connection.close()
