imo
====

A command-line interactive transcription tool using whisper.

(Checked on Ubuntu 20.04 + Cuda)

## Prerequisites / Installation

Tool imo has dependencies that cannot be installed by pip alone.
Install each dependency according to its installation instructions.

(1) Whisper

Follow the "Setup" instruction on the page https://github.com/openai/whisper

(2) PyAudio

Follow the "Installation" instruction on the page https://pypi.org/project/PyAudio/

(3) `numpy` and `docopt` (or `docopt-ng`).

```sh
python3 -m pip install numpy
python3 -m pip install docopt
```

Copy the file `imo.py` to a directory on the path.

## Run

Run imo.py.

```sh
imo.py
```

When you see "press Ctrl+C to quit", you are ready to go.

Try speaking something into the microphone. When you finish speaking, the text will be displayed. After that, every time you speak, the content of your speech will be transcribed and displayed.

To quit, press Ctrl+C.

The default behavior is to estimate the language from speech and transcribe it into text, and output it to the terminal.

* You can specify the language with the option `--language`, e.g., `--language=English`, `--language=Japanese`.
* You can specify a model for transcription with the option `--model`, e.g., `--model=medium`, `--model=large`.

### A Screenshot.

![](images/run1.png)
