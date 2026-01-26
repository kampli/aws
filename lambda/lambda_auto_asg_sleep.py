import boto3

asg = boto3.client('autoscaling')

def handler(event, context):
    asg.update_auto_scaling_group(
        AutoScalingGroupName='LampAutoScalingGroup',
        MinSize=0,
        MaxSize=2,
        DesiredCapacity=0
    )