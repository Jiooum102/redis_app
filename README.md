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

3. **Ensure Redis server is running** (if using local Redis):
   ```bash
   redis-server
   ```

## Usage

### Starting the Application

1. **Run the Flask application**:
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
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
├── static/
│   ├── css/
│   │   └── style.css     # VS Code dark theme styling
│   └── js/
│       └── main.js       # Frontend JavaScript with Socket.IO client
└── templates/
    └── index.html         # Main web interface
```

## Configuration

All Redis connection settings are configured through the web interface. No configuration files or environment variables are required.

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

The application runs in debug mode by default. To disable:

```python
# In app.py, change:
socketio.run(app, debug=True, host='0.0.0.0', port=5000)
# To:
socketio.run(app, debug=False, host='0.0.0.0', port=5000)
```

### Custom Port

To run on a different port:

```python
# In app.py, change the port:
socketio.run(app, debug=True, host='0.0.0.0', port=8080)
```

## License

This project is open source and available for use and modification.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Author

Developed as a Redis pub/sub web interface with modern UI/UX.

