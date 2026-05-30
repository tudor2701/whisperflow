from .config import CONFIG

_SYSTEM_PROMPT = (
    "Du bist ein Transkript-Polierer. Korrigiere ausschließlich Grammatik, "
    "Rechtschreibung und Interpunktion des folgenden gesprochenen Texts. "
    "Behalte Sprache, Wortwahl, Tonalität und Bedeutung exakt bei. "
    "Entferne Füllwörter wie 'ähm' oder 'äh'. "
    "Antworte ausschließlich mit dem polierten Text, ohne Kommentare, "
    "ohne Anführungszeichen, ohne Erklärungen."
)


class Cleaner:
    def __init__(
        self,
        model: str = CONFIG.cleanup_model,
        api_key: str | None = CONFIG.anthropic_api_key,
    ):
        self.model = model
        self.api_key = api_key
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _ensure_client(self):
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def clean(self, text: str) -> str:
        if not text.strip() or not self.available:
            return text
        client = self._ensure_client()
        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": text}],
        )
        parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
        return "".join(parts).strip() or text
