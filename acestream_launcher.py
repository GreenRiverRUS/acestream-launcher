#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Acestream Launcher: Open acestream links with any media player"""

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
            'url',
            metavar='URL',
            help='the acestream url to play'
        )
        parser.add_argument(
            '-p', '--player',
            help='the media player command to use (default: vlc)',
            default='vlc'
        )

        self.app_name = 'Acestream Launcher'
        self.args = parser.parse_args()

        notify2.init(self.app_name)
        self.notifier = notify2.Notification(self.app_name)
        self.session = None
        self.content_info = None

        self.ensure_engine_running()

    def open(self):
        self.start_session()
        self.content_info = self.load_content_info()

        while True:
            file_id = self.select_file_id()
            url = self.start_downloading(file_id)
            self.start_player(url)

    def notify(self, message):
        """Show player status notifications"""

        icon = self.args.player.split()[0]
        messages = {
            'running': 'Acestream engine running.',
            'waiting': 'Waiting for channel response...',
            'noselect': 'Choose nothing to play...',
            'started': 'Streaming started. Launching player.',
            'noinfo': 'Acestream unable to load content info!',
            'noauth': 'Error authenticating to Acestream!',
            'noengine': 'Acestream engine not found in the provided path!',
            'noplayer': 'Player not found in the provided path!',
            'unavailable': 'Acestream channel unavailable!'
        }

        print(messages[message])
        self.notifier.update(self.app_name, messages[message], icon)
        self.notifier.show()

    def ensure_engine_running(self):
        """Start acestream engine"""
        for process in psutil.process_iter():
            if 'acestreamengine' in process.name():
                break
        else:
            try:
                psutil.Popen(['acestreamengine', '--client-console'])
                self.notify('running')
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

    def close_session(self, started=False):
        if started:
            self.session.sendline('STOP')
        self.session.sendline('SHUTDOWN')

    def load_content_info(self):
        """Load content info by content id"""
        content_id = self.args.url.split('://')[1]

        try:
            self.session.timeout = 15
            self.session.sendline('LOADASYNC 42 PID ' + content_id)
            self.session.expect('LOADRESP 42 .*')
            content_info = self.session.after.decode('utf-8').split('\n')[0].split(maxsplit=2)[-1]
            content_info = json.loads(content_info)
            content_info['content_id'] = content_id
        except (pexpect.TIMEOUT, pexpect.EOF):
            self.notify('noinfo')
            self.close_session()
            sys.exit(1)

        return content_info

    def select_file_id(self):
        """Run file selector if needed"""
        icon = self.args.player.split()[0]
        content_files = self.content_info['files']

        if len(content_files) > 1:
            selector = FilenamesSelectorWindow(content_files, icon=icon)
            selector.open()
            file_id = selector.selected_file_index
            filename = selector.selected_file
        else:
            filename, file_id = content_files[0]
        print('Selected: ' + str(filename))

        if file_id is None:
            self.notify('noselect')
            self.close_session()
            sys.exit(1)

        self.notify('waiting')
        return file_id

    def start_downloading(self, file_id):
        """Force engine to start downloading and streaming"""
        content_id = self.content_info['content_id']

        try:
            self.session.timeout = 60
            self.session.sendline('START PID {} {}'.format(content_id, file_id))
            self.session.expect('http://.*')

            url = self.session.after.decode('utf-8').split()[0]

            self.notify('started')
        except (pexpect.TIMEOUT, pexpect.EOF):
            self.notify('unavailable')
            self.close_session(started=True)
            sys.exit(1)

        return url

    def start_player(self, url):
        """Start the media player"""
        player_args = self.args.player.split()
        player_args.append(url)

        try:
            player = psutil.Popen(player_args)
            player.wait()
        except FileNotFoundError:
            self.notify('noplayer')
            self.close_session(started=True)
            sys.exit(1)


def main():
    """Start Acestream Launcher"""
    try:
        AcestreamLauncher().open()
    except (KeyboardInterrupt, EOFError):
        print('Acestream Launcher exiting...')

        for process in psutil.process_iter():
            if 'acestreamengine' in process.name():
                process.kill()

        sys.exit(0)

if __name__ == '__main__':
    main()
