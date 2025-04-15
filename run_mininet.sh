#!/bin/bash

IMAGE_NAME="mininet_img"

export XAUTHORITY=$HOME/.Xauthority

run_docker() {
    shift
    docker run -it --rm --privileged --net=host \
        -e DISPLAY="$DISPLAY" \
        -e XAUTHORITY="$XAUTHORITY" \
        -v "$XAUTHORITY":"$XAUTHORITY" \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v /lib/modules:/lib/modules \
        -v "$(pwd)":/root/project \
        "$IMAGE_NAME" "$@"
}

if [ "$1" == "build" ]; then
    docker build -t $IMAGE_NAME -f ./mininet/Dockerfile.mininet ./mininet/
elif [ "$1" == "run" ]; then
    export DISPLAY=':0'
    run_docker
elif [ "$1" == "run-ssh" ]; then
    export DISPLAY='localhost:10.0'
    run_docker
else
    echo "Usage: $0 {build|run} [docker_run_args...]"
    exit 1
fi
