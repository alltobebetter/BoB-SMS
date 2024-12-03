from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import cloudscraper
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

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
        for row in message_rows[:10]:  # 获取10条消息
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
async def read_messages(phone_id: int):
    phone_data = load_phone_data()
    phone = next((p for p in phone_data["phones"] if p["id"] == phone_id), None)
    
    if not phone:
        return {"status": "error", "message": "Phone not found"}
        
    messages = get_messages(phone["url"])
    if messages:
        return {"status": "success", "data": messages, "phone": phone}
    return {"status": "error", "message": "Failed to fetch messages"}

@app.get("/api/phones")
async def get_phones():
    phone_data = load_phone_data()
    return {"status": "success", "data": phone_data["phones"]}

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>在线短信接收</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/@heroicons/react@2.0.18/outline/esm/index.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', sans-serif;
                background-color: #f3f4f6;
            }
            .phone-card {
                transition: transform 0.2s ease-in-out;
            }
            .phone-card:hover {
                transform: translateY(-5px);
            }
            .messages-container {
                max-height: 80vh;
                overflow-y: auto;
            }
            .loading {
                backdrop-filter: blur(5px);
            }
        </style>
    </head>
    <body>
        <div id="app" class="min-h-screen">
            <!-- 主页面 -->
            <div id="home-page" class="container mx-auto px-4 py-8">
                <h1 class="text-4xl font-bold text-center text-gray-800 mb-8">在线短信接收服务</h1>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="phones-container">
                    <!-- 手机卡片将在这里动态生成 -->
                </div>
            </div>

            <!-- 消息页面 -->
            <div id="messages-page" class="container mx-auto px-4 py-8 hidden">
                <div class="flex items-center justify-between mb-8">
                    <button onclick="showHome()" class="flex items-center text-blue-600 hover:text-blue-800">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                        </svg>
                        返回
                    </button>
                    <h2 class="text-2xl font-bold text-gray-800" id="phone-title"></h2>
                    <button onclick="refreshMessages()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        刷新
                    </button>
                </div>
                <div id="messages-container" class="space-y-4">
                    <!-- 消息将在这里动态生成 -->
                </div>
            </div>

            <!-- 加载动画 -->
            <div id="loading" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center loading">
                <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
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

            async function loadPhones() {
                try {
                    showLoading();
                    const response = await fetch('/api/phones');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const container = document.getElementById('phones-container');
                        container.innerHTML = data.data.map(phone => `
                            <div class="phone-card bg-white rounded-xl shadow-lg p-6 cursor-pointer hover:shadow-xl"
                                 onclick="loadMessages(${phone.id})">
                                <div class="flex items-center justify-between mb-4">
                                    <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                                        ${phone.location}
                                    </span>
                                </div>
                                <h3 class="text-xl font-semibold text-gray-800 mb-2">${phone.number}</h3>
                                <p class="text-gray-600">点击查看最新短信</p>
                            </div>
                        `).join('');
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
                    const response = await fetch(`/api/messages/${phoneId}`);
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        document.getElementById('phone-title').textContent = `${data.phone.number} (${data.phone.location})`;
                        const container = document.getElementById('messages-container');
                        container.innerHTML = data.data.map(message => `
                            <div class="bg-white rounded-lg shadow p-4">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-sm font-medium text-gray-600">${message.sender}</span>
                                </div>
                                <p class="text-gray-800">${message.content}</p>
                            </div>
                        `).join('');
                        showMessages();
                    }
                } catch (error) {
                    console.error('Error:', error);
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
