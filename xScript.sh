#!/bin/bash

export AWS_PROFILE=kamplidev


function listFunctions() {

    grep function $0 | egrep -v "listFunctions|^ *#" | sed 's/ *function //g' | sed 's/(.*//g' | sed 's/ .*//g' | sort

}

function addFilesToRepo() {

    git add ${@}
    git commit -m "adding to repo ${@}"

    git push
}


function updateFilesToRepo() {

    git add ${@}
    git commit -m "Updating to repo ${@}"

    git push
}

function createStack() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    aws cloudformation create-stack \
        --stack-name lamp-stack \
        --template-body file://aws_CF_LAMP_Template.yaml \
        --parameters ParameterKey=KeyName,ParameterValue=testkeypair
}

function updateStack() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    aws cloudformation update-stack \
        --stack-name lamp-stack \
        --template-body file://aws_CF_LAMP_Template.yaml \
        --parameters ParameterKey=KeyName,ParameterValue=testkeypair
}

function deleteStack() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    aws cloudformation delete-stack \
        --stack-name lamp-stack
}

function getOutputs() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    aws cloudformation describe-stacks \
        --stack-name lamp-stack \
        --query "Stacks[0].Outputs"
}

function loginToEC2() {
    echo "getting IP Address for the EC2 instance"
    aws cloudformation describe-stacks \
        --stack-name lamp-stack \
        --query "Stacks[0].Outputs[?OutputKey=='InstancePublicIP'].OutputValue" \
        --output text
    
    ipAddress_EC2=$(aws cloudformation describe-stacks \
                        --stack-name lamp-stack \
                        --query "Stacks[0].Outputs[?OutputKey=='InstancePublicIP'].OutputValue" \
                        --output text);
    echo "ipAddress_EC2 = ${ipAddress_EC2}"
    ssh -o StrictHostKeyChecking=accept-new -i ./testkeypair.pem ec2-user@${ipAddress_EC2}
}

if [ $# -gt 0 ] ; then
    ${@}
else
    echo "Invalid call"
    listFunctions

fi

