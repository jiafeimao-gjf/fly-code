# fly-code 代码审查与待办事项

## 代码审查摘要

| 类别 | 数量 | 状态 |
|------|------|------|
| 严重 Bug | 2 | ✅ 全部修复 |
| 代码异味 | 6 | ✅ 4已修复，2待处理 |
| 设计缺陷 | 5 | 待处理 |
| 功能缺失 | 8 | P2部分完成 |

---

## 严重 Bug ✅ 全部修复

1. `repl.py` 缩进错误 - 方法嵌套错误
2. Ollama 模型选择 - 自动选择、手动切换、tools失败重试

---

## 代码异味

### 已修复
- `cli/main.py` - 未使用的 DocReader 导入
- `core/ai_client.py` - 未使用的 json 导入
- `core/deployer.py` - 未使用的 sys 导入
- `core/planner.py` - 未使用的 logger 导入
- `repl.py` - 未使用的 self.current_spec 变量
- `deployer.py` - 格式化字符串错误 `{{{{.Status}}}}`

### 待处理
- 未使用的变量: `cli/main.py:83-84` 的 `spec_path` 创建后未检查 exists()

---

## 设计缺陷 (P3)

1. 核心功能为空实现 - `planner.py` 使用硬编码模板
2. 代码生成过于简单 - `develop` 命令只生成占位符
3. `analyzer.py` 检测规则有限
4. Spec 更新机制不完整
5. Deployer 缺乏配置管理 (fly-code.yaml)

---

## 功能开发进度

### P0 ✅ 已完成
- 修复 repl.py 缩进错误
- 修复 deployer.py 格式化字符串
- Ollama 模型选择优化

### P1 ✅ Agent 模式已完成
- `/agent` - 交互式 Agent 模式，实时显示执行过程
- `/code` - AI 生成代码（使用 agent.run 支持文件创建）
- `/fix` - AI 修复 bug（使用 agent.run 支持文件编辑）
- `/review` - AI 代码审查
- `/explain` - AI 代码解释
- Agent 模式内支持 `/model`, `/models`, `/debug`, `/verbose` 命令

### P2 ✅ 功能增强已完成
| 功能 | 状态 | 实现 |
|------|------|------|
| AI生成实际代码 | ✅ | `/code`和`/fix`使用`agent.run()`，AI可调用工具创建/编辑文件 |
| 命令历史持久化 | ✅ | readline实现，`~/.fly-code/history`，上下键浏览 |
| Git集成 | ✅ | `git_tool.py`，支持`/git status\|log\|add\|commit\|branch\|checkout\|push\|pull` |
| 流式AI响应 | ✅ | `chat_stream()` + `/stream` 切换，支持逐字输出 |

### P3 📋 长期改进
- 配置文件支持 (fly-code.yaml)
- 扩展 Analyzer 检测规则
- 日志文件功能
- 动态实现计划生成
- Spec 验证逻辑完善
- Tester 测试代码修复

---

## 已完成命令

### 项目命令
- `/init <name>` - 初始化项目
- `/spec create` - 创建规格文档
- `/plan [spec]` - 生成实施计划
- `/develop [spec]` - 从规格开发代码
- `/test [file]` - 运行测试
- `/analyze [target]` - 分析代码
- `/deploy [target]` - 部署
- `/status` - 查看状态

### Agent 模式
- `/agent` - 启动 Agent 模式
- `/code <描述>` - AI 生成代码
- `/fix <bug>` - AI 修复 bug
- `/explain <code>` - AI 解释代码
- `/review [file]` - AI 代码审查
- `/model <name>` - Agent 模式内切换模型
- `/models` - Agent 模式内列出模型
- `/debug` - 切换 debug 模式（更多日志，50次迭代）
- `/verbose` - 切换 verbose 模式

### AI 模型
- `/models` - 列出可用模型
- `/model <name>` - 切换模型
- `/tools` - 列出可用工具

### Git
- `/git status` - 查看状态
- `/git log` - 查看提交历史
- `/git add [files]` - 暂存文件
- `/git commit <msg>` - 提交
- `/git checkout <branch>` - 切换分支
- `/git push [remote]` - 推送
- `/git pull [remote]` - 拉取

### 其他
- `/help` - 显示帮助
- `/exit` - 退出
