# 手势交互系统设计文档

## 一、系统概述

手势交互系统是cnAgentOS的独立功能模块，通过摄像头识别用户手势，提供快捷操作入口。系统采用无侵入式设计，不影响原有功能。

## 二、系统架构

### 2.1 目录结构

```
gesture_control/
├── frontend/                      # 前端实现
│   ├── gesture_recognition.js      # 手势识别核心引擎
│   ├── gesture_actions.js          # 手势动作处理器
│   └── gesture_ui.js               # UI组件（开关按钮、状态指示器）
├── config/                         # 配置文件
│   └── gesture_config.js           # 手势配置与映射关系
└── docs/                           # 文档
    └── gesture_design.md           # 设计文档（本文件）
```

### 2.2 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                   用户界面层                             │
│         GestureUI（开关按钮、状态指示器）                │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ 用户交互
┌─────────────────────────────────────────────────────────┐
│                   手势识别层                             │
│   GestureRecognition（摄像头、图像处理、手势检测）       │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ 手势事件
┌─────────────────────────────────────────────────────────┐
│                   动作处理层                             │
│   GestureActionHandler（执行系统动作）                   │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ 配置读取
┌─────────────────────────────────────────────────────────┐
│                   配置管理层                             │
│   GestureConfig（手势映射、灵敏度设置）                  │
└─────────────────────────────────────────────────────────┘
```

## 三、核心组件说明

### 3.1 GestureRecognition（手势识别引擎）

**功能**：
- 摄像头视频流获取
- 肤肤色彩检测
- 手部区域识别
- 手势分类（上划、下划、张开手掌、竖起大拇指、握拳）

**技术实现**：
- 使用 `navigator.mediaDevices.getUserMedia` 获取摄像头视频流
- 基于 RGB 肤肤色彩检测算法识别手部
- 通过手部区域的长宽比、面积等特征判断手势类型
- 通过位置历史记录检测滑动方向

**手势识别算法**：

1. **上划/下划检测**：
   - 记录手部中心点位置历史（最近10帧）
   - 计算垂直方向位移（deltaY）
   - 如果 |deltaY| > 阈值 且 |deltaY| > |deltaX|，则判定为滑动
   - deltaY < 0 为上划，deltaY > 0 为下划

2. **张开手掌检测**：
   - 计算手部区域的长宽比（aspectRatio = width / height）
   - 如果 0.8 < aspectRatio < 1.2 且面积 > 10000，则判定为张开手掌

3. **竖起大拇指检测**：
   - 如果 aspectRatio < 0.6 且 height > width * 1.5，则判定为竖起大拇指

4. **握拳检测**：
   - 如果面积 < 5000 且 0.7 < aspectRatio < 1.3，则判定为握拳

### 3.2 GestureActionHandler（动作处理器）

**功能**：
- 执行手势对应的系统动作
- 管理最近使用功能列表
- 提供快捷工具面板

**支持的动作**：

| 手势 | 动作 | 说明 |
|------|------|------|
| 上划 | navigateBack | 返回上一页或关闭当前弹窗 |
| 下划 | refreshCurrentPage | 刷新当前页面数据 |
| 张开手掌 | openQuickPanel | 打开全局快捷工具面板 |
| 竖起大拇指 | navigateToChat | 跳转到智能问数页面 |
| 握拳 | takeScreenshot | 截图并保存到本地 |

### 3.3 GestureUI（UI组件）

**功能**：
- 提供全局手势开关按钮（悬浮按钮）
- 显示手势识别状态指示器
- 提供手势提示通知

**UI设计**：
- 开关按钮：圆形悬浮按钮，位于页面右下角
- 状态指示器：小圆点，绿色表示启用，红色表示禁用
- 手势提示：屏幕中央显示识别到的手势名称

### 3.4 GestureConfig（配置管理）

**功能**：
- 定义手势与动作的映射关系
- 管理手势灵敏度设置
- 提供配置持久化（localStorage）

**配置结构**：
```javascript
{
    enabled: false,                    // 全局开关
    gestures: {
        swipe_up: {
            name: '上划',
            description: '全局返回/退出当前子页面',
            enabled: true,
            action: 'navigateBack',
            sensitivity: { threshold: 50, holdTime: 300 }
        },
        // ... 其他手势配置
    },
    globalSettings: {
        defaultEnabled: false,
        showIndicator: true,
        indicatorPosition: 'bottom-right',
        cameraFacing: 'user',
        recognitionInterval: 100
    }
}
```

## 四、使用方法

### 4.1 引入手势控制模块

在需要启用手势控制的页面中，引入以下JS文件：

```html
<!-- 手势配置 -->
<script src="/gesture_control/config/gesture_config.js"></script>

<!-- 手势识别核心 -->
<script src="/gesture_control/frontend/gesture_recognition.js"></script>

<!-- 手势动作处理 -->
<script src="/gesture_control/frontend/gesture_actions.js"></script>

<!-- 手势UI组件 -->
<script src="/gesture_control/frontend/gesture_ui.js"></script>

<!-- html2canvas库（用于截图功能） -->
<script src="/app/static/dist/html2canvas.min.js"></script>
```

### 4.2 启用手势识别

1. 点击页面右下角的手势开关按钮
2. 允许浏览器访问摄像头
3. 手势识别自动启动

### 4.3 使用手势

- **上划**：手掌向上滑动 → 返回上一页
- **下划**：手掌向下滑动 → 刷新当前页面
- **张开手掌**：五指张开 → 打开快捷工具面板
- **竖起大拇指**：竖起大拇指 → 跳转到智能问数
- **握拳**：握紧拳头 → 截图保存

## 五、性能优化

### 5.1 默认关闭
手势识别默认关闭，用户需手动开启，避免影响页面性能。

### 5.2 轻量级实现
- 使用原生的Canvas API进行图像处理
- 不依赖外部手势识别库（如MediaPipe）
- 识别算法简单高效，CPU占用低

### 5.3 帧率控制
- 使用 `requestAnimationFrame` 控制识别帧率
- 识别间隔可配置（默认100ms）

## 六、安全与隐私

### 6.1 摄像头权限
- 需要用户明确授权才能访问摄像头
- 摄像头视频流仅在本地处理，不上传服务器

### 6.2 数据存储
- 手势配置存储在 localStorage
- 最近使用功能列表仅保存在内存中
- 截图文件保存在本地，不上传服务器

## 七、扩展性

### 7.1 新增手势
在 `gesture_recognition.js` 的 `analyzeHandGesture` 方法中添加新的手势识别逻辑。

### 7.2 新增动作
在 `gesture_actions.js` 的 `executeAction` 方法中添加新的动作处理逻辑。

### 7.3 自定义配置
通过修改 `gesture_config.js` 或在后台管理界面调整手势灵敏度、启用/禁用手势。

## 八、兼容性

- **浏览器**：支持现代浏览器（Chrome、Firefox、Edge、Safari）
- **设备**：支持带有摄像头的PC、平板、手机
- **系统**：跨平台（Windows、macOS、Linux、iOS、Android）

## 九、已知限制

1. 手势识别准确率受光照条件影响
2. 复杂背景下可能误识别
3. 需要摄像头权限，部分环境可能受限
4. 截图功能依赖html2canvas库，需额外引入

## 十、后续优化方向

1. 集成MediaPipe Hands提升识别准确率
2. 支持自定义手势训练
3. 添加手势教程和演示
4. 优化手势识别算法，提升鲁棒性
5. 支持多手势组合操作
