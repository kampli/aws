import boto3

asg = boto3.client('autoscaling')

def handler(event, context):
    asg.update_auto_scaling_group(
        AutoScalingGroupName='LampAutoScalingGroup',
        MinSize=1,
        MaxSize=2,
        DesiredCapacity=1
    )

    return {
        "statusCode": 503,
        "body": "Backend waking up. Please retry in ~30 seconds."
    }