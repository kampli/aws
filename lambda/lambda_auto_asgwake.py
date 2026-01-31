import boto3
import json


ec2 = boto3.client('ec2')
asg = boto3.client('autoscaling')

def handler(event, context):
    # Start EC2 instances
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:AutoStop', 'Values': ['true']},
            {'Name': 'instance-state-name', 'Values': ['stopped']}
        ]
    )

    for r in instances.get('Reservations', []):
        for i in r.get('Instances', []):
            print(i['InstanceId'])

    instance_ids = [
        i['InstanceId']
        for r in instances['Reservations']
        for i in r['Instances']
    ]

    if instance_ids:
        ec2.start_instances(InstanceIds=instance_ids)

    # Restore ASG capacity
    asg.update_auto_scaling_group(
        AutoScalingGroupName='LampAutoScalingGroup',
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=1
    )


    html = """
        <!DOCTYPE html>
        <html>
        <head>
        <title>Waking up…</title>
        <meta http-equiv="refresh" content="30;url=/" />
        <style>
            body {
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            }
            .card {
            background: #020617;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            max-width: 420px;
            }
            h1 { margin-bottom: 10px; }
            p { opacity: 0.85; }
            .spinner {
            margin: 20px auto;
            width: 40px;
            height: 40px;
            border: 4px solid #334155;
            border-top: 4px solid #38bdf8;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            }
            @keyframes spin {
            to { transform: rotate(360deg); }
            }
        </style>
        <script>
            setTimeout(() => {
            window.location.href = "/";
            }, 300000);
        </script>
        </head>
        <body>
        <div class="card">
            <h1>🚀 Waking things up</h1>
            <div class="spinner"></div>
            <p>Your application is starting.</p>
            <p>You’ll be redirected automatically in ~300 seconds.</p>
        </div>
        </body>
        </html>
        """


    return {
        "statusCode": 200,
        "statusDescription": "200 OK",
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": html
    }
    