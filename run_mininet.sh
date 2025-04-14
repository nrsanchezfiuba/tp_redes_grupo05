#!/bin/bash

IMAGE_NAME="mininet_img"

if [ "$1" == "build" ]; then
    docker build -t $IMAGE_NAME -f ./mininet/Dockerfile.mininet ./mininet/
elif [ "$1" == "run" ]; then
    shift
    docker run -it --rm --privileged --net=host \
        -e DISPLAY \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v /lib/modules:/lib/modules \
        -v $(pwd):/root \
        $IMAGE_NAME "$@"
else
    echo "Usage: $0 {build|run} [docker_run_args...]"
    exit 1
fi

