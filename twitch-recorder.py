import datetime
import enum
import getopt
import logging
import os
import subprocess
import sys
import shutil
import time
import requests
import config


class TwitchResponseStatus(enum.Enum):
    ONLINE = 0
    OFFLINE = 1
    NOT_FOUND = 2
    UNAUTHORIZED = 3
    ERROR = 4


class TwitchRecorder:
    def __init__(self):
        # global configuration
        self.ffmpeg_path = "ffmpeg"
        self.refresh = 30  # en secondes
        self.output_file_in_channel_folder = False

        # user configuration
        self.channel = config.channel
        self.quality = config.quality
        self.root_path = config.root_path

        # twitch configuration
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.token_url = "https://id.twitch.tv/oauth2/token?client_id=" + self.client_id + "&client_secret=" \
                         + self.client_secret + "&grant_type=client_credentials"
        self.url = "https://api.twitch.tv/helix/streams"
        self.access_token = self.fetch_access_token()

    def fetch_access_token(self):
        token_response = requests.post(self.token_url, timeout=15)
        token_response.raise_for_status()
        token = token_response.json()
        return token["access_token"]

    def run(self):
        if self.output_file_in_channel_folder:
            self.rootpath = os.path.join(self.root_path, self.channel)

        if self.refresh < 15:
            logging.warning("check interval should not be lower than 15 seconds")
            self.refresh = 15
            logging.info("system set check interval to 15 seconds")

        if not os.path.isdir(self.root_path):
            os.makedirs(self.root_path)
            logging.info("creating folder {}".format(self.root_path))
        if self.output_file_in_channel_folder:
            channel_folder_with_path = os.path.join(self.root_path, self.channel)
            if not os.path.isdir(channel_folder_with_path):
                os.makedirs(channel_folder_with_path)
                logging.info("creating folder {}".format(channel_folder_with_path))

        logging.info("checking for %s every %s seconds, recording with %s quality",
                     self.channel, self.refresh, self.quality)
        self.loop_check()

    def check_channel(self):
        info = None
        status = TwitchResponseStatus.ERROR
        try:
            headers = {"Client-ID": self.client_id, "Authorization": "Bearer " + self.access_token}
            r = requests.get(self.url + "?user_login=" + self.channel, headers=headers, timeout=15)
            r.raise_for_status()
            info = r.json()
            if info is None or not info["data"]:
                status = TwitchResponseStatus.OFFLINE
            else:
                status = TwitchResponseStatus.ONLINE
        except requests.exceptions.RequestException as e:
            if e.response:
                if e.response.status_code == 401:
                    status = TwitchResponseStatus.UNAUTHORIZED
                if e.response.status_code == 404:
                    status = TwitchResponseStatus.NOT_FOUND
        return status, info

    def loop_check(self):
        while True:
            status, info = self.check_channel()
            if status == TwitchResponseStatus.NOT_FOUND:
                logging.error("channel not found, invalid channel or typo")
                time.sleep(self.refresh)
            elif status == TwitchResponseStatus.ERROR:
                logging.error("%s unexpected error. will try again in 5 minutes",
                              datetime.datetime.now().strftime("%Hh%Mm%Ss"))
                time.sleep(300)
            elif status == TwitchResponseStatus.OFFLINE:
                logging.info("%s currently offline, checking again in %s seconds", self.channel, self.refresh)
                time.sleep(self.refresh)
            elif status == TwitchResponseStatus.UNAUTHORIZED:
                logging.info("unauthorized, will attempt to log back in immediately")
                self.access_token = self.fetch_access_token()
            elif status == TwitchResponseStatus.ONLINE:
                logging.info("%s online, stream recording in session", self.channel)

                twitch_channels = info["data"]
                twitch_channel = next(iter(twitch_channels), None)
                filename = self.channel + "_" + datetime.datetime.now() \
                    .strftime("%Y-%m-%d_%Hh%Mm%Ss") + "_" + twitch_channel.get("title").replace(' ', '_') + ".mkv"

                # clean filename from unnecessary characters
                filename = "".join(x for x in filename if x.isalnum() or x in [" ", "-", "_", "."])

                filename_with_path = ""
                logging.info(self.output_file_in_channel_folder)
                if self.output_file_in_channel_folder:
                    filename_with_path = os.path.join(self.root_path, self.channel, filename)
                else:
                    filename_with_path = os.path.join(self.root_path, filename)

                subprocess_command = "streamlink -O --twitch-disable-ads twitch.tv/{} {} | ffmpeg -i pipe:0 -c:v copy -f matroska -y {}".format(self.channel, self.quality, filename_with_path)

                # bug python avec subprocess + linux, utiliser une liste avec la commande decoupée ne fonctionne pas
                # cf https://bugs.python.org/issue6689
                subprocess.call(
                    [subprocess_command], shell=True
                )

                logging.info("processing is done, going back to checking...")
                time.sleep(self.refresh)


def main(argv):
    twitch_recorder = TwitchRecorder()
    usage_message = "twitch-recorder.py -c <channel> -q <quality>"

    logger = logging.getLogger()
    for handler in logger.handlers:  # pour supprimer le handler qui log dans un fichier, cf https://stackoverflow.com/a/57622426
        logger.removeHandler(handler)
    console_handle = logging.StreamHandler()
    console_handle.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s", "%Y-%m-%d %H:%M:%S")
    console_handle.setFormatter(formatter)
    logger.addHandler(console_handle)

    try:
        opts, args = getopt.getopt(argv, "hc:q:l:", ["channel=", "quality=", "log=", "enable-output-file-in-channel-folder"])
    except getopt.GetoptError:
        print(usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print(usage_message)
            sys.exit()
        elif opt in ("-c", "--channel"):
            twitch_recorder.channel = arg
        elif opt in ("-q", "--quality"):
            twitch_recorder.quality = arg
        elif opt in ("-l", "--log"):
            logging_level = getattr(logging, arg.upper(), None)
            if not isinstance(logging_level, int):
                raise ValueError("invalid log level: %s" % logging_level)
            logging.basicConfig(level=logging_level)
            logging.info("logging configured to %s", arg.upper())
        elif opt == "--enable-output-file-in-channel-folder":
            twitch_recorder.output_file_in_channel_folder = True
            logging.info("output file will be recorded in channel folder")

    twitch_recorder.run()


if __name__ == "__main__":
    main(sys.argv[1:])
