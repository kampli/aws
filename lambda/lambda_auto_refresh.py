from enum import auto
import boto3
import json
import os
from datetime import datetime

LAUNCH_TEMPLATE_NAME = "lamp-stack-ec2-LaunchTemplate"
ASG_NAME= "LampAutoScalingGroup"
IMAGE_PIPELINE_NAME = "lamp-ec2-web"


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

def get_launch_template_id(name: str) -> str:
    resp = ec2.describe_launch_templates(
        LaunchTemplateNames=[name]
    )
    return resp["LaunchTemplates"][0]["LaunchTemplateId"]


def handler(event, context):
    
    print("Received event:", event)

    # 1️⃣ Launch Template
    lt_id = get_launch_template_id(LAUNCH_TEMPLATE_NAME)
    print("LaunchTemplateId:", lt_id)

    pipeline_name = 'lamp-ec2-web'
    
    latest_ami_id = get_latest_ami_from_pipeline(pipeline_name)


    print(f"Latest AMI from {pipeline_name}: {latest_ami_id}")


    new_version = ec2.create_launch_template_version(
        LaunchTemplateId=lt_id,
        SourceVersion="$Latest",
        LaunchTemplateData={
            "ImageId": latest_ami_id
        }
    )["LaunchTemplateVersion"]["VersionNumber"]

    print("New LT version:", new_version)

    # 4️⃣ Set default
    ec2.modify_launch_template(
        LaunchTemplateId=lt_id,
        DefaultVersion=str(new_version)
    )

    
    #Below code to udpate the latest launch template version.
    #This doesnt work due to permission issues.
    #Work around is to udpate the launch template version in ASG to latest version in the console.

    asg.update_auto_scaling_group(AutoScalingGroupName=ASG_NAME,LaunchTemplate={
        'LaunchTemplateId': lt_id,
        'Version': str(new_version)})
    


    resp = asg.start_instance_refresh(
        AutoScalingGroupName=ASG_NAME,
        Preferences={
            "MinHealthyPercentage": 100,
            "InstanceWarmup": 300
        },
        Strategy="Rolling"
    )


    # # Restore ASG capacity
    # asg.update_auto_scaling_group(
    #     AutoScalingGroupName='LampAutoScalingGroup',
    #     MinSize=2,
    #     MaxSize=3,
    #     DesiredCapacity=2
    # )
    # # Restore ASG capacity
    # asg.update_auto_scaling_group(
    #     AutoScalingGroupName='LampAutoScalingGroup',
    #     MinSize=1,
    #     MaxSize=3,
    #     DesiredCapacity=1
    # )
