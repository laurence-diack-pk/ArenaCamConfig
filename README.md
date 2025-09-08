# Arena Camera Configuration GUI

There was no easy way to edit nodemaps for Lucid cameras on Linux, so here's a terminal-based GUI for configuring Lucid camera node trees using Textual.


## Installation

### From PyPI (when published)

```bash
pip install arena-cam-config
```

### From Source

```bash
git clone https://github.com/laurence-diack-pk/arena-cam-config.git
cd arena-cam-config
pip install -e .
```

## Prerequisites

1. **ArenaSDK**: You MUST have Lucid Vision Labs ArenaSDK installed on your system
   - Download from: https://thinklucid.com/downloads-hub/
   - Follow the installation instructions for your platform

2. **Python 3.8+**: This package requires Python 3.8 or later

## Usage

### Command Line

After installation, you can run the application directly:

```bash
arena-cam-config
```

## Controls

- **Tab**: Switch between different nodemaps (Device, TL Device, etc.)
- **Enter**: Edit the selected parameter or execute a command
- **Arrow Keys**: Navigate through the tree
- **Mouse**: You can use this too
- **q**: Quit the application
- **r**: Refresh the current tree

## Parameter Types

The application handles various camera parameter types:

- **Integers**: Numeric values with min/max validation
- **Floats**: Decimal values with range checking
- **Booleans**: True/False values with radio button selection
- **Enums**: Predefined options with radio button selection
- **Strings**: Text input with validation
- **Commands**: Executable camera functions

## Device Selection

When multiple cameras are connected, the application will display a device selection dialog showing:
- Camera family and model name
- IP address

## Nodemaps

Switch between different camera nodemaps:

1. **Device**: Main camera parameters (exposure, gain, etc.)
2. **TL Device**: Transport layer device parameters
3. **TL Stream**: Streaming parameters
4. **TL Interface**: Interface-specific parameters
5. **TL System**: System-level parameters

## Development

### Setting up Development Environment

```bash
git clone https://github.com/yourusername/arena-cam-config.git
cd arena-cam-config
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- textual >= 0.41.0
- arena-api >= 2.0.0

## Contributing

I built this to accomplish my specific needs. If it doesn't do something you want it to, feel free to be the change you want to see in the world :)

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues related to:
- **This package**: Open an issue on GitHub
- **ArenaSDK**: Contact Lucid Vision Labs support
- **Camera hardware**: Refer to your camera's documentation

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) for the terminal UI
- Designed for [Lucid Vision Labs ArenaSDK](https://thinklucid.com/)
