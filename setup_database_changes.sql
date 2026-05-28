-- 数据库修改恢复脚本
-- 这个脚本包含了wangjiaxin所做的数据库修改
-- 请在新的环境中运行此脚本以应用相同的数据库结构修改
-- 注意：不包含敏感信息如API密钥

-- 1. 修复digital_employee表，添加sort_order字段
-- 如果表已存在，添加sort_order字段（如果不存在）
ALTER TABLE digital_employee ADD COLUMN sort_order INTEGER DEFAULT 0;

-- 2. 创建DeepSeek Chat API接口记录（同伴需要填入自己的API密钥）
INSERT INTO api_interface (name, url, method, response_format, example, qps_limit, token_required, remark, enabled)
VALUES (
    'DeepSeek Chat API',
    'https://aigc-api.aitoolcore.com/api/v1/chat/completions',
    'POST',
    'JSON',
    'https://aigc-api.aitoolcore.com/api/v1/chat/completions',
    '按模型服务配额',
    1,
    'DeepSeek大模型对话接口，支持deepseek-v3.2等模型',
    1
);

-- 3. 更新川小农数字员工配置，关联到正确的模型和API接口
-- 假设模型ID为1（DeepSeek模型），API接口ID为3（上一步创建的）
UPDATE digital_employee 
SET model_id = 1, api_interface_id = 3 
WHERE alias = '川小农' AND name = '川小农';

-- 4. 创建模型服务记录（同伴需要填入自己的API密钥）
-- 注意：这里不包含实际的API密钥，同伴需要自己添加
INSERT INTO model_service (name, model, api_key, base_url, max_tokens, temperature, is_default, token_usage)
VALUES (
    'deepseek-v3.2',
    'deepseek-v3.2',
    'YOUR_API_KEY_HERE', -- 同伴需要填入自己的API密钥
    'https://aigc-api.aitoolcore.com/api/v1/chat/completions',
    4096,
    0.7,
    0,
    0
);

-- 5. 检查修改结果
SELECT '=== 修改结果检查 ===' as check_result;

SELECT 'digital_employee表结构检查' as table_check;
SELECT sql FROM sqlite_master WHERE type='table' AND name='digital_employee';

SELECT '川小农配置检查' as employee_check;
SELECT id, name, alias, model_id, api_interface_id FROM digital_employee WHERE alias = '川小农';

SELECT 'API接口检查' as api_check;
SELECT id, name, url, method FROM api_interface WHERE name LIKE '%DeepSeek%';

SELECT '模型服务检查' as model_check;
SELECT id, name, model, base_url FROM model_service WHERE name = 'deepseek-v3.2';