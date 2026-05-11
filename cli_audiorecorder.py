#!/usr/bin/env python
"""Audiorecorder

Usage:
  cli_audiorecorder.py <URL> [--filename=<name>] [--duration=<time>] [--blocksize=<size>] [-v]
  cli_audiorecorder.py -h | --help
  cli_audiorecorder.py -l | --list

Arguments:
    URL                 Stream URL

Options:
  -h --help             Show this screen.
  -l --list             Show saved recordings.
  --filename=<name>     Name of recording [default: myRadio].
  --duration=<time>     Duration of recording in seconds [default: 30].
  --blocksize=<size>    Block size for read/write in bytes [default: 64].
  -v                    Show verbose output.
"""
import os

from docopt import docopt
import requests
import time

class AudioRecorder:
    def __init__(self, url, filename, duration, blocksize, verbose, status_callback=None):
        self.url = url
        self.filename = filename if filename.endswith('.mp3') else f"{filename}.mp3"
        self.duration = duration
        self.blocksize = blocksize
        self.verbose = verbose

        self.status_callback = status_callback
        self._bitrate = None

    def record(self):
        self._output("start")
        try:
            self._read_header()
            self._output("values")

            if self._bitrate:
                self._record_by_bitrate()
                return

            self._record_by_time()

        except requests.exceptions.HTTPError as e:
            print(f"[!] HTTP-Error: Cannot reach stream ({e.response.status_code}).")
            self._output("fail")
        except requests.exceptions.RequestException as e:
            print(f"[!] Network-Error: {type(e).__name__}")
            self._output("fail")
        except OSError as e:
            print(f"[!] Filesystem-Error: {e.strerror} ({self.filename})")
            self._output("fail")
        except Exception as e:
            print(f"[!] Error: {type(e).__name__}")
            self._output("fail")

    def _read_header(self):
        """
        pre request to read bitrate from header
        """
        with requests.get(self.url, stream=True, headers={'Icy-MetaData': '1'}, timeout=10) as _r_info:
            _r_info.raise_for_status()
            self._bitrate = _r_info.headers.get('icy-br', None)

    def _record_by_bitrate(self):
        """
        download stream based on bitrate
        """
        bytes_per_second = (int(self._bitrate) / 8) * 1024
        full_size = int(bytes_per_second * self.duration)
        bytes_written = 0

        with requests.get(self.url, stream=True, timeout=10) as _r:
            _r.raise_for_status()
            with open(self.filename, 'wb') as f:
                self._output("writing")
                for chunk in _r.iter_content(chunk_size=self.blocksize):
                    if not chunk:
                        continue
                    remaining_bytes = full_size - bytes_written
                    if len(chunk) <= remaining_bytes:
                        f.write(chunk)
                        bytes_written += len(chunk)
                    else:
                        f.write(chunk[:remaining_bytes])
                        break
                    if bytes_written >= full_size:
                        break
        self._output("success")

    def _record_by_time(self):
        """
        download stream based on time as fallback, when no bitrate is available
        """
        start_time = None

        with requests.get(self.url, stream=True, timeout=10) as _r:
            _r.raise_for_status()
            with open(self.filename, 'wb') as f:
                self._output("writing")
                for chunk in _r.iter_content(chunk_size=self.blocksize):
                    if not chunk:
                        continue
                    if start_time is None:
                        start_time = time.time()
                    f.write(chunk)
                    if time.time() - start_time > self.duration:
                        break
        self._output("success")

    def _output(self, o_case):
        """
        CLI output when verbose is True

        :param o_case: Event
        :type o_case: str
        """
        if self.status_callback:
            self.status_callback(o_case)

        if not self.verbose:
            return

        _RED = '\033[91m'
        _RESET = '\033[0m'

        match o_case:
            case "start":
                print("=============================")
                print("=== Audiorecorder started ===")
                print("=============================")
            case "values":
                print(f"-> URL:        {self.url}")
                print(f"-> Filename:   {self.filename}")
                print(f"-> Duration:   {self.duration} s")
                print(f"-> Blocksize:  {self.blocksize} Bytes")
                print(f"-> Bitrate:    {self._bitrate}")
                print("-----------------------------")
            case "writing":
                print(f"{_RED}-->       RECORDING       <--{_RESET}")
            case "success":
                print("=============================")
                print("===        SUCCESS        ===")
                print("=============================")
            case "fail":
                print("=============================")
                print("===        FAILURE        ===")
                print("=============================")

def list_saved_streams():
    print("=== LISTING SAVED STREAMS ===")
    mp3_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.mp3')]

    if not mp3_files:
        print("[!] No mp3 files found")
    else:
        for mp3_file in mp3_files:
            size_bytes = os.path.getsize(mp3_file)
            size_kb = size_bytes / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.0f} KB"
            else:
                size_str = f"{size_kb / 1024:.2f} MB"
            print(f" - {mp3_file} ( {size_str} )")

if __name__ == '__main__':
    args = docopt(str(__doc__))

    list_streams = bool(args['--list'])

    if list_streams:
        list_saved_streams()
    else:
        url = str(args['<URL>'])
        filename = str(args['--filename'])
        duration = int(args['--duration'])
        blocksize = int(args['--blocksize'])
        verbose = bool(args['-v'])

        recorder = AudioRecorder(url, filename, duration, blocksize, verbose)
        recorder.record()
