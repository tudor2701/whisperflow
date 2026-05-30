import threading

import numpy as np
import sounddevice as sd

from .config import CONFIG


class Recorder:
    def __init__(self, sample_rate: int = CONFIG.sample_rate):
        self.sample_rate = sample_rate
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self.level = 0.0  # smoothed live RMS, 0..~1, read by the overlay

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"[recorder] status: {status}", flush=True)
        block = indata.reshape(-1)
        rms = float(np.sqrt(np.mean(block**2))) if block.size else 0.0
        # exponential smoothing so the animation isn't jittery
        self.level = 0.6 * self.level + 0.4 * rms
        with self._lock:
            self._chunks.append(block.copy())

    def start(self) -> None:
        self.level = 0.0
        with self._lock:
            self._chunks.clear()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream is None:
            return np.zeros(0, dtype=np.float32)
        self._stream.stop()
        self._stream.close()
        self._stream = None
        with self._lock:
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(self._chunks).astype(np.float32)


if __name__ == "__main__":
    import time

    r = Recorder()
    print(f"Recording 3 s at {r.sample_rate} Hz...")
    r.start()
    time.sleep(3)
    audio = r.stop()
    print(f"Captured shape={audio.shape}, dtype={audio.dtype}, "
          f"peak={np.abs(audio).max():.3f}, rms={np.sqrt((audio**2).mean()):.3f}")
