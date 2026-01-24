#!/bin/bash

export AWS_PROFILE=kamplidev
#export AWS_PROFILE=default


export lambdaS3BucketName="lamp-lambda-artifacts-725673811658-eu-west-2";

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

function validateTemplate() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    aws cloudformation validate-template \
        --template-body file://aws_CF_LAMP_Template.yaml
}

function createStack() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    echo $(date)
    status=~$(aws cloudformation create-stack \
        --stack-name lamp-stack \
        --capabilities CAPABILITY_NAMED_IAM \
        --template-body file://aws_CF_LAMP_Template.yaml \
        --parameters ParameterKey=KeyName,ParameterValue=testkeypair \
                     ParameterKey=DBRootPassword,ParameterValue=kampli00 \
                     ParameterKey=HostedZoneId,ParameterValue=${HOSTZONEID} 2>&1)
    echo ${status}
                     
}
function createStackLoop() {
    status=$(createStack)
    echo "status -- ${status}"
    isError=`echo ${status} | grep -i 'error'`
    echo "isError -- ${isError}"
    while [ "${isError}"  != "" ] 
    do
        echo "Sleeping.... zzz"
        sleep 10
        status=$(createStack)
        echo "status -- ${status}"
        isError=`echo ${status} | grep -i 'error'`
        echo "isError -- ${isError}"
    done
}

function createChangeSet() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    
    aws cloudformation create-change-set \
        --stack-name lamp-stack \
        --change-set-name lamp-stack-changeset \
        --use-previous-template \
        --parameters ParameterKey=KeyName,ParameterValue=testkeypair \
                     ParameterKey=DBRootPassword,ParameterValue=kampli00 \
                     ParameterKey=HostedZoneId,ParameterValue=${HOSTZONEID} 
        
        # --template-body file://aws_CF_LAMP_Template.yaml \
}

function listChangeSets() {

    aws cloudformation list-change-sets \
        --stack-name lamp-stack

}



function updateStack() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    echo $(date)
    status=$(aws cloudformation update-stack \
        --stack-name lamp-stack \
        --template-body file://aws_CF_LAMP_Template.yaml \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameters ParameterKey=KeyName,ParameterValue=testkeypair \
                     ParameterKey=DBRootPassword,ParameterValue=kampli00 \
                     ParameterKey=HostedZoneId,ParameterValue=${HOSTZONEID} 2>&1)
    echo ${status}    
}

function updateStackLoop() {
    status=$(updateStack)
    echo "status -- ${status}"
    isError=`echo ${status} | grep -i 'error'`
    echo "isError -- ${isError}"
    while [ "${isError}"  != "" ] 
    do
        echo "Sleeping.... zzz"
        sleep 10
        status=$(updateStack)
        echo "status -- ${status}"
        isError=`echo ${status} | grep -i 'error'`
        echo "isError -- ${isError}"
    done
}

function deleteStack() {

    echo "AWS_PROFILE == ${AWS_PROFILE}"
    echo $(date)
    status=$(aws cloudformation delete-stack \
        --stack-name lamp-stack 2>&1)
    echo ${status}
}

function deleteStackLoop() {
    status=$(deleteStack)
    echo "status -- ${status}"
    isError=`echo ${status} | grep -i 'error'`
    echo "isError -- ${isError}"
    while [ "${isError}"  != "" ] 
    do
        echo "Sleeping.... zzz"
        sleep 10
        status=$(deleteStack)
        echo "status -- ${status}"
        isError=`echo ${status} | grep -i 'error'`
        echo "isError -- ${isError}"
    done
}

function getOutputs() {
    echo "AWS_PROFILE == ${AWS_PROFILE}"
    aws cloudformation describe-stacks \
        --stack-name lamp-stack \
        --query "Stacks[0].Outputs"
}

function getIPAddress() {
    ipAddress_EC2=$(aws cloudformation describe-stacks \
                        --stack-name lamp-stack \
                        --query "Stacks[0].Outputs[?OutputKey=='InstancePublicIP'].OutputValue" \
                        --output text);
    echo "${ipAddress_EC2}"
    
}

function getPublicDNS() {
    publicDNS=$(aws cloudformation describe-stacks \
                        --stack-name lamp-stack \
                        --query "Stacks[0].Outputs[?OutputKey=='PublicDNS'].OutputValue" \
                        --output text);
    echo "${publicDNS}"
    
}

function loginToEC2() {
    
    ipAddress_EC2=$(getIPAddress);
    echo "ipAddress_EC2 = ${ipAddress_EC2}"
    chmod 600 testkeypair.pem
    ls -l testkeypair.pem
    ssh -o StrictHostKeyChecking=accept-new -i ./testkeypair.pem ec2-user@${ipAddress_EC2}
}


function openURLs() {
    
    ipAddress_EC2=$(getIPAddress);
    publicDNS_EC2=$(getPublicDNS)
    echo "ipAddress_EC2 = ${ipAddress_EC2}"
    echo -e "   URLs = 
                http://${ipAddress_EC2}
                https://${ipAddress_EC2}
                http://${publicDNS_EC2}
                https://${publicDNS_EC2}
                "
    open "http://${ipAddress_EC2}" "https://${ipAddress_EC2}" http://${publicDNS_EC2} https://${publicDNS_EC2}
}

function updateLambdaOnS3() {
    cd lambda
    rm -f lambda.zip
    zip -r lambda.zip *.py
    cd ..

    bucketExists=$(aws s3 ls ${lambdaS3BucketName} 2>&1 | grep -io "NoSuchBucket")

    if [ "${bucketExists}" != ""] ; then
        aws s3 mb --region eu-west-2 s3://${lambdaS3BucketName}
    fi
    
    aws s3 rm s3://${lambdaS3BucketName}/lambda.zip
    aws s3 cp lambda/lambda.zip s3://${lambdaS3BucketName}/lambda.zip


    mkdir -p layer
    cd layer
    mkdir -p python
    pip install pymysql -t python
    pip install requests -t python

    zip -r pymysql-layer.zip python
    cd ..

    aws s3 rm s3://${lambdaS3BucketName}/pymysql-layer.zip

    aws s3 cp layer/pymysql-layer.zip s3://${lambdaS3BucketName}/pymysql-layer.zip

}

if [ $# -gt 0 ] ; then
    ${@}
else
    echo "List of functions supported:"
    listFunctions
fi

