FROM golang:1.21-alpine

# Install dependencies
RUN apk add --no-cache git bash

# Install git-lfs-transfer
RUN go install github.com/charmbracelet/git-lfs-transfer@latest

# Copy the binary to a standard location
RUN cp /go/bin/git-lfs-transfer /usr/local/bin/

# Create a volume mount point for the binary
VOLUME ["/usr/local/bin"]

# Keep container running
CMD ["tail", "-f", "/dev/null"]