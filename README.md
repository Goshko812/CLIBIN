# CLIBIN - A Command Line Pastebin Service

CLIBIN is a lightweight, Docker-based command line pastebin service inspired by the original clbin. With CLIBIN, you can quickly share text content via simple curl commands, making it perfect for sharing terminal output, logs, code snippets, and more.


## Features

- **Simple Command Line Interface**: Share content with a single curl command
- **Automatic Cleanup**: 24-hour retention with automatic deletion of expired pastes
- **Rate Limiting**: Prevents abuse with a limit of 10 requests per minute
- **Syntax Highlighting**: Add `?hl` to any paste URL for line numbers and syntax highlighting
- **Docker-Ready**: Easy deployment with Docker and Docker Compose
- **Size Limits**: 100KB per paste to ensure service stability
- **Self-Hosted**: Full control over your data and service

## Installation

### Prerequisites

- Docker and Docker Compose
- A domain name (for production deployment)
- NGINX or another reverse proxy (for production deployment)

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/Goshko812/CLIBIN.git
   cd CLIBIN
   ```

2. Modify the app.py file to display your domain instead of the default:
   ```python
   # Find this line in the MANPAGE string and similar places:
   # <command> | curl -F 'clibin=<-' https://example.com
   # Change to your domain:
   # <command> | curl -F 'clibin=<-' https://your-domain.com
   ```

3. Build and start the service:
   ```bash
   docker-compose up -d
   ```

4. The service will be available at `http://localhost:5000` or `http://<your-IP>:5000`

### Production Deployment with NGINX

For a production environment, it's recommended to use NGINX as a reverse proxy. Here's a sample NGINX configuration:

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Remember to:
1. Replace `example.com` with your actual domain
2. Obtain SSL certificates (e.g., using Let's Encrypt)

## Usage

### Basic Usage

To share content:

```bash
echo "Hello, world!" | curl -F 'clibin=<-' https://your-domain.com
```

The service will return a URL where your content can be accessed:

```
https://your-domain.com/AbCdEf
```

### Syntax Highlighting

For syntax highlighting and line numbers, add `?hl` to the end of the URL:

```
https://your-domain.com/AbCdEf?hl
```

### Helper Function

Add this helper function to your `.bashrc` or `.zshrc` for even easier usage:

```bash
clibin() {
    if [ $# -eq 0 ]; then
        curl -F 'clibin=<-' https://your-domain.com
    else
        "$@" | curl -F 'clibin=<-' https://your-domain.com
    fi
}
```

With this function, you can use:

```bash
# Pipe output to clibin
ps auxf | clibin

# Run a command and send its output to clibin
clibin netstat -tlnaepw
```

## Configuration

You can modify the following settings in `app.py`:

- `RETENTION_TIME`: How long pastes are kept (default: 86400 seconds, or 1 day)
- `MAX_PASTE_SIZE`: Maximum size of pastes (default: 100KB)
- Rate limits: Currently set to 10 requests per minute

## Security Considerations

- CLIBIN does not offer password protection for pastes
- All pastes are public and accessible to anyone with the URL
- Consider using HTTPS with a valid SSL certificate in production
- The service performs basic input validation, but additional security measures may be needed in high-risk environments

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the original clbin service
- Built with Flask, Docker, and Python

---
