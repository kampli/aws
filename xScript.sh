#!/bin/bash

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
    aws cloudformation update-stack \
        --stack-name lamp-stack \
        --template-body file://aws_CF_LAMP_Template.yaml \
        --parameters ParameterKey=KeyName,ParameterValue=testkeypair
}

function updateStack() {
    aws cloudformation update-stack \
        --stack-name lamp-stack \
        --template-body file://aws_CF_LAMP_Template.yaml \
        --parameters ParameterKey=KeyName,ParameterValue=testkeypair
}

function deleteStack() {
    aws cloudformation delete-stack \
        --stack-name lamp-stack
}

if [ $# -gt 0 ] ; then
    ${@}
else
    echo "Invalid call"
    listFunctions

fi

