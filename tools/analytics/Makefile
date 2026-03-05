GO := /usr/local/go/bin/go

.PHONY: build install test clean

build:
	$(GO) build -o bin/analytics .

install: build
	cp bin/analytics $(HOME)/.local/bin/analytics

test:
	$(GO) test ./...

clean:
	rm -rf bin/
