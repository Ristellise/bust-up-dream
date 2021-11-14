/* 
* The MIT License (MIT)
* 
* Copyright (c) 2021 Shinon
* 
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
* 
* The above copyright notice and this permission notice shall be included in all
* copies or substantial portions of the Software.
* 
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
* 
* Wenn Class for interfacing with the lower level ws audio api.
*/
class Wenn {
    setup(artist, track, album, cover) {
        let loc = window.location, new_uri;
        new_uri = "ws:" + "//" + loc.host + loc.pathname + "stream"
        const _this = this
        var defaultConfig = {
            codec: {
                sampleRate: 48000,
                channels: 2,
                app: 2049,
                frameDuration: 20,
                bufferSize: 4096,
                calcBuffer: true
            },
            server: new_uri,
            html: {
                artist: artist, track: track, album: album, cover
            },
            contextOpts: {
                sampleRate: 48000
            }
        };
        this.c = {lastVol: 0.5}
        console.log(this.c)
        this.c.player = new WSAudioAPI.Player(defaultConfig);
    }

    log(side, message) {
        if (this.c.enableLogging)
            console.log(`%c[${side}]%c: ${message}`, 'color:red', 'color:inital')
    }

    setVolume(input_volume) {
        this.c.lastVol = input_volume;
        this.c.player.setVolume(this.c.lastVol)
    }

    isStarted() {
        return this.c.player.audioQueue != null;
    }

    start() {
        this.c.player.start();
        this.c.player.setVolume(this.c.lastVol)
    }

    stop() {
        this.c.player.stop();
    }
}