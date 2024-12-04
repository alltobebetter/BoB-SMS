from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import cloudscraper
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# 设置密码
CORRECT_PASSWORD = "your_password_here"  # 替换成你想要的密码

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
        <title>在线短信接收</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
        <script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script>
        <style>
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #f6f8ff 0%, #f1f5ff 100%);
            }
            
            .glass-effect {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .phone-card {
                transition: all 0.3s ease;
                background: linear-gradient(145deg, #ffffff, #f5f7ff);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
            
            .phone-card:hover {
                transform: translateY(-5px) scale(1.02);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            }
            
            .gradient-text {
                background: linear-gradient(135deg, #2563eb, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .message-card {
                transition: all 0.2s ease;
            }
            
            .message-card:hover {
                transform: translateX(5px);
            }
            
            .custom-scrollbar::-webkit-scrollbar {
                width: 6px;
            }
            
            .custom-scrollbar::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 3px;
            }
            
            .custom-scrollbar::-webkit-scrollbar-thumb {
                background: #c5c5c5;
                border-radius: 3px;
            }
            
            .pulse {
                animation: pulse 2s infinite;
            }
            
            @keyframes float {
                0% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
                100% { transform: translateY(0px); }
            }
            
            .float {
                animation: float 3s ease-in-out infinite;
            }
        </style>
    </head>
    <body class="min-h-screen">
        <div id="app">
            <!-- 主页面 -->
            <div id="home-page" class="container mx-auto px-4 py-12">
                <div class="text-center mb-16 animate__animated animate__fadeIn">
                    <h1 class="text-5xl font-bold gradient-text mb-4">在线短信接收服务</h1>
                    <p class="text-gray-600 text-lg">选择一个虚拟号码来接收短信验证码</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" id="phones-container">
                    <!-- 手机卡片将在这里动态生成 -->
                </div>
            </div>

            <!-- 消息页面 -->
            <div id="messages-page" class="container mx-auto px-4 py-8 hidden">
                <div class="glass-effect rounded-2xl p-6 mb-8">
                    <div class="flex items-center justify-between">
                        <button onclick="showHome()" class="flex items-center space-x-2 text-blue-600 hover:text-blue-800 transition-colors">
                            <i data-feather="arrow-left"></i>
                            <span>返回</span>
                        </button>
                        <h2 class="text-2xl font-bold gradient-text" id="phone-title"></h2>
                        <button onclick="refreshMessages()" class="flex items-center space-x-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                            <i data-feather="refresh-cw"></i>
                            <span>刷新</span>
                        </button>
                    </div>
                </div>
                
                <div id="messages-container" class="space-y-4 custom-scrollbar" style="max-height: 70vh; overflow-y: auto">
                    <!-- 消息将在这里动态生成 -->
                </div>
            </div>

            <!-- 加载动画 -->
            <div id="loading" class="hidden fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50">
                <div class="bg-white p-8 rounded-2xl shadow-xl">
                    <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500 mx-auto"></div>
                    <p class="text-gray-600 mt-4">加载中...</p>
                </div>
            </div>
        </div>

        <script>
            // 初始化 Feather Icons
            feather.replace();
            
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
