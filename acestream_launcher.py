#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Acestream Launcher: Open acestream links with any media player"""

import os
import sys
import time
import hashlib
import argparse
import json

import psutil
import pexpect
import notify2

from filename_selector_app import FilenamesSelectorWindow


class AcestreamLauncher(object):
    """Acestream Launcher"""
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog='acestream-launcher',
            description='Open acestream links with any media player'
        )
        parser.add_argument(
            '-t', '--type',
            choices=['acestream', 'torrent'],
            default='acestream',
            help='the type of the provided url: acestream cid or '
                 'link to the torrent file (default: acestream)'
        )
        parser.add_argument(
            'url',
            help='the url to content for playing'
        )
        parser.add_argument(
            '--get-cid',
            action='store_const', const=True,
            help='get acestream cid for torrent and exit (available only for --type torrent)'
        )
        parser.add_argument(
            '-p', '--player',
            help='the media player command to use (default: vlc)',
            default='vlc'
        )

        self.app_name = 'Acestream Launcher'
        self.args = parser.parse_args()
        self.icon = self.args.player.split()[0]

        notify2.init(self.app_name)
        self.notifier = notify2.Notification(self.app_name)
        self.notify('running')
        self.session = None
        self.content_info = None

        self.ensure_engine_running()

    def open(self):
        self.start_session()
        self.content_info = self.load_content_info()

        if self.args.get_cid:
            content_id = self.get_torrent_cid()
            print('Content ID: ' + content_id)
            self.close_session()
            return

        streaming_started = False
        while True:
            file_id, options_available = self.select_file_id()
            if file_id is None:
                break
            streaming_started = True
            url = self.start_streaming(file_id)
            self.start_player(url)
            if not options_available:
                break

        self.close_session(streaming_started=streaming_started)

    def notify(self, message):
        """Show player status notifications"""
        
        messages = {
            'running': 'Acestream Launcher started.',
            'waiting': 'Waiting for channel response...',
            'started': 'Streaming started. Launching player.',
            'badtype': 'One can get content id only for torrent.',
            'noinfo': 'Acestream unable to load content info!',
            'nourl': 'No url provided to play!',
            'nocontent': 'No content on the provided link!',
            'noauth': 'Error authenticating to Acestream!',
            'noengine': 'Acestream engine not found in the provided path!',
            'noplayer': 'Player not found in the provided path!',
            'unavailable': 'Acestream channel unavailable!'
        }

        message = messages[message]
        if sys.stdout.isatty():
            print(message)
        else:
            self.notifier.update(self.app_name, message, self.icon)
            self.notifier.show()

    def ensure_engine_running(self):
        """Ensure acestream engine started"""
        for process in psutil.process_iter():
            if 'acestreamengine' in process.name():
                break
        else:
            try:
                psutil.Popen(['acestreamengine', '--client-console'])
                time.sleep(5)
            except FileNotFoundError:
                self.notify('noengine')
                sys.exit(1)

    def start_session(self):
        """Start acestream telnet session"""
        product_key = 'n51LvQoTlJzNGaFxseRK-uvnvX-sD4Vm5Axwmc4UcoD-jruxmKsuJaH0eVgE'
        session = pexpect.spawn('telnet localhost 62062')
        self.session = session

        try:
            session.timeout = 20
            session.sendline('HELLOBG version=3')
            session.expect('key=.*')

            request_key = session.after.decode('utf-8').split()[0].split('=')[1]
            signature = (request_key + product_key).encode('utf-8')
            signature = hashlib.sha1(signature).hexdigest()
            response_key = product_key.split('-')[0] + '-' + signature

            session.sendline('READY key=' + response_key)
            session.expect('AUTH.*')
            session.sendline('USERDATA [{"gender": "1"}, {"age": "3"}]')
        except (pexpect.TIMEOUT, pexpect.EOF):
            self.notify('noauth')
            self.close_session()
            sys.exit(1)

        return session

    def close_session(self, streaming_started=False):
        if streaming_started:
            self.session.sendline('STOP')
        self.session.sendline('SHUTDOWN')

    def format_content_command_args(self, file_id=None):
        if self.args.type == 'acestream':
            content_id = self.args.url.split('://')[1]
            if file_id is not None:
                command = 'PID {} {}'.format(content_id, file_id)
            else:
                command = 'PID {}'.format(content_id)
        elif self.args.type == 'torrent':
            torrent_url = self.args.url
            if file_id is not None:
                command = 'TORRENT {} {} 0 0 0'.format(torrent_url, file_id)
            else:
                command = 'TORRENT {} 0 0 0'.format(torrent_url)
        else:
            command = None

        return command

    def load_content_info(self):
        """Load content info by content id"""
        command = self.format_content_command_args()
        if command is None:
            self.notify('nourl')
            self.close_session()
            sys.exit(1)

        try:
            self.session.timeout = 15
            self.session.sendline('LOADASYNC 42 ' + command)
            self.session.expect('LOADRESP 42 .*')
            content_info = self.session.after.decode('utf-8').split('\n')[0].split(maxsplit=2)[-1]
            content_info = json.loads(content_info)
        except (pexpect.TIMEOUT, pexpect.EOF):
            self.notify('noinfo')
            self.close_session()
            sys.exit(1)

        return content_info

    def get_torrent_cid(self):
        if self.args.type != 'torrent':
            self.notify('badtype')
            self.close_session()
            sys.exit(1)

        self.session.sendline(
            'GETCID checksum={} infohash={} developer=0 affiliate=0 zone=0'.format(
                self.content_info['checksum'], self.content_info['infohash']
            )
        )
        self.session.expect('##.*')
        content_id = self.session.after.decode('utf-8')[2:]

        return content_id


    def select_file_id(self):
        """Run file selector if needed"""
        content_files = self.content_info.get('files', [])

        if len(content_files) > 1:
            options_available = True
            selector = FilenamesSelectorWindow(content_files, icon=self.icon)
            selector.open()
            file_id = selector.selected_file_index
            filename = selector.selected_file 
        elif len(content_files) == 1:
            options_available = False
            filename, file_id = content_files[0]
        else:
            self.notify('nocontent')
            self.close_session()
            sys.exit(1)
        print('Selected: ' + str(filename))

        return file_id, options_available

    def start_streaming(self, file_id):
        """Force engine to start downloading and streaming"""
        self.notify('waiting')
        command = self.format_content_command_args(file_id)

        try:
            self.session.timeout = 60
            self.session.sendline('START ' + command)
            self.session.expect('START http://.*')

            url = self.session.after.decode('utf-8').split()[1]

            self.notify('started')
        except (pexpect.TIMEOUT, pexpect.EOF):
            self.notify('unavailable')
            self.close_session(streaming_started=True)
            sys.exit(1)

        return url

    def start_player(self, url):
        """Start the media player"""
        player_args = self.args.player.split()
        player_args.append(url)

        try:
            env = dict(os.environ)
            env.pop('LD_PRELOAD', None)  # fuck opera!
            player = psutil.Popen(player_args, env=env)
            player.wait()
        except FileNotFoundError:
            self.notify('noplayer')
            self.close_session(streaming_started=True)
            sys.exit(1)


def main():
    """Start Acestream Launcher"""
    try:
        AcestreamLauncher().open()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)

if __name__ == '__main__':
    main()
