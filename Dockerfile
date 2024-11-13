# syntax=docker/dockerfile:1
FROM golang:1.23 AS builder
WORKDIR /usr/src/app
COPY go.mod go.sum ./
RUN go mod download && go mod verify
COPY . .
RUN go build -o /usr/src/app/main main.go

FROM chromedp/headless-shell:latest
RUN apt-get update && apt-get install dumb-init -y
ENTRYPOINT ["dumb-init", "--"]
COPY --from=builder /usr/src/app/main /
COPY --from=builder /usr/src/app/static /static/
EXPOSE 1323
CMD ["/main"]
