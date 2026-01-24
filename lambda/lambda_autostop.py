import boto3

ec2 = boto3.client('ec2')
asg = boto3.client('autoscaling')

def handler(event, context):
    # Stop EC2 instances
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:AutoStop', 'Values': ['true']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    instance_ids = [
        i['InstanceId']
        for r in instances['Reservations']
        for i in r['Instances']
    ]

    if instance_ids:
        ec2.stop_instances(InstanceIds=instance_ids)

    # Scale ASGs to zero
    groups = asg.describe_auto_scaling_groups()['AutoScalingGroups']

    for g in groups:
        tags = {t['Key']: t['Value'] for t in g['Tags']}
        if tags.get('AutoStop') == 'true':
            asg.update_auto_scaling_group(
                AutoScalingGroupName=g['AutoScalingGroupName'],
                MinSize=0,
                MaxSize=0,
                DesiredCapacity=0
            )
