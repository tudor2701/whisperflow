import time

import numpy as np

from .config import CONFIG


class Transcriber:
    def __init__(self, model_name: str = CONFIG.model_name, language: str | None = CONFIG.language):
        self.model_name = model_name
        self.language = language
        self._warmed = False

    def warmup(self) -> None:
        if self._warmed:
            return
        t0 = time.time()
        silence = np.zeros(CONFIG.sample_rate, dtype=np.float32)
        self._run(silence)
        self._warmed = True
        print(f"[transcriber] warmed in {time.time() - t0:.1f}s", flush=True)

    def _run(self, audio: np.ndarray) -> dict:
        import mlx_whisper

        return mlx_whisper.transcribe(
            audio,
            path_or_hf_repo=self.model_name,
            language=self.language,
            fp16=True,
            verbose=False,
        )

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        result = self._run(audio)
        text = (result.get("text") or "").strip()
        return text
