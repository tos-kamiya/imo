#!/usr/bin/env python3

# ref: https://github.com/openai/whisper
# ref: https://people.csail.mit.edu/hubert/pyaudio/
# ref: https://stackoverflow.com/questions/42544661/convert-numpy-int16-audio-array-to-float32
# ref: https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time

from locale import normalize
import subprocess
import os
import sys
import tempfile
import time
import wave

import whisper
import pyaudio
import numpy as np
import argparse


CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

INT16_MAX_VALUE = (1 << 16) // 2

AUDIO_DATA_GENERATOR_SUBPROCESS_MARK = '--audio-data-generator'

script_path = os.path.realpath(__file__)


def open_pyaudio_stream():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    return p, stream


def close_pyaudio_stream(p_stream):
    p, stream = p_stream
    stream.stop_stream()
    stream.close()
    p.terminate()


def read_pyaudio_stream(p_stream):
    _, stream = p_stream
    raw_data = stream.read(CHUNK)
    data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32, order='C') / INT16_MAX_VALUE
    sum_sq = np.sum(data**2)
    vol = np.sqrt(sum_sq / CHUNK)
    return raw_data, vol


def save_wav(fn, buf, sample_width):
    wf = wave.open(fn, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(buf)
    wf.close()


def detect_noise_level(p_stream, breath_frames):
    silence_vols = []
    for _ in range(breath_frames * 2):
        _, vol = read_pyaudio_stream(p_stream)
        silence_vols.append(vol)
    silence_vol_threshold = np.max(silence_vols) * 4
    return silence_vol_threshold


def whisper_convert_to_text(audio, model, language, task):
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    if language is None:
        _, probs = model.detect_language(mel)
        ml = max(probs, key=probs.get)
        print("[%s] " % ml, end='')
        language = ml
    options = {'language': language, 'task': task}
    result = whisper.transcribe(model, audio, **options)
    return result['text']


def audio_data_generator(noise_level, breath_frames, temp_wav_file, ready_flag_file):
    p_stream = open_pyaudio_stream()
    try:
        if noise_level is None:
            noise_level = detect_noise_level(p_stream, breath_frames)
            print("* detected noise level: %g" % noise_level, file=sys.stderr, flush=True)

        # flag indicating 'get ready'
        with open(ready_flag_file, 'w') as outp:
            pass

        while True:
            # wait until audio data get consumed
            while os.path.exists(temp_wav_file):
                time.sleep(0.1)

            # wait speech
            print("* waiting speech", file=sys.stderr, flush=True)
            raw_data, vol = read_pyaudio_stream(p_stream)
            while vol < noise_level:
                raw_data, vol = read_pyaudio_stream(p_stream)

            # record speech
            frames = [raw_data]
            silence_frames = 0
            while silence_frames < breath_frames:
                raw_data, vol = read_pyaudio_stream(p_stream)
                frames.append(raw_data)
                if vol < noise_level:
                    silence_frames += 1
                else:
                    silence_frames = 0

            # save speech as audio data
            sample_width = p_stream[0].get_sample_size(FORMAT)
            save_wav(temp_wav_file + '.a', b''.join(frames), sample_width)
            os.rename(temp_wav_file + '.a', temp_wav_file)
            print("* save audio data to a temporary file", file=sys.stderr, flush=True)
    finally:
        close_pyaudio_stream(p_stream)


def main():
    parser = argparse.ArgumentParser(description='Interactive Moji-Okoshi (voice transcription)')

    parser.add_argument(
        '--model', type=str, default='medium',
        help='Model. Either tiny, base, small, medium, large, or large-v2 [default: large-v2]')
    parser.add_argument(
        '--language', type=str, default=None,
        help='Language of speech. Automatically detected when not specified.')
    parser.add_argument(
        '--task', type=str, default=None,
        help='Specify `translate` to translate speech into English.')
    parser.add_argument(
        '--noise-level', type=float, default=None,
        help='Minimum volume of speech. Specify if you have trouble detecting speech breaks (0.0 to 0.2).')
    parser.add_argument(
        '--breath-time', type=float, default=1.5,
        help='Silent intervals perceived as sentence breaks [default: 1.5]')
    parser.add_argument(
        '--diag', action='store_true', default=False,
        help='Show subprocess\'s stderr/stdout (for debug)')

    args = parser.parse_args()

    breath_frames = int(RATE / CHUNK * args.breath_time)

    # prepare temporary directory
    tempdir = tempfile.TemporaryDirectory()
    temp_wav_file = os.path.join(tempdir.name, "out.wav")
    ready_flag_file = os.path.join(tempdir.name, "ready_flag")

    # spawn audio-data-generator process
    cmd = [sys.executable, script_path, AUDIO_DATA_GENERATOR_SUBPROCESS_MARK, args.noise_level or "", "%d" % breath_frames, temp_wav_file, ready_flag_file]
    if args.diag:
        adg_p = subprocess.Popen(cmd)
    else:
        adg_p = subprocess.Popen(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    print("* loading model ... (may take minutes on the first run)", file=sys.stderr, flush=True)
    model = whisper.load_model(args.model)

    try:
        # wait until agp process gets ready
        if args.noise_level is None:
            print("* detecting noise level ...", file=sys.stderr, flush=True)
        while not os.path.exists(ready_flag_file):
            time.sleep(0.1)
        print("* press Ctrl+C to quit", file=sys.stderr, flush=True)

        while True:
            # wait until audio data gets ready
            while not os.path.exists(temp_wav_file):
                time.sleep(0.1)
            if args.diag:
                print("* load audio data from a temporary file", file=sys.stderr, flush=True)

            # read audio data and delete it
            audio = whisper.load_audio(temp_wav_file)
            os.remove(temp_wav_file)
            audio = whisper.pad_or_trim(audio)

            # convert speech to text
            text = whisper_convert_to_text(audio, model, args.language, args.task)

            # print the text
            print(text)
    except KeyboardInterrupt as _:
        if adg_p.poll() is None:
            adg_p.terminate()
        sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == AUDIO_DATA_GENERATOR_SUBPROCESS_MARK:
        cmd = sys.argv[2:]
        noise_level, breath_frames, temp_wav_file, ready_flag_file = cmd
        noise_level = None if noise_level == "" else float(noise_level)
        breath_frames = int(breath_frames)
        audio_data_generator(noise_level, breath_frames, temp_wav_file, ready_flag_file)
    else:
        main()
