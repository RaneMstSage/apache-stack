#!/bin/bash

# Build and push all Docker containers to Docker Hub
# Requires: docker login

set -e

DOCKER_USER="ranemstsage"
TAG="latest"

echo "=========================================="
echo "Building and Pushing Apache Stack Containers"
echo "=========================================="

# Check if logged in to Docker Hub
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo ""
    echo "Please login to Docker Hub first:"
    echo "docker login -u $DOCKER_USER"
    echo ""
    echo "After logging in, run this script again."
    exit 1
fi

# Function to build and push a container
build_and_push() {
    local NAME=$1
    local DIR=$2
    local IMAGE="$DOCKER_USER/apache-stack-$NAME:$TAG"
    
    echo ""
    echo "Building $NAME..."
    echo "----------------------------------------"
    
    cd "$DIR"
    
    # Build with BuildKit for better caching
    DOCKER_BUILDKIT=1 docker build -t "$IMAGE" .
    
    if [ $? -eq 0 ]; then
        echo "✓ Build successful: $IMAGE"
        
        echo "Pushing to Docker Hub..."
        docker push "$IMAGE"
        
        if [ $? -eq 0 ]; then
            echo "✓ Push successful: $IMAGE"
        else
            echo "✗ Push failed: $IMAGE"
            exit 1
        fi
    else
        echo "✗ Build failed: $IMAGE"
        exit 1
    fi
    
    cd ..
}

# Build and push each container
echo ""
echo "1. SSH Router (with VS Code support)"
build_and_push "ssh-router" "ssh-router"

echo ""
echo "2. Apache"
build_and_push "apache" "apache"

echo ""
echo "3. PHP-FPM"
build_and_push "php" "php"

echo ""
echo "4. Redmine"
build_and_push "redmine" "redmine"

echo ""
echo "=========================================="
echo "All containers built and pushed successfully!"
echo "=========================================="
echo ""
echo "Images available at:"
echo "  - $DOCKER_USER/apache-stack-ssh-router:$TAG"
echo "  - $DOCKER_USER/apache-stack-apache:$TAG"
echo "  - $DOCKER_USER/apache-stack-php:$TAG"
echo "  - $DOCKER_USER/apache-stack-redmine:$TAG"
echo ""
echo "To use these in docker-compose.yml, they're already configured."
echo ""