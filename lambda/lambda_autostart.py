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
