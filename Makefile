SHELL=/bin/bash

all: build

# Build the application
build:
	@go build -o main main.go
	@echo "Successful Build - Current OS/Architecture"

# Generate openapi documentation
openapi:
	@redocly bundle openapi/main.yaml --dereferenced -o static/openapi/openapi.yaml

.PHONY: build openapi
