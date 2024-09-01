# Twitch stream recorder

From https://github.com/ancalentari/twitch-stream-recorder

## Requirements

1. [python3.8](https://www.python.org/downloads/release/python-380/) or higher
2. requests (python module)
3. [streamlink](https://streamlink.github.io/)  
4. [ffmpeg](https://ffmpeg.org/)

## Setting up

Create `config.py` file in the same directory as `twitch-recorder.py` with:

```properties
# root_path = "D:\\test_record"  # windows
root_path = "/d/test_record"  # linux
channel = "crittervision"
quality = "best"
output_file_in_channel_folder = False
client_id = "XXXX"
client_secret = "XXXX"
```

`root_path` - path to a folder where you want your VODs to be saved to  
`channel` - name of the streamer channel you want to record by default  
`quality` - record quality, choose from `best` `1080p60` `1080p` `720p60` `720p` `480p` `360p` `160p` (some of them may not be available)  
`output_file_in_channel_folder` - True or False  
`client_id` - you can grab this from [here](https://dev.twitch.tv/console/apps) once you register your application  
`client_secret` - you generate this [here](https://dev.twitch.tv/console/apps) as well, for your registered application  


## Running script

The script will be logging to a console.

Run the script

```shell script
python3.8 twitch-recorder.py
```

To record a specific streamer use `-c` or `--channel`

```shell script
python3.8 twitch-recorder.py --channel mrderiv
```

To specify quality use `-q` or `--quality`

```shell script
python3.8 twitch-recorder.py --quality 720p
```

To change default logging use `-l` or `--log`

```shell script
python3.8 twitch-recorder.py --log warn
```

To record streams in a channel named folder, use `--enable-output-file-in-channel-folder`

```shell script
python3.8 twitch-recorder.py --enable-output-file-in-channel-folder
```
