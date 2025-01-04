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
                padding: 2rem;
                border-right: 1px solid #333;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
            }
            
            .sidebar::before, .sidebar::after {
                content: '';
                position: absolute;
                left: 2rem;
                right: 2rem;
                height: 1px;
                background: linear-gradient(to right, transparent, #333, transparent);
            }
            
            .sidebar::before {
                top: 2rem;
            }
            
            .sidebar::after {
                bottom: 2rem;
            }
            
            .sidebar-content {
                position: relative;
                padding: 2rem 0;
            }
            
            .sidebar-content::before {
                content: '';
                position: absolute;
                left: -2rem;
                top: 0;
                bottom: 0;
                width: 3px;
                background: linear-gradient(to bottom, transparent, #333, transparent);
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
            
            h1 {
                font-size: 1.75rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
            }
            
            .description {
                font-size: 0.9rem;
                color: #999;
                margin-bottom: 2rem;
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
            
            .refresh-button {
                background: none;
                border: 1px solid #eee;
                border-radius: 4px;
                padding: 0.5rem 1rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                transition: all 0.2s ease;
            }
            
            .refresh-button:hover {
                background: #f5f5f5;
                border-color: #ddd;
            }
            
            .back-button {
                background: none;
                border: none;
                cursor: pointer;
                padding: 0.5rem;
                margin-right: 1rem;
                color: #666;
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
            
            @media (max-width: 768px) {
                .container {
                    grid-template-columns: 1fr;
                }
                
                .sidebar {
                    padding: 1rem;
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
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
