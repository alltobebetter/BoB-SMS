from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import cloudscraper
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# 设置密码
CORRECT_PASSWORD = "114514"  # 替换成你想要的密码

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_phone_data():
    current_dir = os.path.dirname(os.path.dirname(__file__))
    json_path = os.path.join(current_dir, 'data', 'info.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_messages(url):
    scraper = cloudscraper.create_scraper(delay=10)
    
    try:
        response = scraper.get(url)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        message_rows = soup.find_all('div', class_='row border-bottom table-hover')
        
        messages = []
        for row in message_rows[:10]:
            sender = row.find('div', class_='mobile_hide').text.strip()
            content = row.find('div', class_='col-xs-12 col-md-8').text.strip()
            
            message = {
                'sender': sender,
                'content': content
            }
            messages.append(message)
            
        return messages
    except Exception as e:
        print(f'Error: {e}')
        return None

@app.get("/api/messages/{phone_id}")
async def read_messages(phone_id: int, pass_: str = Query(..., alias="pass")):
    # 验证密码
    if pass_ != CORRECT_PASSWORD:
        raise HTTPException(
            status_code=403,
            detail="Invalid password"
        )
    
    phone_data = load_phone_data()
    phone = next((p for p in phone_data["phones"] if p["id"] == phone_id), None)
    
    if not phone:
        raise HTTPException(
            status_code=404,
            detail="Phone not found"
        )
        
    messages = get_messages(phone["url"])
    if messages:
        public_phone = {
            "id": phone["id"],
            "number": phone["number"],
            "location": phone["location"]
        }
        return {"status": "success", "data": messages, "phone": public_phone}
    
    raise HTTPException(
        status_code=500,
        detail="Failed to fetch messages"
    )

@app.get("/api/phones")
async def get_phones():
    phone_data = load_phone_data()
    public_phones = [{
        "id": phone["id"],
        "number": phone["number"],
        "location": phone["location"]
    } for phone in phone_data["phones"]]
    return {"status": "success", "data": public_phones}

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>临时手机号服务</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Inter', sans-serif;
            }
            
            body {
                line-height: 1.6;
                height: 100vh;
                overflow: hidden;
            }
            
            .container {
                display: grid;
                grid-template-columns: 300px 1fr;
                height: 100vh;
            }
            
            .sidebar {
                background: #1a1a1a;
                color: #ffffff;
                padding: 2.5rem;
                border-right: 1px solid #333;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                position: relative;
            }
            
            .sidebar::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: linear-gradient(to bottom, #333, transparent);
            }
            
            .sidebar-content {
                position: relative;
            }
            
            h1 {
                font-size: 1.75rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
                padding-bottom: 1.5rem;
                border-bottom: 2px solid #333;
                position: relative;
            }
            
            h1::after {
                content: '';
                position: absolute;
                bottom: -2px;
                left: 0;
                width: 50%;
                height: 2px;
                background: #666;
            }
            
            .description {
                font-size: 0.95rem;
                color: #999;
                margin-bottom: 3rem;
                line-height: 1.8;
            }
            
            .links-section {
                background: #222;
                padding: 1.5rem;
                margin-top: auto;
            }
            
            .links-title {
                font-size: 0.85rem;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 1rem;
            }
            
            .link-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                color: #999;
                text-decoration: none;
                padding: 0.75rem;
                transition: all 0.2s ease;
                margin-bottom: 0.5rem;
            }
            
            .link-item:hover {
                color: #fff;
                background: #2a2a2a;
            }
            
            .link-text {
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            .main-content {
                background: #ffffff;
                position: relative;
                overflow: hidden;
            }
            
            .phone-page, .message-page {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                padding: 2rem;
                overflow-y: auto;
                transition: transform 0.3s ease;
            }
            
            .phone-page {
                transform: translateX(0);
            }
            
            .phone-page.hidden {
                transform: translateX(-100%);
            }
            
            .message-page {
                transform: translateX(100%);
                background: #fff;
            }
            
            .message-page.visible {
                transform: translateX(0);
            }
            
            .phone-grid {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }
            
            .phone-card {
                border: 1px solid #e5e5e5;
                padding: 1.25rem;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .phone-card:hover {
                border-color: #000;
                background: #f9f9f9;
            }
            
            .phone-number {
                font-size: 1.1rem;
                font-weight: 500;
                margin-bottom: 0.5rem;
            }
            
            .location {
                font-size: 0.9rem;
                color: #666;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .message-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #eee;
            }
            
            .header-left {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .back-button {
                background: none;
                border: none;
                cursor: pointer;
                padding: 0.5rem;
                margin-right: 1rem;
                color: #666;
            }
            
            .refresh-button {
                position: relative;
                background: none;
                border: 1px solid #eee;
                padding: 0.5rem 1rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                transition: all 0.2s ease;
            }
            
            .refresh-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .refresh-button .spinner {
                display: none;
                width: 16px;
                height: 16px;
                border: 2px solid #666;
                border-top-color: transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            .refresh-button.loading .spinner {
                display: inline-block;
            }
            
            .refresh-button.loading .refresh-icon {
                display: none;
            }
            
            .message-item {
                padding: 1rem;
                border: 1px solid #eee;
                margin-bottom: 0.75rem;
            }
            
            .message-sender {
                font-weight: 500;
                margin-bottom: 0.25rem;
            }
            
            .message-content {
                font-size: 0.9rem;
                color: #666;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            @media (max-width: 768px) {
                .container {
                    grid-template-columns: 1fr;
                }
                
                .sidebar {
                    display: none;
                }
                
                .main-content {
                    height: 100vh;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <div class="sidebar-content">
                    <h1>临时手机号服务</h1>
                    <p class="description">
                        提供临时手机号接收短信服务，支持多个国家号码。
                        所有号码实时更新，完全免费使用。
                    </p>
                </div>
                <div class="links-section">
                    <div class="links-title">相关链接</div>
                    <a href="https://aibob.click" target="_blank" class="link-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M16 16s-1.5-2-4-2-4 2-4 2"></path>
                            <line x1="9" y1="9" x2="9.01" y2="9"></line>
                            <line x1="15" y1="9" x2="15.01" y2="9"></line>
                        </svg>
                        <span class="link-text">AI智能助手</span>
                    </a>
                    <a href="https://buy.aibob.click/sms" target="_blank" class="link-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"></path>
                            <path d="M4 6v12c0 1.1.9 2 2 2h14v-4"></path>
                            <path d="M18 12H4"></path>
                        </svg>
                        <span class="link-text">购买API服务</span>
                    </a>
                    <a href="/docs" target="_blank" class="link-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                        <span class="link-text">API文档</span>
                    </a>
                </div>
            </div>
            
            <div class="main-content">
                <div class="phone-page" id="phonePage">
                    <div class="phone-grid" id="phoneList"></div>
                </div>
                <div class="message-page" id="messagePage">
                    <div class="message-header">
                        <div class="header-left">
                            <button class="back-button" onclick="goBack()">
                                ← 返回
                            </button>
                            <div>
                                <h2 id="currentNumber"></h2>
                                <div id="currentLocation" style="color: #666;"></div>
                            </div>
                        </div>
                        <button class="refresh-button" onclick="refreshMessages()">
                            <div class="spinner"></div>
                            <svg class="refresh-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                            </svg>
                            刷新
                        </button>
                    </div>
                    <div id="messagesList"></div>
                </div>
            </div>
        </div>

        <script>
            const PASSWORD = '114514';
            let currentPhoneId = null;
            let isRefreshing = false;
            
            async function loadPhones() {
                const response = await fetch('/api/phones');
                const data = await response.json();
                
                const phoneList = document.getElementById('phoneList');
                phoneList.innerHTML = data.data.map(phone => `
                    <div class="phone-card" onclick="showMessages(${phone.id}, '${phone.number}', '${phone.location}')">
                        <div class="phone-number">${phone.number}</div>
                        <div class="location">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                <circle cx="12" cy="10" r="3"></circle>
                            </svg>
                            ${phone.location}
                        </div>
                    </div>
                `).join('');
            }
            
            async function showMessages(phoneId, number, location) {
                currentPhoneId = phoneId;
                document.getElementById('phonePage').classList.add('hidden');
                document.getElementById('messagePage').classList.add('visible');
                document.getElementById('currentNumber').textContent = number;
                document.getElementById('currentLocation').textContent = location;
                await loadMessages(phoneId);
            }
            
            async function loadMessages(phoneId) {
                const response = await fetch(`/api/messages/${phoneId}?pass=${PASSWORD}`);
                const data = await response.json();
                
                const messagesList = document.getElementById('messagesList');
                messagesList.innerHTML = data.data.map(message => `
                    <div class="message-item">
                        <div class="message-sender">${message.sender}</div>
                        <div class="message-content">${message.content}</div>
                    </div>
                `).join('');
            }
            
            async function refreshMessages() {
                if (isRefreshing || !currentPhoneId) return;
                
                const refreshBtn = document.querySelector('.refresh-button');
                refreshBtn.classList.add('loading');
                refreshBtn.disabled = true;
                isRefreshing = true;
                
                try {
                    await loadMessages(currentPhoneId);
                } finally {
                    refreshBtn.classList.remove('loading');
                    refreshBtn.disabled = false;
                    isRefreshing = false;
                }
            }
            
            function goBack() {
                document.getElementById('phonePage').classList.remove('hidden');
                document.getElementById('messagePage').classList.remove('visible');
            }
            
            loadPhones();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
