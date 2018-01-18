# Acestream Launcher
Acestream Launcher allows you to open Acestream links with a Media Player of your choice

## Dependencies
    python, python-psutil, python-pexpect, python-notify2, acestream-engine, python-gobject, gtk3

## Usage
    acestream-launcher URL [--player PLAYER] [--engine ENGINE]

## Positional arguments
    URL                   The acestream url to play

## Optional arguments
    -h, --help            Show this help message and exit
    -p, --player PLAYER   The media player command to use (default: vlc)

## Installation
Install required dependencies and run `install.sh` as root. The script will install acestream-launcher in `opt` directory.

## Packages
Arch Linux: [AUR Package](https://aur.archlinux.org/packages/acestream-launcher)
