# Redis Pub/Sub Web Application

A modern, user-friendly web application for interacting with Redis pub/sub messaging system. Built with Python Flask and featuring a VS Code dark mode-inspired interface.

## Features

- **Redis Connection Management**: Connect to Redis servers with custom host, port, password, and database configuration
- **Publish Messages**: Send JSON messages to Redis channels with a dynamic form interface
- **Subscribe to Channels**: Subscribe to multiple Redis channels and receive messages in real-time
- **Real-time Message Display**: View incoming and outgoing messages instantly via WebSocket
- **Message History**: Keep track of message history with timestamps and channel information
- **Dynamic JSON Form**: Add or remove key-value pairs dynamically when composing messages
- **Smart Value Parsing**: Automatically detects and parses numbers, booleans, null, and JSON objects
- **Form Caching**: Automatically saves and restores form data per channel using localStorage
- **Channel Selection**: Quick-select subscribed channels when publishing messages
- **VS Code Dark Theme**: Beautiful dark mode interface inspired by VS Code

## Technology Stack

- **Backend**: Python 3.13+
- **Web Framework**: Flask 3.0.0
- **WebSocket**: Flask-SocketIO 5.3.5
- **Redis Client**: redis-py 5.0.1
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Real-time Communication**: Socket.IO

## Requirements

- Python 3.9 or higher
- Redis server (local or remote)
- pip (Python package manager)

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd redis_app
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```
   
   The `.env` file supports the following variables:
   - `FLASK_DEBUG`: Set to `False` for production (default: `True`)
   - `HOST`: Server host (default: `0.0.0.0`)
   - `PORT`: Server port (default: `5000`)
   - `SECRET_KEY`: Flask secret key (change in production)
   - `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)

4. **Ensure Redis server is running** (if using local Redis):
   ```bash
   redis-server
   ```

## Usage

### Development Mode

1. **Run the Flask application**:
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Production Deployment

**Important**: The Flask development server is not suitable for production. Use a production WSGI server like Gunicorn.

#### Using Gunicorn (Recommended)

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run with Gunicorn**:
   ```bash
   gunicorn --worker-class gevent --worker-connections 1000 -w 1 --bind 0.0.0.0:5000 app:app
   ```

   Options:
   - `--worker-class gevent`: Required for Flask-SocketIO WebSocket support (gevent is more compatible than eventlet)
   - `--worker-connections 1000`: Maximum number of simultaneous connections per worker
   - `-w 1`: Number of worker processes (1 is recommended for SocketIO)
   - `--bind 0.0.0.0:5000`: Host and port to bind to
   - `app:app`: Flask application instance

   **Alternative**: If you prefer eventlet (may have compatibility issues with Python 3.13+):
   ```bash
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
   ```

3. **For production, you may also want to**:
   - Set environment variables:
     ```bash
     export FLASK_DEBUG=False
     export PORT=5000
     ```
   - Use a reverse proxy (nginx) in front of Gunicorn
   - Set up process management (systemd, supervisor, etc.)
   - Configure SSL/TLS certificates

#### Production Configuration

Create a `gunicorn_config.py` file for advanced configuration:

```python
bind = "0.0.0.0:5000"
workers = 1
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2
```

Then run:
```bash
gunicorn -c gunicorn_config.py app:app
```

#### Using with Nginx (Reverse Proxy)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Connecting to Redis

1. Fill in the Redis connection form:
   - **Host**: Redis server hostname (default: `localhost`)
   - **Port**: Redis server port (default: `6379`)
   - **Password**: Redis password (leave empty if no password)
   - **Database**: Redis database number (default: `0`)

2. Click **Connect** to establish the connection

3. The connection status indicator will show green when connected

### Publishing Messages

1. **Select or enter a channel name**:
   - Use the dropdown to select from subscribed channels, or
   - Type a channel name manually

2. **Compose your JSON message**:
   - Click **+ Add Field** to add key-value pairs
   - Enter keys and values in the form fields
   - Remove fields using the × button (disabled when only one field remains)
   - Values are automatically parsed:
     - Numbers: `123` → `123` (number)
     - Booleans: `true`/`false` → boolean
     - Null: `null` → null
     - JSON: `{"key": "value"}` → parsed JSON object
     - Strings: Everything else → string

3. **Click Publish** to send the message

### Subscribing to Channels

1. Enter a channel name in the "Subscribe to Channel" section
2. Click **Subscribe**
3. The channel will appear in the subscribed channels list
4. Messages published to this channel will appear in real-time in the Messages section

### Unsubscribing from Channels

- Click the × button on any channel tag in the subscribed channels list

### Viewing Messages

- All published and received messages appear in the Messages section
- Messages are color-coded:
  - **Sent messages**: Green left border
  - **Received messages**: Blue left border
- Each message shows:
  - Message type (SENT/RECEIVED)
  - Channel name
  - Timestamp
  - Formatted JSON content

### Form Caching

- Form data is automatically saved as you type
- Data is cached per channel in browser localStorage
- When you select a channel or reload the page, your previous form data is restored
- Each channel remembers its own form structure

## Project Structure

```
redis_app/
├── app.py                 # Main Flask application with SocketIO handlers
├── redis_client.py        # Redis connection and pub/sub manager
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Example environment variables file
├── .gitignore            # Git ignore file
├── static/
│   ├── css/
│   │   └── style.css     # VS Code dark theme styling
│   └── js/
│       └── main.js       # Frontend JavaScript with Socket.IO client
└── templates/
    └── index.html         # Main web interface
```

## Configuration

### Application Configuration

Application settings can be configured via environment variables in a `.env` file:

- `FLASK_DEBUG`: Enable/disable debug mode (default: `True`)
- `HOST`: Server host address (default: `0.0.0.0`)
- `PORT`: Server port number (default: `5000`)
- `SECRET_KEY`: Flask secret key for sessions (change in production)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)

Copy `.env.example` to `.env` and modify as needed:
```bash
cp .env.example .env
```

### Redis Configuration

All Redis connection settings are configured through the web interface. No configuration files or environment variables are required for Redis connection details.

## Features in Detail

### Dynamic JSON Form
- Add unlimited key-value pairs
- Remove fields individually
- Smart value type detection
- Real-time JSON building

### Auto-save & Caching
- Form data saved automatically as you type
- Per-channel caching
- Restores data on page reload
- Loads cached data when selecting channels

### Real-time Updates
- WebSocket-based communication
- Instant message delivery
- Live connection status
- Real-time channel subscription updates

## Troubleshooting

### Connection Issues

- **Connection Failed**: 
  - Verify Redis server is running
  - Check host and port are correct
  - Ensure firewall allows the connection

- **Authentication Failed**:
  - Verify password is correct
  - Check if Redis requires authentication

### Message Issues

- **Messages not appearing**:
  - Ensure you're subscribed to the channel
  - Check Redis connection status
  - Verify channel names match exactly

- **JSON parsing errors**:
  - Ensure at least one field has a key
  - Check JSON syntax in value fields
  - Use quotes for string values that look like numbers

## Development

### Running in Debug Mode

The application runs in debug mode by default when using `python app.py`. 

To disable debug mode:
```bash
export FLASK_DEBUG=False
python app.py
```

### Custom Port

To run on a different port:

```bash
export PORT=8080
python app.py
```

Or with Gunicorn:
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8080 app:app
```

### Environment Variables

All environment variables can be set in the `.env` file:

- `FLASK_DEBUG`: Set to `False` for production (default: `True`)
- `HOST`: Host address to bind to (default: `0.0.0.0`)
- `PORT`: Port number to bind to (default: `5000`)
- `SECRET_KEY`: Flask secret key (change in production)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)

### Logging

The application uses Python's logging module. Logs are output to the console with timestamps and log levels. You can control the verbosity using the `LOG_LEVEL` environment variable:

- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages only

## License

This project is open source and available for use and modification.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Author

Developed as a Redis pub/sub web interface with modern UI/UX.

