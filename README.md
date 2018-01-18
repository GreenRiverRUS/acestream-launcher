# Acestream Launcher
Acestream Launcher allows you to open Acestream links with a Media Player of your choice

## Dependencies
    python, python-psutil, python-pexpect, python-notify2, acestream-engine, python-gobject, gtk3

## Usage
    acestream-launcher [-u ACESTREAM_URL] [-t TORRENT_URL] [--player PLAYER]

## Required arguments (one of)
    -u, --url ACESTREAM_URL     The acestream url to play, e.g. acestream://1ccf192064ee2d95e91a79f91c6097273d582827
    -t, --torrent TORRENT_URL   The link to the torrent file to play, e.g. http://rutor.org/download/67346

## Optional arguments
    -h, --help                  Show this help message and exit
    -p, --player PLAYER         The media player command to use (default: vlc)

## Installation
Install required dependencies and run `install.sh` as root. The script will install acestream-launcher in `opt` directory.

## Packages
Arch Linux: [AUR Package](https://aur.archlinux.org/packages/acestream-launcher)
