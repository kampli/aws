import boto3
import json


ec2 = boto3.client('ec2')
asg = boto3.client('autoscaling')
ib = boto3.client("imagebuilder")

def get_pipeline_arn_by_name(pipeline_name: str) -> str:
    """
    Resolve Image Builder pipeline ARN from pipeline name
    """
    paginator = ib.get_paginator("list_image_pipelines")

    for page in paginator.paginate():
        for p in page["imagePipelineList"]:
            if p["name"] == pipeline_name:
                return p["arn"]

    raise Exception(f"Image Builder pipeline not found: {pipeline_name}")


def get_latest_ami_from_pipeline(pipeline_name: str) -> str:
    """
    Return latest AVAILABLE AMI ID from Image Builder pipeline name
    """
    pipeline_arn = get_pipeline_arn_by_name(pipeline_name)

    paginator = ib.get_paginator("list_image_pipeline_images")

    images = []
    for page in paginator.paginate(imagePipelineArn=pipeline_arn):
        images.extend(page["imageSummaryList"])

    # Only images that completed successfully
    available = [
        img for img in images
        if img["state"]["status"] == "AVAILABLE"
    ]

    if not available:
        raise Exception(f"No AVAILABLE images for pipeline {pipeline_name}")

    latest = max(available, key=lambda x: x["dateCreated"])

    # Return first AMI (single-region pipeline)
    return latest["outputResources"]["amis"][0]["image"]


def handler(event, context):
 
    latest_ami_id = get_latest_ami_from_pipeline(pipeline_name='lamp-ec2-web')


    print(f"Latest AMI from {pipeline_name}: {latest_ami_id}")

    # Restore ASG capacity
    asg.update_auto_scaling_group(
        AutoScalingGroupName='LampAutoScalingGroup',
        MinSize=2,
        MaxSize=3,
        DesiredCapacity=2
    )
    # Restore ASG capacity
    asg.update_auto_scaling_group(
        AutoScalingGroupName='LampAutoScalingGroup',
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=1
    )
