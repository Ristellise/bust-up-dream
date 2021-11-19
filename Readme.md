# [BUST UP DREAM](https://www.youtube.com/watch?v=anzcYSTY270)

A simple open-source web radio station.

## Who is it for?

It's for those who love python and wanted to create a web radio out of it.

## Setup

You will need the following dependencies:

- [quart](https://pypi.org/project/quart/)
- audio_metadata (from [here](https://github.com/thebigmunch/audio-metadata))
- Your songs.

For songs, place them in the specified format:

- Music
   - Album
      - Song 1.opus
      - Song 2.opus
      - ...
      - Song 5.opus
      - Cover.jpg
   - Album 2
      - Song 1.opus
      - Song 2.opus
      - ...
      - Song 5.opus
      - Cover.jpg
   - Cover.jpg
   - Music_1.m3u8

A valid example format is in the Music directory.

## Setup Precautions

- Encode all your music to opus audio, js stream will not take anything else.
- generally 180kbps is good enough. `--bitrate 180 --vbr --music`
- Cover's must be jpg, not png.

## Acknowledgements

- ws-audio-api [ws.js] (Modified to support multiple channels & chrome fix.)
- Listen.moe (Design was liften from it since I can't design...)

## Websocket API

This web radio uses websockets to communicate at the address `/stream`. once connected, the server will send out 2 json encoded data:

1. Current Track being played
2. Current Track Album

Rest of the data recieved in binary are singular opus packets, (typically 20ms.)

## Disclaimer

**No support will be provided**, I'm just providing the code & script. 
