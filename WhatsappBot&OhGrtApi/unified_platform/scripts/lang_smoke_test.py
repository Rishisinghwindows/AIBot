import asyncio

from common.config.settings import settings
from common.services.ai_language_service import ai_understand_message, ai_translate_response


SAMPLES = {
    "hi": "नमस्ते, मुझे दिल्ली का मौसम बताइए",
    "bn": "নমস্কার, আজ কলকাতার আবহাওয়া কেমন?",
    "ta": "வணக்கம், சென்னை வானிலை என்ன?",
    "te": "నమస్తే, హైదరాబాద్ వాతావరణం ఎలా ఉంది?",
    "ml": "ഹായ്, കൊച്ചി കാലാവസ്ഥ എങ്ങനെയാണ്?",
    "kn": "ನಮಸ್ಕಾರ, ಬೆಂಗಳೂರು ಹವಾಮಾನ ಹೇಗಿದೆ?",
    "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਅੰਮ੍ਰਿਤਸਰ ਦਾ ਮੌਸਮ ਕਿਵੇਂ ਹੈ?",
    "mr": "नमस्कार, मुंबईचे हवामान कसे आहे?",
    "or": "ନମସ୍କାର, ଭୁବନେଶ୍ୱର ଆବହାଓା କେମିତି?",
}


async def main() -> None:
    print("OPENAI_API_KEY set:", bool(settings.OPENAI_API_KEY))

    for lang, text in SAMPLES.items():
        result = await ai_understand_message(text, openai_api_key=settings.OPENAI_API_KEY)
        detected = result.get("detected_language")
        translated = await ai_translate_response(
            "Hello! This is a test response.",
            lang,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        print(f"\nInput[{lang}]: {text}")
        print("Detected:", detected)
        print("Translated:", translated)


if __name__ == "__main__":
    asyncio.run(main())
