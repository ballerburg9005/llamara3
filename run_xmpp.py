#!/bin/python

from getpass import getpass
import threading
from argparse import ArgumentParser
import subprocess
import tempfile
import os
import requests
import logging
import asyncio
import aiohttp
import json
import mimetypes
import pathlib
import random
import string
import re
import sys
from datetime import datetime, time, timedelta, timezone
from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout, XMPPError
from slixmpp.plugins.xep_0363 import stanza
from slixmpp.plugins.xep_0333 import markers
from slixmpp.plugins.xep_0184 import XEP_0184
from slixmpp.xmlstream import ET
from aiohttp import ClientSession, ClientTimeout
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

import magic

import sqlite3

from botlogic import *

class EchoBot(ClientXMPP, BotLogic):
    def __init__(self, jid, password):
        BotLogic.__init__(self)
        ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("sesion_end", self.session_end)
        self.add_event_handler("message", self.handle_message)
        self.add_event_handler("disconnected", self.handle_disconnect)
#        self.add_event_handler("ping", self.ping_response) 

        
        # Register XEP plugins for file upload
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0066')  # Out of Band Data
        self.register_plugin('xep_0363')  # HTTP Upload
        self.register_plugin('xep_0085')  #
        self.register_plugin('xep_0184')  # receipts? shit?
        self.register_plugin('xep_0333')  # mark msgs as read

        # don't know what this does
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0334') # Message Processing Hints
        self.register_plugin('xep_0319') # Last User Interaction in Presence
        self.register_plugin('xep_0280') # carbons
        self.register_plugin('xep_0115') # capabilities
        self.register_plugin('xep_0092') # version
        self.register_plugin('xep_0084') # avatar
        self.register_plugin('xep_0153') # related to avatar?
        self.register_plugin('xep_0054') # related to avatar?

        self.plugin['xep_0184'].auto_ack = True

        self.messenger = "XMPP"

    def get_image_mime_type(self, image_data):
        mime = magic.Magic()
        mime_type = mime.from_buffer(image_data)
        return mime_type

    async def set_avatar(self, ctx):
        avatar_file = None
        try:
            avatar_file = open(os.path.expanduser("assets/avatar.jpg"), 'rb')
        except IOError:
            print('Could not find file: %s' % self.filepath)
            return False

        avatar = avatar_file.read()

        avatar_type = self.get_image_mime_type(avatar)
        avatar_id = self['xep_0084'].generate_id(avatar)
        avatar_bytes = len(avatar)

        avatar_file.close()

        used_xep84 = False

        print('Publish XEP-0084 avatar data')
        result = await self['xep_0084'].publish_avatar(avatar)
        if isinstance(result, XMPPError):
            print('Could not publish XEP-0084 avatar')
        else:
            used_xep84 = True

        print('Update vCard with avatar')
        result = await self['xep_0153'].set_avatar(avatar=avatar, mtype=avatar_type)
        if isinstance(result, XMPPError):
            print('Could not set vCard avatar')

        if used_xep84:
            print('Advertise XEP-0084 avatar metadata')
            result = await self['xep_0084'].publish_avatar_metadata([
                {'id': avatar_id,
                 'type': avatar_type,
                 'bytes': avatar_bytes}
                # We could advertise multiple avatars to provide
                # options in image type, source (HTTP vs pubsub),
                # size, etc.
                # {'id': ....}
            ])
            if isinstance(result, XMPPError):
                print('Could not publish XEP-0084 metadata')

        print('Wait for presence updates to propagate...')
#       self.schedule('end', 5, self.disconnect, kwargs={'wait': True})
        return True


    async def chat_state_notifications(self, recipient, status):
        state_notification = self.Message()
        state_notification["to"] = recipient
        state_notification["chat_state"] = status
        state_notification.send()



    async def handle_message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            if msg['body'] and not (re.compile(r'^https://[^ ]*:5443/upload/[^ ]+$')).search(msg['body']):
                # TODO don't spam this with each send
                self.send_presence(pstatus='Available (Llamara3)', pshow='chat')
                self['xep_0333'].send_marker(msg['from'], msg['id'], "displayed")
                await self.chat_state_notifications(msg['from'], "composing")
                await self.plugin["xep_0115"].update_caps(jid=self.boundjid)
                

                user_message = self.sanitize_ascii_input(msg['body'].strip())
                user_handle = self.sanitize_ascii_input(msg['from'].bare, True)


                if(bool(re.search(r".*OMEMO.*http[s]?://[^\s]*.*", user_message))):
                    msg.reply("""Your client is sending e2e encrypted messages. Please set this conversation to "unencrypted" or disable OMEMO.""").send() 
                else:
                    await self.process_message(user_handle, user_message)
                await self.chat_state_notifications(msg['from'], "inactive")
            else:
                msg.reply("[Client could not process received data message]").send()
        else:
            print("Received non-chat message:")
            print(str(msg))


    async def send_text_message(self, ctx, user_handle, text):
        try:
            message = self.Message(sto=user_handle, stype='chat')
            message['body'] = text
            message.send()
            return True
        except IqTimeout:
            raise TimeoutException()
            return False
        except (ConnectionError, SystemExit):
            raise FuckedupException()
            return False

    async def send_voice_message(self, ctx, user_handle, text):
        message = self.Message(sto=user_handle, stype='chat')
        if await self.generate_tts_audio(text, user_handle):
            self.process_audio_files(user_handle)
            try:
                url = await self.upload_file_from_path("temp_audios/"+user_handle+".mp3")
                if url:
                    message['body'] = url
                    message['oob']['url'] = url
                message.send()
                return True
            except (IqError, IqTimeout, XMPPError) as ex:
                logging.error(f"Could not send voice message: {ex}")
                send_text_message(None, user_handle, "Error when sending voice message.")
        return False

    async def upload_file_from_path(self, path, timeout=None):
        """Upload a file from a local file path via XEP-0363."""
        logging.info(f'Uploading file from path: {path}')

        if not os.path.isfile(path):
            raise FileNotFoundError("File not found.")

        with open(path, 'rb') as file:
            input_file = file.read()
        filesize = len(input_file)
        logging.debug(f"Filesize is {filesize} bytes")

        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        logging.debug(f"Content type is {content_type}")

        filename = self.get_random_filename(path)
        logging.debug(f"Uploading file with filename {filename}")

        url = await self['xep_0363'].upload_file(
            filename, size=filesize, input_file=input_file,
            content_type=content_type, timeout=timeout)

        return url

    def get_random_filename(self, filename):
        """Return a random filename, keeping the extension intact."""
        path = pathlib.Path(filename)
        extension = ''.join(path.suffixes) if path.suffixes else ".unknown"
        return ''.join(random.choice(string.ascii_letters) for _ in range(10)) + extension


    def session_end(self, event):
        pass


    def session_start(self, event):
        self.send_presence(pstatus='Available', pshow='chat')
        self.get_roster()
        self.loop.create_task(self.start_periodic_check())

#    def ungay_dt(self, dt):
#       return datetime.strptime(dt.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")



    # TODO this does not work sometimes for some reason
    async def handle_disconnect(self, data=""):
        print("Attempting to reconnect...")
        while True:
            try:
                await self.connect()
#                await self.process(forever=False)
                break
            except Exception as e:
                print(f"Reconnection failed: {e}. Retrying in 10 seconds...")
                await asyncio.sleep(10)


if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

    config = json.loads('{"model": "Llama-3-8B-Instruct-abliterated-v2:latest", "user": "", "password": ""}')
    with open("config.json", 'r') as file:
        config = json.load(file)
   
    if not os.path.exists("temp_audios"):
        os.mkdir("temp_audios")
 
    if not config or not "model" in config or len(config["model"]) < 3:
        print("Model name missing in config.json (e.g. Llama-3-8B-Instruct-abliterated-v2:latest)")
    elif "user" in config and "password" in config and len(config["user"]) > 5 and len(config["password"]) > 3:
        xmpp = EchoBot(config["user"], config["password"])
        xmpp.model = config["model"]
        xmpp.auto_reconnect = True
        xmpp.connect()
        xmpp.process(forever=True)
    else:
        print("Bad config.json.")
