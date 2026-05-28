# 数据库修改说明

## 概述
这些修改修复了数字员工对话功能和数据库结构问题。主要包括以下内容：

## 修改内容

### 1. 代码修改（已提交到Git仓库）
- **app.py**: 
  - 端口配置改为10086
  - 添加了crawl4ai环境变量配置
- **app/models/db.py**:
  - 修复了`digital_employee`表缺少`sort_order`字段的问题
  - 添加了ALTER TABLE语句确保现有表也有该字段

### 2. 数据库修改（未提交，包含在此脚本中）
由于数据库文件包含敏感信息（API密钥），这些修改需要手动应用：

#### 已应用的数据库修改：
1. **添加了sort_order字段**到`digital_employee`表
2. **创建了DeepSeek Chat API接口**（ID: 3）
3. **更新了川小农数字员工配置**，关联到模型ID 1和API接口ID 3
4. **创建了DeepSeek模型服务记录**（需要填入自己的API密钥）

## 如何应用这些修改

### 步骤1：拉取最新的代码
```bash
git pull origin main
```

### 步骤2：运行数据库修改脚本
```bash
# 确保数据库文件存在
# 如果不存在，系统会在首次运行时自动创建

# 运行修改脚本
sqlite3 database/app.db < setup_database_changes.sql
```

### 步骤3：添加自己的API密钥
编辑数据库中的模型服务记录，填入自己的API密钥：
```sql
-- 查看当前模型服务
SELECT * FROM model_service;

-- 更新API密钥（将YOUR_API_KEY_HERE替换为实际密钥）
UPDATE model_service 
SET api_key = 'sk-your-actual-api-key-here' 
WHERE name = 'deepseek-v3.2';
```

### 步骤4：验证修改
运行验证脚本检查所有修改是否成功应用：
```bash
sqlite3 database/app.db "
-- 检查digital_employee表结构
SELECT '表结构检查:' as check_item;
SELECT sql FROM sqlite_master WHERE type='table' AND name='digital_employee';

-- 检查川小农配置
SELECT '川小农配置检查:' as check_item;
SELECT id, name, alias, model_id, api_interface_id FROM digital_employee WHERE alias = '川小农';

-- 检查API接口
SELECT 'API接口检查:' as check_item;
SELECT id, name, url, method FROM api_interface WHERE name LIKE '%DeepSeek%';

-- 检查模型服务
SELECT '模型服务检查:' as check_item;
SELECT id, name, model, base_url FROM model_service WHERE name = 'deepseek-v3.2';
"
```

## 重要提醒

### ⚠️ 安全注意事项
1. **不要提交包含API密钥的数据库文件**到Git仓库
2. **数据库文件包含敏感信息**，应在本地环境中保密
3. 每个开发者应该使用自己的API密钥

### 🔧 功能说明
这些修改解决了以下问题：
- 数字员工（川小农）无法对话的问题
- 数据库表结构不完整的问题
- 端口配置问题（现在使用10086端口）

### 🚀 验证功能
修改完成后，可以：
1. 启动服务器：`python app.py`
2. 访问聊天页面：`http://localhost:10086/chat`
3. 测试与川小农的对话功能

## 故障排除

### 如果遇到问题：
1. **数据库错误**: 确保已运行`setup_database_changes.sql`脚本
2. **端口占用**: 检查10086端口是否被占用
3. **API调用失败**: 确认已正确配置API密钥
4. **缺少依赖**: 运行`pip install crawl4ai redis`

## 联系信息
如果有问题，请联系代码修改者：wangjiaxin

---
*最后更新: 2026-05-28*