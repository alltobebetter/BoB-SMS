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
                background: #ffffff;
                color: #1a1a1a;
                line-height: 1.6;
            }
            
            .container {
                display: grid;
                grid-template-columns: 300px 1fr;
                min-height: 100vh;
            }
            
            .sidebar {
                padding: 2rem;
                border-right: 1px solid #e5e5e5;
            }
            
            .main-content {
                padding: 2rem;
            }
            
            h1 {
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
            }
            
            .description {
                font-size: 0.9rem;
                color: #666;
                margin-bottom: 2rem;
            }
            
            .phone-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 1rem;
            }
            
            .phone-card {
                border: 1px solid #e5e5e5;
                padding: 1.5rem;
                transition: all 0.2s ease;
                cursor: pointer;
            }
            
            .phone-card:hover {
                border-color: #000;
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
            
            .messages {
                margin-top: 2rem;
                display: none;
            }
            
            .message-item {
                padding: 1rem;
                border: 1px solid #e5e5e5;
                margin-bottom: 0.5rem;
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
                    border-right: none;
                    border-bottom: 1px solid #e5e5e5;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <h1>临时手机号服务</h1>
                <p class="description">
                    提供临时手机号接收短信服务，支持多个国家号码。
                    所有号码实时更新，完全免费使用。
                </p>
            </div>
            
            <div class="main-content">
                <div class="phone-grid" id="phoneList"></div>
                <div class="messages" id="messagesList"></div>
            </div>
        </div>

        <script>
            const PASSWORD = '114514';
            
            async function loadPhones() {
                const response = await fetch('/api/phones');
                const data = await response.json();
                
                const phoneList = document.getElementById('phoneList');
                phoneList.innerHTML = data.data.map(phone => `
                    <div class="phone-card" onclick="loadMessages(${phone.id})">
                        <div class="phone-number">${phone.number}</div>
                        <div class="location">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                <circle cx="12" cy="10" r="3"></circle>
                            </svg>
                            ${phone.location}
                        </div>
                    </div>
                `).join('');
            }
            
            async function loadMessages(phoneId) {
                const response = await fetch(`/api/messages/${phoneId}?pass=${PASSWORD}`);
                const data = await response.json();
                
                const messagesList = document.getElementById('messagesList');
                messagesList.style.display = 'block';
                messagesList.innerHTML = data.data.map(message => `
                    <div class="message-item">
                        <div class="message-sender">${message.sender}</div>
                        <div class="message-content">${message.content}</div>
                    </div>
                `).join('');
            }
            
            loadPhones();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
