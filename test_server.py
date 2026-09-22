import unittest

from fastapi import HTTPException

from server import TextTranslationRequest, app, health, translate_text


class FakePipeline:
    def translate_text(self, text: str, src: str, tgt: str) -> str:
        return f"{tgt}:{text}"


class ServerContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        app.state.pipeline = FakePipeline()

    async def test_health_reports_ready(self) -> None:
        self.assertEqual(await health(), {"status": "ok", "ready": True})

    async def test_text_translation_returns_contract(self) -> None:
        result = await translate_text(
            TextTranslationRequest(text=" Hello ", src="eng", tgt="amh")
        )
        self.assertEqual(result.source_text, "Hello")
        self.assertEqual(result.translated_text, "amh:Hello")
        self.assertEqual(result.src_lang, "eng")
        self.assertEqual(result.tgt_lang, "amh")

    async def test_same_language_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            await translate_text(
                TextTranslationRequest(text="Hello", src="eng", tgt="eng")
            )
        self.assertEqual(context.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
