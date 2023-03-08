FROM golang:alpine AS builder

RUN apk add --no-cache git

RUN go install github.com/mailhog/MailHog@latest

FROM alpine:latest

RUN apk add --no-cache ca-certificates

COPY --from=builder /go/bin/MailHog /usr/local/bin/MailHog

EXPOSE 1025 8025

CMD ["MailHog", "-ui-bind-addr", "0.0.0.0:8025", "-smtp-bind-addr", "0.0.0.0:1025"]
