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
    <html>
    <head>
        <title>SMS Receiver</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: #fafafa;
            }
            
            .card {
                background: white;
                border-radius: 16px;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-4px);
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.05);
            }
            
            .message-card {
                background: white;
                border-radius: 12px;
                transition: all 0.2s ease;
            }
            
            .message-card:hover {
                transform: translateX(4px);
            }
            
            .custom-scrollbar::-webkit-scrollbar {
                width: 4px;
            }
            
            .custom-scrollbar::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            
            .custom-scrollbar::-webkit-scrollbar-thumb {
                background: #ddd;
                border-radius: 2px;
            }
        </style>
    </head>
    <body class="min-h-screen bg-gray-50">
        <div id="app" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <!-- 主页面 -->
            <div id="home-page" class="py-12">
                <div class="text-center mb-16">
                    <h1 class="text-4xl font-bold text-gray-900 mb-3">在线短信接收</h1>
                    <p class="text-gray-500">选择一个虚拟号码来接收短信验证码</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="phones-container">
                    <!-- 手机卡片将在这里动态生成 -->
                </div>
            </div>

            <!-- 消息页面 -->
            <div id="messages-page" class="py-8 hidden">
                <div class="flex items-center justify-between mb-8">
                    <button onclick="showHome()" class="flex items-center text-gray-600 hover:text-gray-900">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                        </svg>
                        返回
                    </button>
                    <h2 class="text-xl font-semibold text-gray-900" id="phone-title"></h2>
                    <button onclick="refreshMessages()" class="flex items-center bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                        </svg>
                        刷新
                    </button>
                </div>
                
                <div id="messages-container" class="space-y-4 custom-scrollbar">
                    <!-- 消息将在这里动态生成 -->
                </div>
            </div>

            <!-- 加载动画 -->
            <div id="loading" class="hidden fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
                <div class="bg-white p-6 rounded-xl shadow-lg">
                    <div class="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
                </div>
            </div>
        </div>

        <script>
            let currentPhoneId = null;

            function showLoading() {
                document.getElementById('loading').classList.remove('hidden');
            }

            function hideLoading() {
                document.getElementById('loading').classList.add('hidden');
            }

            function showHome() {
                document.getElementById('messages-page').classList.add('hidden');
                document.getElementById('home-page').classList.remove('hidden');
                currentPhoneId = null;
            }

            function showMessages() {
                document.getElementById('home-page').classList.add('hidden');
                document.getElementById('messages-page').classList.remove('hidden');
            }

            function loadPhones() {
                try {
                    showLoading();
                    fetch('/api/phones')
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                const container = document.getElementById('phones-container');
                    const response = await fetch('/api/phones');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const container = document.getElementById('phones-container');
                        container.innerHTML = data.data.map((phone, index) => `
                            <div class="animate__animated animate__fadeInUp" style="animation-delay: ${index * 0.1}s">
                                <div class="phone-card rounded-2xl shadow-lg p-8 cursor-pointer"
                                     onclick="loadMessages(${phone.id})">
                                    <div class="flex items-center justify-between mb-6">
                                        <span class="px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                                            ${phone.location}
                                        </span>
                                        <i data-feather="phone-call" class="text-blue-500"></i>
                                    </div>
                                    <h3 class="text-2xl font-bold text-gray-800 mb-4">${phone.number}</h3>
                                    <div class="flex items-center text-gray-600 hover:text-blue-600 transition-colors">
                                        <span class="mr-2">查看短信</span>
                                        <i data-feather="arrow-right"></i>
                                    </div>
                                </div>
                            </div>
                        `).join('');
                        feather.replace();
                    }
                } catch (error) {
                    console.error('Error:', error);
                } finally {
                    hideLoading();
                }
            }

            async function loadMessages(phoneId) {
                try {
                    showLoading();
                    currentPhoneId = phoneId;
                    const response = await fetch(`/api/messages/${phoneId}?pass=your_password_here`);
                    
                    if (response.status === 403) {
                        alert('访问被拒绝：密码错误');
                        hideLoading();
                        return;
                    }
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        document.getElementById('phone-title').textContent = `${data.phone.number} (${data.phone.location})`;
                        const container = document.getElementById('messages-container');
                        container.innerHTML = data.data.map((message, index) => `
                            <div class="animate__animated animate__fadeInRight" style="animation-delay: ${index * 0.05}s">
                                <div class="message-card glass-effect rounded-xl p-6 hover:shadow-lg transition-all">
                                    <div class="flex items-center justify-between mb-3">
                                        <div class="flex items-center space-x-3">
                                            <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                                                <i data-feather="message-circle" class="text-blue-500"></i>
                                            </div>
                                            <span class="font-medium text-gray-700">${message.sender}</span>
                                        </div>
                                    </div>
                                    <p class="text-gray-600 pl-13">${message.content}</p>
                                </div>
                            </div>
                        `).join('');
                        feather.replace();
                        showMessages();
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('获取消息失败');
                } finally {
                    hideLoading();
                }
            }

            function refreshMessages() {
                if (currentPhoneId) {
                    loadMessages(currentPhoneId);
                }
            }

            // 页面加载时获取手机列表
            document.addEventListener('DOMContentLoaded', loadPhones);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
