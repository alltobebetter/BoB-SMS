from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import cloudscraper
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，实际使用时建议设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_messages():
    scraper = cloudscraper.create_scraper(delay=10)
    url = 'https://yunduanxin.net/info/46726416679/'
    
    try:
        response = scraper.get(url)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        message_rows = soup.find_all('div', class_='row border-bottom table-hover')
        
        messages = []
        for row in message_rows[:5]:
            sender = row.find('div', class_='mobile_hide').text.strip()
            time_div = row.find_all('div', class_='col-xs-0 col-md-2')
            time_str = time_div[0].text.strip() if time_div else "未知时间"
            content = row.find('div', class_='col-xs-12 col-md-8').text.strip()
            
            message = {
                'sender': sender,
                'time': time_str,
                'content': content
            }
            messages.append(message)
            
        return messages
    except Exception as e:
        print(f'Error: {e}')
        return None

@app.get("/api/messages")
async def read_messages():
    messages = get_messages()
    if messages:
        return {"status": "success", "data": messages}
    return {"status": "error", "message": "Failed to fetch messages"}

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>短信查看器</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .message-card {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .message-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                color: #666;
            }
            .message-content {
                color: #333;
            }
            .refresh-button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-bottom: 20px;
            }
            .refresh-button:hover {
                background-color: #45a049;
            }
            .loading {
                text-align: center;
                color: #666;
            }
        </style>
    </head>
    <body>
        <h1>最新短信消息</h1>
        <button class="refresh-button" onclick="fetchMessages()">刷新消息</button>
        <div id="messages-container"></div>

        <script>
            function fetchMessages() {
                const container = document.getElementById('messages-container');
                container.innerHTML = '<div class="loading">加载中...</div>';
                
                fetch('/api/messages')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            container.innerHTML = data.data.map(message => `
                                <div class="message-card">
                                    <div class="message-header">
                                        <span>发送者: ${message.sender}</span>
                                        <span>${message.time}</span>
                                    </div>
                                    <div class="message-content">
                                        ${message.content}
                                    </div>
                                </div>
                            `).join('');
                        } else {
                            container.innerHTML = '<div class="error">获取消息失败</div>';
                        }
                    })
                    .catch(error => {
                        container.innerHTML = '<div class="error">获取消息失败</div>';
                        console.error('Error:', error);
                    });
            }

            // 页面加载时自动获取消息
            document.addEventListener('DOMContentLoaded', fetchMessages);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
