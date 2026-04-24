FROM golang:1.23-alpine AS builder
WORKDIR /build
COPY go.mod ./
COPY main.go ./
RUN go mod tidy && CGO_ENABLED=0 go build -o /app -ldflags="-s -w" .

FROM alpine:latest
COPY --from=builder /app /app
EXPOSE 8001
CMD ["/app"]
