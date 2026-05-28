# 手势交互系统部署说明

## 一、文件清单

手势交互系统已创建以下文件：

```
gesture_control/
├── frontend/
│   ├── gesture_recognition.js      # 手势识别核心引擎
│   ├── gesture_actions.js          # 手势动作处理器
│   └── gesture_ui.js               # UI组件
├── config/
│   └── gesture_config.js           # 手势配置
└── docs/
    ├── gesture_design.md           # 设计文档
    └── README.md                   # 本文件
```

## 二、依赖库部署

### 2.1 html2canvas（截图功能）

**下载地址**：https://github.com/niklasvh/html2canvas/releases

**部署步骤**：
1. 下载 `html2canvas.min.js` 文件
2. 放置到 `/app/static/dist/` 目录
3. 确保文件路径为 `/app/static/dist/html2canvas.min.js`

**引入方式**：
```html
<script src="/static/dist/html2canvas.min.js"></script>
```

### 2.2 可选：MediaPipe Hands（提升识别准确率）

如果需要更高精度的手势识别，可以集成 MediaPipe Hands 库。

**下载地址**：https://github.com/google/mediapipe

**部署步骤**：
1. 下载 MediaPipe Hands 相关文件
2. 放置到 `/app/static/dist/mediapipe/` 目录
3. 修改 `gesture_recognition.js` 使用 MediaPipe API

**注意**：当前实现已采用轻量级的原生JavaScript实现，无需MediaPipe即可运行。

## 三、集成到现有系统

### 3.1 在全局模板中引入

在 `/app/templates/base.html` 或全局布局文件中添加：

```html
<!-- 手势控制系统 -->
<script src="/gesture_control/config/gesture_config.js"></script>
<script src="/gesture_control/frontend/gesture_recognition.js"></script>
<script src="/gesture_control/frontend/gesture_actions.js"></script>
<script src="/gesture_control/frontend/gesture_ui.js"></script>

<!-- html2canvas（用于截图功能） -->
<script src="/static/dist/html2canvas.min.js"></script>
```

### 3.2 在特定页面引入

如果只想在特定页面启用手势控制，在该页面的HTML模板中添加上述引用。

## 四、使用说明

### 4.1 启用手势识别

1. 打开浏览器访问cnAgentOS系统
2. 页面右下角会出现一个紫色的圆形按钮（手势开关）
3. 点击按钮，允许摄像头权限
4. 手势识别启动，按钮右上角的小圆点变为绿色

### 4.2 使用手势

| 手势 | 操作 | 说明 |
|------|------|------|
| 上划 | 返回 | 手掌向上滑动，返回上一页 |
| 下划 | 刷新 | 手掌向下滑动，刷新当前页面 |
| 张开手掌 | 快捷面板 | 五指张开，打开快捷工具面板 |
| 竖起大拇指 | 智能问数 | 竖起大拇指，跳转到智能问数页面 |
| 握拳 | 截图 | 握紧拳头，截图并保存 |

### 4.3 快捷工具面板

张开手掌后，会从右侧滑入快捷工具面板，包含：
- 手势开关状态
- 系统时间
- 最近使用的三个功能
- 清理缓存按钮

## 五、配置管理

### 5.1 修改手势灵敏度

编辑 `/gesture_control/config/gesture_config.js`：

```javascript
sensitivity: {
    swipeThreshold: 50,      // 滑动识别阈值（像素）
    holdTime: 300,           // 手势保持时间（毫秒）
    fingerThreshold: 30      // 手指识别阈值
}
```

### 5.2 启用/禁用特定手势

在配置文件中修改对应手势的 `enabled` 属性：

```javascript
gestures: {
    swipe_up: {
        enabled: true,   // true: 启用, false: 禁用
        // ...
    }
}
```

### 5.3 通过代码修改配置

```javascript
// 禁用某个手势
updateGestureEnabled('swipe_up', false);

// 启用/禁用手势识别
updateGlobalEnabled(true);
```

## 六、注意事项

1. **摄像头权限**：首次使用需要允许浏览器访问摄像头
2. **光照条件**：确保光照充足，避免逆光
3. **背景简洁**：复杂背景可能影响识别准确率
4. **性能影响**：手势识别会占用一定CPU资源，建议在需要时开启
5. **浏览器兼容**：支持现代浏览器（Chrome、Firefox、Edge、Safari）

## 七、故障排查

### 7.1 手势识别无法启动

**可能原因**：
- 浏览器不支持摄像头API
- 用户拒绝摄像头权限
- 摄像头被其他程序占用

**解决方法**：
- 检查浏览器控制台错误信息
- 在浏览器设置中允许摄像头权限
- 关闭其他使用摄像头的程序

### 7.2 手势识别不准确

**可能原因**：
- 光照不足或逆光
- 背景复杂
- 手势动作不规范

**解决方法**：
- 调整摄像头角度和光照
- 简化背景
- 调整灵敏度配置
- 规范手势动作（参考设计文档）

### 7.3 截图功能无法使用

**可能原因**：
- html2canvas库未正确引入
- 页面内容包含跨域资源

**解决方法**：
- 确认html2canvas.min.js已部署到正确路径
- 检查浏览器控制台是否有加载错误
- 配置html2canvas的CORS选项

## 八、后续开发

### 8.1 后台管理界面

将在任务块7中开发手势配置管理界面，支持：
- 可视化配置手势灵敏度
- 启用/禁用手势
- 自定义手势动作映射

### 8.2 手势识别优化

可选集成MediaPipe Hands库，提升识别准确率：
- 支持更复杂的手势
- 提供手部关键点检测
- 提升识别鲁棒性

## 九、技术支持

如有问题，请参考：
- 设计文档：`/gesture_control/docs/gesture_design.md`
- 项目README：`/README.md`
- 需求文档：`/requirements.md`
