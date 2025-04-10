# 珊瑚卫士——基于YOLO与降噪模型的南海珊瑚礁白化智能识别平台

## 目录
- [项目简介](#项目简介)
- [环境要求](#环境要求)
- [快速启动](#快速启动)
  - [1. 项目下载](#1-项目下载)
  - [2. 安装依赖](#2-安装依赖)
  - [3. 数据库配置](#3-数据库配置)
  - [4. 初始化项目](#4-初始化项目)
  - [5. 启动服务](#5-启动服务)
- [系统功能指南](#系统功能指南)
  - [前台功能](#前台功能)
  - [后台管理](#后台管理)
- [高级配置](#高级配置)
- [常见问题](#常见问题)



## 项目简介
本系统是面向南海珊瑚礁保护的智能化监测平台，集成以下核心功能：
- 🛰️ **多源数据融合**：整合遥感SST、DHW、Hotspot数据和实地监测数据
- 🧠 **AI智能识别**：基于YOLO多模型的珊瑚白化实时检测
- 📊 **多维可视化**：动态热力图、趋势分析图、时序分析图、热力图、风险评估仪表盘
- 📑 **自动化报告**：一键生成PDF/Excel格式分析报告
- 🔒 **权限管理系统**：细粒度RBAC权限控制

技术栈：`Django 5.1` + `MySQL 8.0` + `PyTorch 2.5` + `ECharts 5`

---

## 环境要求
| 组件              | 最低配置                          | 推荐配置                          |
|-------------------|----------------------------------|----------------------------------|
| 操作系统          | Windows 10 / Ubuntu 20.04       | Windows 11 / Ubuntu 22.04       |
| Python            | 3.10+                           | 3.12.3                          |
| 内存              | 8GB RAM                         | 16GB RAM                        |
| 存储空间          | 50GB可用空间                    | 100GB SSD                       |

---

## 快速启动

### 1. 下载项目
根基提供的网盘链接下载即可。

### 2. 安装依赖
```bash
# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
# 安装核心依赖
pip install -r requirements.txt
# 安装GPU支持（若需加速推理）
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
```

### 3. 数据库配置
1. 使用Navicat或MySQL客户端创建数据库：
   ```sql
   CREATE DATABASE coral_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. 修改数据库配置 `djangoProject/settings.py`：
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'coral_db',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

### 4. 初始化项目
```bash
# 数据库迁移
python manage.py makemigrations
python manage.py migrate
# 创建超级管理员
python manage.py createsuperuser
```

### 5. 启动服务
```bash
python manage.py runserver 
```
访问地址：
- 前台首页：http://127.0.0.1:8000/
- 后台管理：http://127.0.0.1:8000/admin

---

## 系统功能指南

### 前台功能
#### 1. 信息浏览

- **珊瑚知识科普**：提供珊瑚相关白化知识科普、相关专业名词解释
- **影响珊瑚白化现象的因素**：认识珊瑚生态环境的重要性、影响因素、厄尔尼诺现象等等
- **保护指南**：实时与保护建议

#### 2. 数据可视化
- **海温趋势分析**：支持多区域对比、时间范围筛选
- **年度海温数据可视化**：支持定向查询某地点海温数据及变化趋势
- **南海热力图**：缩放查看南海内相关区域热压力分布
- **珊瑚健康评估系统**：根据特有计算方式与核心指标、评定珊瑚白化风险等级、相关措施与保护建议

#### 3. 白化检测
1. 进入"珊瑚检测"页面
2. 上传珊瑚礁图像（支持JPG/PNG格式）
3. 选择检测模型（YOLOv5/YOLOv8）
4. 查看检测结果与置信度

#### 4. 报告生成
- 在仪表盘页面点击"导出报告"
- 选择格式（PDF/Excel）和时间范围
- 下载包含风险评估的详细报告

---

### 后台管理
#### 1. 数据管理
- **位置管理**：  
  `/admin/coral_app/location/`：管理珊瑚礁区域坐标、增删改查
- **海洋数据管理**：  
  `/admin/coral_app/marinedata/`：支持CSV批量导入/导出、增删改查

#### 2. 用户权限
- **用户组管理**：创建"研究员"、"管理员"等角色
- **权限分配**：精确到字段级的读写控制
- **操作审计**：查看所有敏感操作日志

#### 3. 系统监控
- 实时服务器状态
- API调用统计
- 模型推理性能监控
---

## 高级配置
### GPU加速推理
1. 安装CUDA 11.8工具包
2. 修改`coral_app/views.py`中模型加载代码：
   ```python
   model = torch.hub.load('ultralytics/yolov5', 'custom', 
                         path='models/yolov8n.pt',
                         device='cuda:0')
   ```

### HTTPS部署
1. 生成SSL证书：
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   ```
2. 修改启动命令：
   ```bash
   python manage.py runsslserver 0.0.0.0:443 --cert cert.pem --key key.pem
   ```

---

## 常见问题
**Q1: 数据库连接失败**  
✅ 检查MySQL服务是否启动  
✅ 验证`settings.py`中的用户名/密码  
✅ 确保数据库字符集为`utf8mb4`

**Q2: 模型加载缓慢**  
✅ 确认已安装CUDA和cuDNN  
✅ 使用`nvidia-smi`检查GPU占用  
✅ 尝试减小批量大小（batch_size）

**Q3: 热力图不显示**  
✅ 检查ECharts版本是否为5.0+  
✅ 确保`location_id__lat/lon`字段有有效值  
✅ 查看浏览器控制台错误日志

---

---
© 2025 珊瑚卫士——基于YOLO与降噪模型的南海珊瑚礁白化智能识别平台

---

> 提示：运行前请确保：  
> 1. MySQL服务已启动（默认端口3306）  
> 2. Python环境为3.10+  
> 3. 至少预留5GB磁盘空间用于模型存储