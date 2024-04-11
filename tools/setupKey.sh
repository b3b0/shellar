#!/bin/bash
clear
setup_success=true

if [ ! -f ~/.ssh/id_rsa ]; then
    echo "No SSH key found. Generating a new one..."
    if ! command -v ssh-keygen &> /dev/null; then
        echo "ssh-keygen not found. Please install it using your package manager."
        setup_success=false
    else
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    fi
fi

if [ "$setup_success" = true ]; then
    echo "Trying to authenticate with the server using the SSH key..."
    ssh -o BatchMode=yes -o StrictHostKeyChecking=no "$1@$2" exit

    if [ $? -ne 0 ]; then
        echo "Authentication failed. Attempting to copy SSH key to the server..."
        if ! command -v ssh-copy-id &> /dev/null; then
            echo "ssh-copy-id not found. Please install it using your package manager."
            setup_success=false
        else
            ssh-copy-id "$1@$2"
        fi
    fi
fi

if [ "$setup_success" = true ]; then
    echo "Connecting to $2 as $1..."
    ssh "$1@$2"
else
    echo "SSH setup failed. Please resolve the issues and try again."
fi