# 高校宿舍报修管理系统

## 项目介绍
这是一个基于Vue.js 3 + Flask技术栈的前后端分离高校宿舍报修管理系统，不依赖Node.js，使用CDN引入前端依赖。

## 技术栈
- **前端**：Vue.js 3 + Vue Router + Pinia + Element Plus + Axios
- **后端**：Python Flask + SQLAlchemy + Flask-JWT-Extended
- **数据库**：SQLite (开发环境) / MySQL (生产环境)
- **交互模式**：RESTful API

## 项目结构
```
├── frontend/          # 前端代码
│   └── index.html     # 主页面，CDN引入所有依赖
├── backend/           # 后端代码
│   ├── app.py         # Flask应用主文件
│   ├── requirements.txt  # Python依赖
│   ├── start.bat      # Windows启动脚本
│   └── uploads/       # 图片上传目录
└── README.md          # 项目说明文档
```

## 功能模块

### 1. 公共模块
- 登录/注册
- 个人中心
- 公告查看

### 2. 学生端功能
- 在线报修（支持图片上传、预约时间）
- 我的报修单（进度追踪）
- 维修评价

### 3. 维修人员端功能
- 任务大厅/派单中心
- 维修处理（状态更新、异常上报）
- 历史记录

### 4. 管理员端功能
- 报修管理（审核与派单）
- 用户管理（学生、维修人员）
- 基础数据维护
- 公告管理
- 数据可视化看板
- 报表导出

## 安装与运行

### 前置条件
1. 安装 Python 3.7+
2. 安装 pip
3. 安装浏览器（推荐 Chrome、Firefox）

### 后端安装与运行
1. 进入 backend 目录
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行后端服务：
   - Windows: 双击 `start.bat` 或在命令行执行 `python app.py`
   - Linux/Mac: 执行 `python3 app.py`

### 前端运行
直接用浏览器打开 `frontend/index.html` 文件即可

## 数据库配置

### 开发环境（默认）
使用 SQLite 数据库，无需额外配置，系统会自动创建 `dorm_repair.db` 文件。

### 生产环境（MySQL）
修改 `backend/app.py` 中的数据库配置：
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/dorm_repair'
```

## 初始账号
系统会自动创建一个默认管理员账号：
- 账号：`admin`
- 密码：`admin123`

## API 接口

### 认证相关
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/change-password` - 修改密码

### 报修相关
- `POST /api/repairs` - 创建报修单
- `GET /api/repairs` - 获取报修单列表

## 注意事项
1. 前端使用 CDN 引入依赖，需要网络连接
2. 图片上传功能在开发环境下使用本地存储，生产环境建议使用云存储
3. JWT 密钥在生产环境中需要修改为强密钥
4. 定期备份数据库文件

## 毕设亮点
1. 完整的角色权限管理
2. 响应式设计，支持移动端
3. 图片上传与预览功能
4. 数据可视化看板（使用 ECharts）
5. Excel 报表导出功能
6. RESTful API 设计规范

## 项目扩展
1. 添加短信通知功能
2. 实现维修人员定位与导航
3. 增加智能故障诊断功能
4. 对接学校统一认证系统
5. 实现微信小程序端

## 联系方式
如有问题或建议，请联系项目负责人。