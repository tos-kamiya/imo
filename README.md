imo
====

A command-line interactive transcription tool using whisper.

(Checked on Ubuntu 22.04 + Cuda)

## Prerequisites / Installation

Tool imo has dependencies that cannot be installed by pip alone.
Install each dependency according to its installation instructions.

(1) Whisper

Follow the "Setup" instruction on the page https://github.com/openai/whisper

(2) PyAudio

Follow the "Installation" instruction on the page https://pypi.org/project/PyAudio/

(3) `numpy`

```sh
python3 -m pip install numpy
```

Copy the file `imo.py` to a directory on the path.

## Usage

Run imo.py.

```sh
imo.py
```

or

```sh
python3 imo.py
```

When a message "press Ctrl+C to quit" is shown up, you are ready to go; try speaking something into the microphone. When you finish speaking, the text will be displayed. After that, every time you speak, the content of your speech will be transcribed and displayed.

To quit, press Ctrl+C.

### Options

The default behavior is to estimate the language from speech and transcribe it into text, and output it to the terminal.

* `--language` to specify the language, e.g., `--language=English`, `--language=Japanese`.
* `--model` to specify the model to transcribe or translate e.g., `--model=medium`, `--model=large`. The default is `--model=large-v2`.
* `--task` The default is to transcribe, but when you specify `--task=translate`, it will also perform translation.

### A Screenshot.

![](images/run1.png)

### Troubleshoot

* If it cannot be run with an error, check that Whisper, PyAudio and numpy are installed.
* The first time it is launched, it downloads the model and may take a few minutes to load.
* If no text is output, check that the microphone is recognized (and audio level is adjusted) in OS settings.
* If recognition accuracy is not good, specify the language with the `--language` option.
