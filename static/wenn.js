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
* WennPlayer Class for interfacing with the lower level ws audio api.
*/
class WennPlayer {
    setup(artist, track, album, cover) {
        let loc = window.location, new_uri;
        var proto = window.location.href.indexOf("https://") === 0 ? "wss:" : "ws:";
        new_uri = proto + "//" + loc.host + loc.pathname + "api/stream"
        const _this = this
        var defaultConfig = {
            codec: {
                sampleRate: 48000,
                channels: 2,
                app: 2049,
                frameDuration: 20,
                bufferSize: 4096,
                calcBuffer: true,
                isPacked: true
            },
            server: new_uri,
            events: {
                instance: _this,
                jsonEvent: _this.onWebsockJsonEvent
            },
            contextOpts: {
                sampleRate: 48000
            }
        };
        this.c = {
            lastVol: 0.5,
            html: {
                artist: artist, track: track, album: album, cover: cover
            },
            enableLogging: true
        }
        this.c.player = new WSAudioAPI.Player(defaultConfig);
    }

    b64toBlob(dataURI) {

        var byteString = atob(dataURI.split(',')[1]);
        var ab = new ArrayBuffer(byteString.length);
        var ia = new Uint8Array(ab);

        for (var i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
        }
        return new Blob([ab], {type: 'image/jpeg'});
    }

    onWebsockJsonEvent(jsonData, _this) {
        if (jsonData.event === 'meta') {
            if (jsonData.artist) {
                if (typeof (ketikin) !== 'undefined')
                    ketikin(_this.c.html.artist, {
                        texts: [jsonData.artist[0]], speed: 50, loop: false
                    })
                else
                    _this.c.html.artist.innerText = jsonData.artist[0]
            }
            if (jsonData.title) {
                if (typeof (ketikin) !== 'undefined')
                    ketikin(_this.c.html.track, {
                        texts: [jsonData.title[0]], speed: 50, loop: false
                    })
                else
                    _this.c.html.track.innerText = jsonData.title[0]
            }
            if (jsonData.album) {
                if (typeof (ketikin) !== 'undefined')
                    ketikin(_this.c.html.album, {
                        texts: [jsonData.album[0]], speed: 50, loop: false
                    })
                else
                    _this.c.html.album.innerText = jsonData.album[0]
            }
            var coverShown = window.getComputedStyle(document.querySelector("#cover").parentElement).display;
            if (coverShown !== 'none') {
                if (jsonData.cover) {
                    _this.c.html.cover.src = URL.createObjectURL(
                        _this.b64toBlob("data:image/jpeg;base64," + jsonData.cover.cover)
                    )
                } else

                    _this.setImage(_this); // cursed i know but fuck it.
            }
        }
    }

    rand(min, max) {
        return Math.floor(Math.random() * (max - min)) + min;
    }

    setImage(_this = null) {
        if (_this == null)
            this.c.html.cover.src = "/api/cover?" + this.rand(0, 1000);
        else
            _this.c.html.cover.src = "/api/cover?" + this.rand(0, 1000);
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