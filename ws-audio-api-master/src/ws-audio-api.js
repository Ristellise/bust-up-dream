//    WebSockets Audio API
//
//    Opus Quality Settings
//    =====================
//    App: 2048=voip, 2049=audio, 2051=low-delay
//    Sample Rate: 8000, 12000, 16000, 24000, or 48000
//    Frame Duration: 2.5, 5, 10, 20, 40, 60
//    Buffer Size = sample rate/6000 * 1024

(function (global) {
    var defaultConfig = {
        codec: {
            sampleRate: 24000,
            channels: 1,
            app: 2048,
            frameDuration: 20,
            bufferSize: 4096,
            calcBuffer: false,
            isPacked: false
        },
        events: {
            instance: null,
            jsonEvent: null,
            blobParser: null
        },
        server: {
            host: window.location.hostname
        },
        contextOpts: {
            sampleRate: 24000
        },
    };

    var AudioContext = window.AudioContext || window.webkitAudioContext;
    var audioContext = false;

    var WSAudioAPI = global.WSAudioAPI = {
        Player: function (config, socket) {
            this.config = config || {};
            this.config.codec = this.config.codec || defaultConfig.codec;
            this.config.events = this.config.events || defaultConfig.events;
            this.config.server = this.config.server || defaultConfig.server;
            this.config.contextOpts = this.config.contextOpts || defaultConfig.contextOpts;
            audioContext = new AudioContext(this.config.contextOpts);

            if (this.config.codec.calcBuffer) {
                this.config.codec.bufferSize = ((this.config.codec.sampleRate) / 6000) * 1024;
            }

            this.sampler = new Resampler(this.config.codec.sampleRate, audioContext.sampleRate, this.config.codec.channels, this.config.codec.bufferSize);
            this.parentSocket = socket;

            this.decoder = new OpusDecoder(this.config.codec.sampleRate, this.config.codec.channels);
            this.silence = new Float32Array(this.config.codec.bufferSize);
        },
    };


    WSAudioAPI.Player.prototype.start = function () {
        var _this = this;

        this.audioQueue = {
            buffer: new Float32Array(0),

            write: function (newAudio) {
                var currentQLength = this.buffer.length;
                newAudio = _this.sampler.resampler(newAudio);
                var newBuffer = new Float32Array(currentQLength + newAudio.length);
                newBuffer.set(this.buffer, 0);
                newBuffer.set(newAudio, currentQLength);
                this.buffer = newBuffer;
            },

            read: function (nSamples) {
                var samplesToPlay = this.buffer.subarray(0, nSamples);
                this.buffer = this.buffer.subarray(nSamples, this.buffer.length);
                return samplesToPlay;
            },

            length: function () {
                return this.buffer.length;
            }
        };

        this.scriptNode = audioContext.createScriptProcessor(this.config.codec.bufferSize, this.config.codec.channels, this.config.codec.channels);
        this.scriptNode.onaudioprocess = function (e) {
            var chans = _this.config.codec.channels;
            if (_this.audioQueue.length()) {
                var buf = _this.audioQueue.read(_this.config.codec.bufferSize * chans);
                var channels = [];
                for (var c = 0; c < chans; c++) {
                    channels.push(e.outputBuffer.getChannelData(c))
                }

                for (var i = 0; i < buf.length; i += chans) {
                    for (var c = 0; c < channels.length; c++) {
                        channels[c][i / 2] = buf[i + c];
                    }
                }
            } else {
                console.warn("Buffer empty!");
                for (var i = 0; i < chans; i++) {
                    e.outputBuffer.getChannelData(i).set(_this.silence);
                }
            }
        };
        this.gainNode = audioContext.createGain();
        this.scriptNode.connect(this.gainNode);
        this.gainNode.connect(audioContext.destination);
        audioContext.resume()
        if (!this.parentSocket) {
            this.socket = new WebSocket(this.config.server);
        } else {
            this.socket = this.parentSocket;
        }
        var _onmessage = this.parentOnmessage = this.socket.onmessage;
        this.socket.onmessage = function (message) {
            if (_onmessage) {
                _onmessage(message);
            }
            audioContext.resume()
            if (message.data instanceof Blob) {
                const reader = new FileReader();
                reader.onload = function () {
                    if (_this.config.codec.isPacked) {
                        const dv = new DataView(reader.result);
                        var curr =0;
                        var pksize = dv.getUint16(0);
                        curr += 2;
                        while (pksize > 0) {
                            var wavAudio = _this.decoder.decode_float(dv.buffer.slice(curr,curr+pksize));
                            _this.audioQueue.write(wavAudio);
                            curr += pksize;
                            if (curr >= dv.byteLength)
                                break;
                            pksize = dv.getUint16(curr);
                            curr += 2;
                        }
                    } else {
                        var dd = _this.decoder.decode_float(reader.result);
                        _this.audioQueue.write(dd);
                    }
                };
                reader.readAsArrayBuffer(message.data);
            } else if (typeof message.data === "string") {
                const jsonData = JSON.parse(message.data);
                if (_this.config.events.jsonEvent)
                    _this.config.events.jsonEvent(jsonData, _this.config.events.instance);
            }
        };
    };

    WSAudioAPI.Player.prototype.getVolume = function () {
        return this.gainNode ? this.gainNode.gain.value : 'Stream not started yet';
    };

    WSAudioAPI.Player.prototype.setVolume = function (value) {
        if (this.gainNode) this.gainNode.gain.value = value;
    };

    WSAudioAPI.Player.prototype.stop = function () {
        this.audioQueue = null;
        this.scriptNode.disconnect();
        this.scriptNode = null;
        this.gainNode.disconnect();
        this.gainNode = null;

        if (!this.parentSocket) {
            this.socket.close();
        } else {
            this.socket.onmessage = this.parentOnmessage;
        }
    };
})(window);