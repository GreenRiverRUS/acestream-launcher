# Acestream Launcher
Acestream Launcher allows you to open Acestream links with a Media Player of your choice

## Dependencies
    python, python-psutil, python-pexpect, python-notify2, acestream-engine, python-gobject, gtk3

## Usage
    acestream-launcher [--type {acestream,torrent}] [--player PLAYER] URL

## Required arguments
    -t, --type {acestream,torrent}    The type of the provided url: acestream cid or link to the torrent file (default: acestream)
    url                               The url to content for playing

## Optional arguments
    -h, --help                        Show help message and exit
    -p, --player PLAYER               The media player command to use (default: vlc)
    --get-cid                         Get acestream cid for torrent and exit (available only for torrent)

## Installation
Install required dependencies and run `install.sh` as root. The script will install acestream-launcher in `opt` directory.

## Packages
Arch Linux: [AUR Package](https://aur.archlinux.org/packages/acestream-launcher)
