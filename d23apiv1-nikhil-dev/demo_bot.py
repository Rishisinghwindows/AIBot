from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import uvicorn

app = FastAPI()

VERIFY_TOKEN = "mobirizer_2025_d23"

@app.get("/whatsapp/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return PlainTextResponse(params.get("hub.challenge"))

    return PlainTextResponse("Verification failed", status_code=403)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9002)
