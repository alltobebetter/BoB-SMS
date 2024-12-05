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
        <title>临时短信接收</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
        <script src="https://unpkg.com/phosphor-icons"></script>
        <style>
            body {
                font-family: 'Noto Sans SC', sans-serif;
                background-color: #fafafa;
            }
            
            .card {
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .message-item {
                border-left: 3px solid #3b82f6;
                background: white;
                transition: all 0.2s ease;
            }
            
            .message-item:hover {
                border-left-width: 5px;
            }
            
            .custom-scrollbar::-webkit-scrollbar {
                width: 4px;
            }
            
            .custom-scrollbar::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            
            .custom-scrollbar::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 2px;
            }
            
            .fade-enter {
                animation: fadeIn 0.5s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .modal {
                background-color: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
            }
            
            .modal-content {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }
        </style>
    </head>
    <body class="min-h-screen bg-gray-50">
        <div id="app" class="max-w-6xl mx-auto px-4 py-8">
            <!-- 主页面 -->
            <div id="home-page">
                <div class="text-center mb-12">
                    <div class="flex items-center justify-center space-x-8 mb-6">
                        <a href="https://www.aibob.click/" class="text-gray-600 hover:text-blue-600 transition-colors duration-200">主页</a>
                        <a href="https://mail.aibob.click/" class="text-gray-600 hover:text-blue-600 transition-colors duration-200">临时邮件</a>
                        <h1 class="text-4xl font-bold text-gray-800">AIBoB 临时短信接收服务</h1>
                        <div class="flex items-center space-x-6">
                            <a href="/docs" target="_blank" class="text-gray-600 hover:text-blue-600 transition-colors duration-200 flex items-center">
                                <i class="ph-code text-lg mr-1"></i>
                                API
                            </a>
                            <a href="#" onclick="showContact()" class="text-gray-600 hover:text-blue-600 transition-colors duration-200 flex items-center">
                                <i class="ph-envelope text-lg mr-1"></i>
                                联系我们
                            </a>
                        </div>
                    </div>
                    <p class="text-gray-600">选择一个临时号码来接收验证码</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="phones-container">
                    <!-- 手机卡片将在这里动态生成 -->
                </div>
            </div>

            <!-- 消息页面 -->
            <div id="messages-page" class="hidden">
                <div class="card p-4 mb-6">
                    <div class="flex items-center justify-between">
                        <button onclick="showHome()" class="flex items-center space-x-2 text-gray-600 hover:text-blue-600">
                            <i class="ph-arrow-left"></i>
                            <span>返回</span>
                        </button>
                        <h2 class="text-xl font-semibold text-gray-800" id="phone-title"></h2>
                        <button onclick="refreshMessages()" class="flex items-center space-x-2 text-blue-600 hover:text-blue-800">
                            <i class="ph-arrows-clockwise"></i>
                            <span>刷新</span>
                        </button>
                    </div>
                </div>
                
                <div id="messages-container" class="space-y-4 custom-scrollbar" style="max-height: 75vh; overflow-y: auto">
                    <!-- 消息将在这里动态生成 -->
                </div>
            </div>

            <!-- 加载动画 -->
            <div id="loading" class="hidden fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
                <div class="bg-white p-6 rounded-lg shadow-xl text-center">
                    <div class="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent mx-auto"></div>
                    <p class="text-gray-600 mt-3">加载中...</p>
                </div>
            </div>

            <!-- 联系方式弹窗 -->
            <div id="contact-modal" class="modal hidden fixed inset-0 z-50 flex items-center justify-center">
                <div class="modal-content w-full max-w-md mx-4 p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-semibold text-gray-800">联系方式</h3>
                        <button onclick="hideContact()" class="text-gray-500 hover:text-gray-700">
                            <i class="ph-x text-xl"></i>
                        </button>
                    </div>
                    <div class="space-y-4">
                        <div class="flex items-center space-x-3">
                            <i class="ph-envelope-simple text-blue-500 text-xl"></i>
                            <span class="text-gray-600">me@supage.eu.org</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
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

            function showContact() {
                document.getElementById('contact-modal').classList.remove('hidden');
            }
            
            function hideContact() {
                document.getElementById('contact-modal').classList.add('hidden');
            }

            let currentPhoneId = null;

            async function loadPhones() {
                try {
                    showLoading();
                    const response = await fetch('/api/phones');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const container = document.getElementById('phones-container');
                        container.innerHTML = data.data.map((phone, index) => `
                            <div class="card p-6 cursor-pointer fade-enter" style="animation-delay: ${index * 0.05}s"
                                 onclick="loadMessages(${phone.id})">
                                <div class="flex items-center justify-between mb-4">
                                    <span class="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm">
                                        ${phone.location}
                                    </span>
                                    <i class="ph-phone text-blue-500 text-xl"></i>
                                </div>
                                <h3 class="text-lg font-medium text-gray-800 mb-3">${phone.number}</h3>
                                <div class="flex items-center text-blue-600">
                                    <span class="text-sm">查看短信</span>
                                    <i class="ph-arrow-right ml-2"></i>
                                </div>
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
                    const response = await fetch(`/api/messages/${phoneId}?pass=114514`);
                    
                    if (response.status === 403) {
                        alert('访问被拒绝：密码错误');
                        return;
                    }
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        document.getElementById('phone-title').textContent = `${data.phone.number} (${data.phone.location})`;
                        const container = document.getElementById('messages-container');
                        container.innerHTML = data.data.map((message, index) => `
                            <div class="message-item p-4 rounded-lg fade-enter" style="animation-delay: ${index * 0.05}s">
                                <div class="flex items-center mb-2">
                                    <span class="font-medium text-gray-700">${message.sender}</span>
                                </div>
                                <p class="text-gray-600">${message.content}</p>
                            </div>
                        `).join('');
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

            // 点击模态框外部关闭
            document.getElementById('contact-modal').addEventListener('click', function(e) {
                if (e.target === this) {
                    hideContact();
                }
            });

            // 页面加载时获取手机列表
            document.addEventListener('DOMContentLoaded', loadPhones);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
