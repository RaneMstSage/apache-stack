FROM golang:1.21-alpine
RUN apk add --no-cache git
RUN go install github.com/charmbracelet/git-lfs-transfer@latest
# Keep container running
CMD ["tail", "-f", "/dev/null"]