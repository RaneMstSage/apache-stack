#!/bin/bash

# Push built containers to Docker Hub
# Run this after build-and-push.sh or manual builds

DOCKER_USER="ranemstsage"
TAG="latest"

echo "=========================================="
echo "Pushing Apache Stack Containers to Docker Hub"
echo "=========================================="
echo ""
echo "Note: You must be logged in to Docker Hub"
echo "Run: docker login -u $DOCKER_USER"
echo ""

# Function to push a container
push_image() {
    local NAME=$1
    local IMAGE="$DOCKER_USER/apache-stack-$NAME:$TAG"
    
    echo "Pushing $IMAGE..."
    
    if docker image inspect "$IMAGE" &>/dev/null; then
        docker push "$IMAGE"
        
        if [ $? -eq 0 ]; then
            echo "✓ Push successful: $IMAGE"
        else
            echo "✗ Push failed: $IMAGE"
            echo "Try: docker login -u $DOCKER_USER"
            exit 1
        fi
    else
        echo "✗ Image not found: $IMAGE"
        echo "Build it first with: docker build -t $IMAGE <directory>"
        return 1
    fi
}

# Push each container
echo ""
push_image "ssh-router"
echo ""
push_image "apache"
echo ""  
push_image "php"
echo ""
push_image "redmine"

echo ""
echo "=========================================="
echo "Push Complete!"
echo "=========================================="
echo ""
echo "To pull these images on another machine:"
echo "  docker pull $DOCKER_USER/apache-stack-ssh-router:$TAG"
echo "  docker pull $DOCKER_USER/apache-stack-apache:$TAG"
echo "  docker pull $DOCKER_USER/apache-stack-php:$TAG"
echo "  docker pull $DOCKER_USER/apache-stack-redmine:$TAG"
echo ""