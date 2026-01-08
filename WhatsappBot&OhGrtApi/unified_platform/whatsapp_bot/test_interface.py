"""
Test Interface for WhatsApp Bot.

Provides a web UI and API endpoint to test the bot without actual WhatsApp credentials.
Supports text messages and image uploads.
"""

import logging
import base64
import uuid
from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from whatsapp_bot.graph import process_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])


class TestMessage(BaseModel):
    """Test message input."""
    message: str
    phone: str = "919876543210"
    image_base64: Optional[str] = None  # Base64 encoded image
    image_caption: Optional[str] = None  # Optional caption for image


class TestResponse(BaseModel):
    """Test response output."""
    response_text: str
    intent: str
    response_type: str = "text"
    response_media_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/chat", response_model=TestResponse)
async def test_chat(msg: TestMessage):
    """
    Test endpoint to send messages and get bot responses directly.

    This bypasses WhatsApp and returns the response in the API response.
    Supports both text messages and images.
    """
    # Determine message type
    message_type = "text"
    image_bytes = None

    if msg.image_base64:
        message_type = "image"
        try:
            # Remove data URL prefix if present
            image_data = msg.image_base64
            if "," in image_data:
                image_data = image_data.split(",")[1]
            image_bytes = base64.b64decode(image_data)
            logger.info(f"Decoded image: {len(image_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode image: {e}")
            return TestResponse(
                response_text="Failed to decode the uploaded image.",
                intent="error",
                error=str(e),
            )

    # Create a mock WhatsApp message
    whatsapp_message = {
        "message_id": f"test_{msg.phone}_{uuid.uuid4().hex[:8]}",
        "from_number": msg.phone,
        "phone_number_id": "test_phone_id",
        "timestamp": "1704153600",
        "message_type": message_type,
        "text": msg.message if message_type == "text" else (msg.image_caption or msg.message or ""),
        "media_id": f"test_media_{uuid.uuid4().hex[:8]}" if message_type == "image" else None,
        "location": None,
        # Add image bytes directly for test interface (bypasses media download)
        "image_bytes": image_bytes,
        "caption": msg.image_caption or msg.message if message_type == "image" else None,
    }

    try:
        # Process through the graph
        result = await process_message(whatsapp_message)

        return TestResponse(
            response_text=result.get("response_text", "No response generated"),
            intent=result.get("intent", "unknown"),
            response_type=result.get("response_type", "text"),
            response_media_url=result.get("response_media_url"),
            error=result.get("error"),
        )
    except Exception as e:
        logger.error(f"Test chat error: {e}", exc_info=True)
        return TestResponse(
            response_text=f"Error processing message: {str(e)}",
            intent="error",
            error=str(e),
        )


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    phone: str = Form(default="919876543210"),
):
    """
    Upload an image file and get bot response.

    Alternative to sending base64 in JSON.
    """
    try:
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Create message with image
        msg = TestMessage(
            message=caption or "Analyze this image",
            phone=phone,
            image_base64=image_base64,
            image_caption=caption,
        )

        return await test_chat(msg)
    except Exception as e:
        logger.error(f"Image upload error: {e}", exc_info=True)
        return TestResponse(
            response_text=f"Failed to process uploaded image: {str(e)}",
            intent="error",
            error=str(e),
        )


@router.get("/", response_class=HTMLResponse)
async def test_ui():
    """Serve the test chat interface with image upload support."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Bot Test Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #128C7E 0%, #075E54 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .chat-container {
            width: 100%;
            max-width: 500px;
            height: 90vh;
            max-height: 800px;
            background: #ECE5DD;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: #075E54;
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .chat-header .avatar {
            width: 45px;
            height: 45px;
            background: #25D366;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        .chat-header .info h2 {
            font-size: 18px;
            font-weight: 500;
        }

        .chat-header .info p {
            font-size: 12px;
            opacity: 0.8;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .message {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 10px;
            position: relative;
            word-wrap: break-word;
        }

        .message.user {
            background: #DCF8C6;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .message.bot {
            background: white;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .message .text {
            font-size: 14px;
            line-height: 1.4;
            white-space: pre-wrap;
        }

        .message .image-container {
            margin-bottom: 8px;
        }

        .message .image-container img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            cursor: pointer;
        }

        .message .meta {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 5px;
            margin-top: 5px;
        }

        .message .time {
            font-size: 11px;
            color: #667781;
        }

        .message .intent {
            font-size: 10px;
            background: #128C7E;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
        }

        .message.bot .intent {
            background: #667781;
        }

        /* Image Preview */
        .image-preview-container {
            display: none;
            background: #F0F2F5;
            padding: 10px 15px;
            border-top: 1px solid #ddd;
        }

        .image-preview-container.active {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .image-preview {
            width: 60px;
            height: 60px;
            border-radius: 8px;
            object-fit: cover;
            border: 2px solid #128C7E;
        }

        .preview-info {
            flex: 1;
        }

        .preview-info .filename {
            font-size: 13px;
            font-weight: 500;
            color: #333;
        }

        .preview-info .filesize {
            font-size: 11px;
            color: #667781;
        }

        .remove-image {
            width: 30px;
            height: 30px;
            border: none;
            background: #FF4444;
            color: white;
            border-radius: 50%;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .remove-image:hover {
            background: #CC0000;
        }

        .chat-input {
            background: #F0F2F5;
            padding: 10px 15px;
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .attach-btn {
            width: 40px;
            height: 40px;
            border: none;
            background: transparent;
            color: #667781;
            border-radius: 50%;
            cursor: pointer;
            font-size: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .attach-btn:hover {
            background: #ddd;
            color: #128C7E;
        }

        .chat-input input[type="text"] {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 25px;
            font-size: 15px;
            outline: none;
        }

        .chat-input input[type="file"] {
            display: none;
        }

        .chat-input button.send-btn {
            width: 50px;
            height: 50px;
            border: none;
            background: #128C7E;
            color: white;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }

        .chat-input button.send-btn:hover {
            background: #075E54;
        }

        .chat-input button:disabled {
            background: #ccc !important;
            cursor: not-allowed;
        }

        .typing {
            display: flex;
            gap: 4px;
            padding: 15px;
            background: white;
            border-radius: 10px;
            width: fit-content;
        }

        .typing span {
            width: 8px;
            height: 8px;
            background: #667781;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 10px 15px;
            background: #F0F2F5;
            border-top: 1px solid #ddd;
        }

        .suggestion {
            padding: 8px 15px;
            background: white;
            border: 1px solid #128C7E;
            color: #128C7E;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .suggestion:hover {
            background: #128C7E;
            color: white;
        }

        .error {
            background: #FFE4E4 !important;
            border-left: 3px solid #FF4444;
        }

        /* Image modal */
        .image-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .image-modal.active {
            display: flex;
        }

        .image-modal img {
            max-width: 90%;
            max-height: 90%;
            border-radius: 8px;
        }

        .image-modal .close-modal {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            background: white;
            border: none;
            border-radius: 50%;
            font-size: 24px;
            cursor: pointer;
        }

        /* Analysis type selector */
        .analysis-selector {
            display: none;
            background: #F0F2F5;
            padding: 8px 15px;
            border-top: 1px solid #ddd;
            gap: 8px;
            flex-wrap: wrap;
        }

        .analysis-selector.active {
            display: flex;
        }

        .analysis-option {
            padding: 6px 12px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 15px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .analysis-option:hover,
        .analysis-option.selected {
            background: #128C7E;
            color: white;
            border-color: #128C7E;
        }

        /* Status indicator */
        .status-indicator {
            position: fixed;
            bottom: 20px;
            left: 20px;
            padding: 8px 16px;
            background: rgba(0,0,0,0.7);
            color: white;
            border-radius: 20px;
            font-size: 12px;
            display: none;
            z-index: 1001;
        }

        .status-indicator.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="avatar">🤖</div>
            <div class="info">
                <h2>D23 AI Bot</h2>
                <p>WhatsApp Test Interface</p>
            </div>
        </div>

        <div class="chat-messages" id="messages">
            <div class="message bot">
                <div class="text">👋 Welcome to D23 AI Bot Test Interface!

Try asking me about:
• Horoscope (e.g., "Aries horoscope today")
• Weather (e.g., "Weather in Delhi")
• News (e.g., "Latest news")

📷 Upload images using the 📎 button:
• Click 📎 to select an image
• Add an optional caption
• Click send ➤</div>
                <div class="meta">
                    <span class="time">Now</span>
                </div>
            </div>
        </div>

        <div class="suggestions">
            <span class="suggestion" onclick="sendSuggestion(this)">Aries horoscope</span>
            <span class="suggestion" onclick="sendSuggestion(this)">Weather in Mumbai</span>
            <span class="suggestion" onclick="sendSuggestion(this)">Hello!</span>
            <span class="suggestion" onclick="sendSuggestion(this)">Help</span>
        </div>

        <div class="analysis-selector" id="analysisSelector">
            <span class="analysis-option selected" data-type="describe">📝 Describe</span>
            <span class="analysis-option" data-type="ocr">📄 Extract Text</span>
            <span class="analysis-option" data-type="food">🍕 Identify Food</span>
            <span class="analysis-option" data-type="document">📋 Analyze Doc</span>
            <span class="analysis-option" data-type="receipt">🧾 Read Receipt</span>
        </div>

        <div class="image-preview-container" id="imagePreview">
            <img class="image-preview" id="previewImg" src="" alt="Preview">
            <div class="preview-info">
                <div class="filename" id="fileName">image.jpg</div>
                <div class="filesize" id="fileSize">0 KB</div>
            </div>
            <button class="remove-image" onclick="removeImage()">✕</button>
        </div>

        <div class="chat-input">
            <input type="file" id="imageInput" accept="image/*">
            <button class="attach-btn" id="attachBtn" title="Attach Image">📎</button>
            <input type="text" id="messageInput" placeholder="Type a message..." onkeypress="handleKeyPress(event)">
            <button class="send-btn" id="sendBtn">➤</button>
        </div>
    </div>

    <!-- Image Modal -->
    <div class="image-modal" id="imageModal">
        <button class="close-modal" id="closeModalBtn">✕</button>
        <img id="modalImage" src="" alt="Full Image">
    </div>

    <!-- Status indicator for debugging -->
    <div class="status-indicator" id="statusIndicator"></div>

    <script>
        // DOM Elements
        const messagesContainer = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const attachBtn = document.getElementById('attachBtn');
        const imageInput = document.getElementById('imageInput');
        const imagePreviewContainer = document.getElementById('imagePreview');
        const previewImg = document.getElementById('previewImg');
        const analysisSelector = document.getElementById('analysisSelector');
        const imageModal = document.getElementById('imageModal');
        const modalImage = document.getElementById('modalImage');
        const closeModalBtn = document.getElementById('closeModalBtn');
        const statusIndicator = document.getElementById('statusIndicator');

        // State
        let selectedImage = null;
        let selectedAnalysisType = 'describe';
        let isProcessing = false;

        // Show status message
        function showStatus(msg, duration = 2000) {
            statusIndicator.textContent = msg;
            statusIndicator.classList.add('active');
            setTimeout(() => statusIndicator.classList.remove('active'), duration);
        }

        // Attach button click handler
        attachBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Attach button clicked');
            imageInput.click();
        });

        // Image input change handler
        imageInput.addEventListener('change', function(e) {
            console.log('Image input changed');
            handleImageSelect(e);
        });

        // Send button click handler
        sendBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Send button clicked');
            sendMessage();
        });

        // Close modal handlers
        closeModalBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            closeImageModal();
        });

        imageModal.addEventListener('click', function(e) {
            if (e.target === imageModal) {
                closeImageModal();
            }
        });

        // Analysis type selector
        document.querySelectorAll('.analysis-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.analysis-option').forEach(o => o.classList.remove('selected'));
                this.classList.add('selected');
                selectedAnalysisType = this.dataset.type;
                console.log('Selected analysis type:', selectedAnalysisType);

                const prompts = {
                    'describe': 'Describe this image in detail',
                    'ocr': 'Extract all text from this image',
                    'food': 'What food is in this image?',
                    'document': 'Analyze this document',
                    'receipt': 'Extract receipt details'
                };
                messageInput.placeholder = prompts[selectedAnalysisType] || 'Type a caption...';
            });
        });

        function formatTime() {
            return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function addMessage(text, isUser, intent = null, isError = false, imageData = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}${isError ? ' error' : ''}`;

            let metaHtml = `<span class="time">${formatTime()}</span>`;
            if (intent && !isUser) {
                metaHtml = `<span class="intent">${intent}</span>` + metaHtml;
            }

            let imageHtml = '';
            if (imageData) {
                const imgId = 'img_' + Date.now();
                imageHtml = `
                    <div class="image-container">
                        <img id="${imgId}" src="${imageData}" alt="Uploaded image">
                    </div>
                `;
                // Add click handler after element is added
                setTimeout(() => {
                    const imgEl = document.getElementById(imgId);
                    if (imgEl) {
                        imgEl.addEventListener('click', () => openImageModal(imageData));
                    }
                }, 0);
            }

            const textContent = (text || '').split('\\n').join('<br>');

            messageDiv.innerHTML = `
                ${imageHtml}
                <div class="text">${textContent}</div>
                <div class="meta">${metaHtml}</div>
            `;

            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addTypingIndicator() {
            const typing = document.createElement('div');
            typing.className = 'typing';
            typing.id = 'typing';
            typing.innerHTML = '<span></span><span></span><span></span>';
            messagesContainer.appendChild(typing);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function removeTypingIndicator() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }

        function handleImageSelect(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) {
                console.log('No file selected');
                return;
            }

            console.log('File selected:', file.name, file.type, file.size);

            if (!file.type.startsWith('image/')) {
                alert('Please select an image file');
                return;
            }

            if (file.size > 10 * 1024 * 1024) {
                alert('Image size must be less than 10MB');
                return;
            }

            showStatus('Loading image...');

            const reader = new FileReader();

            reader.onload = function(e) {
                console.log('FileReader loaded, data length:', e.target.result.length);
                selectedImage = e.target.result;
                previewImg.src = selectedImage;
                document.getElementById('fileName').textContent = file.name;
                document.getElementById('fileSize').textContent = formatFileSize(file.size);
                imagePreviewContainer.classList.add('active');
                analysisSelector.classList.add('active');
                messageInput.placeholder = 'Add a caption (optional) or click send...';
                messageInput.focus();
                showStatus('Image ready to send');
            };

            reader.onerror = function(e) {
                console.error('FileReader error:', e);
                alert('Error reading file. Please try again.');
            };

            reader.readAsDataURL(file);
        }

        function removeImage() {
            console.log('Removing image');
            selectedImage = null;
            imageInput.value = '';
            imagePreviewContainer.classList.remove('active');
            analysisSelector.classList.remove('active');
            messageInput.placeholder = 'Type a message...';
        }

        function openImageModal(src) {
            console.log('Opening image modal');
            modalImage.src = src;
            imageModal.classList.add('active');
        }

        function closeImageModal() {
            console.log('Closing image modal');
            imageModal.classList.remove('active');
        }

        async function sendMessage() {
            if (isProcessing) {
                console.log('Already processing, ignoring');
                return;
            }

            const message = messageInput.value.trim();
            const hasImage = selectedImage !== null;

            console.log('sendMessage called - message:', message, 'hasImage:', hasImage);

            if (!message && !hasImage) {
                console.log('Nothing to send');
                return;
            }

            isProcessing = true;
            sendBtn.disabled = true;

            // Determine display message
            let displayMessage = message;
            if (hasImage && !message) {
                const prompts = {
                    'describe': 'Describe this image',
                    'ocr': 'Extract text from this image',
                    'food': 'Identify food in this image',
                    'document': 'Analyze this document',
                    'receipt': 'Read this receipt'
                };
                displayMessage = prompts[selectedAnalysisType] || 'Analyze this image';
            }

            // Store image before clearing
            const imageToSend = selectedImage;
            const captionToSend = message || displayMessage;

            // Add user message to chat
            addMessage(displayMessage, true, null, false, hasImage ? imageToSend : null);

            // Clear inputs
            messageInput.value = '';
            if (hasImage) {
                removeImage();
            }

            // Show typing indicator
            addTypingIndicator();
            showStatus('Processing...');

            try {
                const payload = {
                    message: captionToSend,
                    phone: '919876543210'
                };

                if (imageToSend) {
                    payload.image_base64 = imageToSend;
                    payload.image_caption = captionToSend;
                    console.log('Sending image, base64 length:', imageToSend.length);
                }

                console.log('Sending request to /test/chat');

                const response = await fetch('/test/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                console.log('Response status:', response.status);

                const data = await response.json();
                console.log('Response data:', data);

                removeTypingIndicator();

                if (data.error) {
                    addMessage(data.response_text || data.error, false, data.intent, true);
                } else {
                    addMessage(data.response_text, false, data.intent);
                }

                showStatus('Done!');
            } catch (error) {
                console.error('Fetch error:', error);
                removeTypingIndicator();
                addMessage('Failed to connect to the bot: ' + error.message, false, 'error', true);
                showStatus('Error: ' + error.message, 3000);
            }

            isProcessing = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }

        function sendSuggestion(el) {
            messageInput.value = el.textContent;
            sendMessage();
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // Handle paste for images
        document.addEventListener('paste', function(event) {
            const items = event.clipboardData && event.clipboardData.items;
            if (!items) return;

            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    event.preventDefault();
                    const file = items[i].getAsFile();
                    if (file) {
                        console.log('Pasted image:', file.name, file.type, file.size);
                        // Create a fake event for handleImageSelect
                        handleImageSelect({ target: { files: [file] } });
                    }
                    break;
                }
            }
        });

        // ESC to close modal
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeImageModal();
            }
        });

        // Focus input on load
        messageInput.focus();

        console.log('Test interface loaded successfully');
    </script>
</body>
</html>
"""
