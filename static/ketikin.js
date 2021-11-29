/*Ketikin.js - A typewriter javascript library.
* By parinpan
*
* License: Unknown
*
* Changes by Shinon:
* - Made selector to be unable to selected so as when copy pasting, it won't be a selected.
* - Hide cursor after flashing X amount of times.
*  */
const ketikin = (selector, options) => {
    const baseTypingSpeed = 5
    const maxTypingSpeed = 100
    const defaultTimeGap = 1000
    const cursor = '<span id="{id}">|</span>'

    fenceSpeed = (speed) => {
        speed = speed > maxTypingSpeed ? maxTypingSpeed : speed
        speed = speed < 0 ? 0 : speed
        speed = maxTypingSpeed - speed
        return speed
    }

    getSeq = (element) => {
        return element.getAttribute('ketikin-seq')
    }

    getCursor = (element) => {
        return element.querySelector('#' + getSeq(element)) || document.createElement("cursor")
    }

    animateCursor = (element) => {
        getCursor(element).style.userSelect = "none";
        getCursor(element).animate([{opacity: 0.5}], {
            duration: defaultTimeGap,
            iterations: 3
        }).onfinish = function () {
            getCursor(element).style.opacity = "0";
        }
    }

    removeCursor = (element) => {
        getCursor(element).remove()
    }

    addCursor = (element) => {
        element.innerHTML = element.innerHTML + cursor.replace('{id}', getSeq(element))
    }

    addTypingChar = (element, char) => {
        element.innerHTML = element.innerHTML + char
    }

    swapTypingText = (element, text) => {
        element.innerHTML = text
    }

    type = (element, char, executionTime) => {
        setTimeout(() => removeCursor(element) | addTypingChar(element, char) | addCursor(element), executionTime)
    }

    backSpace = (element, text, executionTime) => {
        setTimeout(() => removeCursor(element) | swapTypingText(element, text) | addCursor(element), executionTime)
        return text.substring(0, text.length - 1)
    }

    arrangeExecutionTime = (lastExecutionTime, speedBaseline) => {
        return lastExecutionTime + Math.floor(Math.random() * fenceSpeed(options.speed)) + speedBaseline
    }

    orchestrate = (element, text, shouldBackSpacing, executionTime) => {
        for (const char of text) {
            type(element, char, executionTime)
            executionTime = arrangeExecutionTime(executionTime, baseTypingSpeed)
        }

        if (shouldBackSpacing) {
            let backSpacingSpeed = baseTypingSpeed
            executionTime = executionTime + defaultTimeGap

            while (text) {
                text = backSpace(element, text, executionTime)
                executionTime = arrangeExecutionTime(executionTime, backSpacingSpeed)
                backSpacingSpeed = Math.floor(backSpacingSpeed * 0.7)
            }

            setTimeout(() => swapTypingText(element, text) | addCursor(element), executionTime)
        }

        return executionTime
    }

    playOrchestration = (element, texts, opts) => {
        let executionTime = 0
        let shouldBackSpacing = false

        texts.forEach((text, index) => {
            shouldBackSpacing = (index < texts.length - 1 && !opts.loop) || opts.loop
            executionTime = orchestrate(element, text, shouldBackSpacing, executionTime) + defaultTimeGap
        })

        if (opts.loop) {
            setTimeout(() => playOrchestration(element, texts, opts), executionTime)
        } else {
            setTimeout(() => animateCursor(element), executionTime)
        }
    }

    setupOptions = (opts) => {
        return Object.assign({
            texts: null,
            speed: 0,
            loop: false
        }, opts)
    }

    setupTexts = (element, opts) => {
        return (opts.texts || [element.innerText]).filter(text => text)
    }

    setupElement = (element) => {
        element.setAttribute('ketikin-seq', 'seq-' + Math.random().toString(36).substr(2))
        element.innerHTML = ""
        return element
    }

    if (typeof (selector) == "string") {
        document.querySelectorAll(selector).forEach(element => {
            const opts = setupOptions(options)
            const texts = setupTexts(element, opts)

            if (texts.length > 0) {
                playOrchestration(setupElement(element), texts, opts)
            }
        })
    } else {
        const opts = setupOptions(options)
        const texts = setupTexts(selector, opts)

        if (texts.length > 0) {
            playOrchestration(setupElement(selector), texts, opts)
        }
    }

}