# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指导。

## 项目概述

**fly-code** 是一个文档驱动的编程智能体 CLI。使用 Python 开发，支持方案设计、代码开发、测试、问题分析和部署的自动化。

### 核心原则：文档优先开发

所有工作都从文档开始：
- **新功能/任务**: 先写 SPEC.md，再实现
- **迭代**: 先迭代文档，再修改代码
- **Bug 修复**: 先记录问题和解决方案，再编写代码

## 项目结构

```
fly-code/
├── cli/                    # CLI 入口和命令处理
│   ├── __init__.py
│   ├── main.py            # argparse CLI 接口
│   └── repl.py            # 交互式 REPL，支持斜杠命令
├── core/                   # Agent 核心逻辑
│   ├── __init__.py
│   ├── agent.py           # Agent 编排器（tools + model）
│   ├── planner.py         # 方案设计和规划
│   ├── developer.py       # 代码生成和修改
│   ├── tester.py          # 测试生成和执行
│   ├── analyzer.py        # 代码问题分析
│   ├── deployer.py        # 部署自动化
│   ├── tools/             # 工具封装
│   │   ├── base.py        # BaseTool 基类
│   │   ├── file_tool.py   # 文件读写
│   │   ├── edit_tool.py   # 文件编辑（diff）
│   │   ├── bash_tool.py   # 命令执行
│   │   ├── glob_tool.py   # 文件搜索
│   │   └── grep_tool.py   # 内容搜索
│   ├── models/            # AI 模型封装
│   │   ├── base.py        # AIModel 基类
│   │   ├── ollama_model.py
│   │   └── minimax_model.py
│   └── ai_client.py       # AI 客户端（向后兼容）
├── docs/                   # 文档驱动工作流
│   ├── __init__.py
│   ├── spec_manager.py    # SPEC.md 创建和迭代
│   └── reader.py          # 文档解析和验证
├── utils/                  # 共享工具
│   ├── __init__.py
│   └── logger.py
├── tests/
└── README.md
```

## 核心架构

### Agent 执行流程

```
用户输入
    │
    ▼
┌─────────────────────────────────┐
│          Agent.run()            │
│  - system_prompt (工具使用说明)  │
│  - user_input (用户需求)        │
│  - project_context (SPEC.md)    │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│     AI 模型 (Ollama/MiniMax)    │
│  - 模型通过 JSON 输出工具调用    │
│  - Agent 解析并执行工具         │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│        工具执行 (Tool Result)     │
│  - file_operations (文件)      │
│  - edit_file (编辑)            │
│  - bash (命令)                 │
│  - glob / grep (搜索)          │
└─────────────────────────────────┘
    │
    ▼
  结果返回给 AI → 最终响应
```

### Agent 执行输出示例

```
────────────────────────────────────────────────────
  Agent 开始处理
────────────────────────────────────────────────────

22:30:01 [INFO] [1/10] 正在思考...
22:30:01 [DEBUG] Raw response: {"tool": "file_operations", ...}
22:30:01 [INFO] [工具调用 #1] file_operations
22:30:01 [SUCCESS] 结果: Created hello.py
22:30:02 [INFO] [2/10] 正在思考...

────────────────────────────────────────────────────
  Agent 完成
────────────────────────────────────────────────────
```

**Debug/Verbose 模式** (`/debug` 或 `/verbose`):
- logger 级别设为 DEBUG，显示所有调试信息
- max_iterations 从 10 增至 50
- 显示原始 AI 响应、完整工具参数等

## 工具 (Tools)

| 工具 | 功能 | 参数 |
|------|------|------|
| `file_operations` | 文件读写、目录创建 | `operation`: file_read/file_write/directory_create, `path`, `content` |
| `edit_file` | 文件编辑 | `operation`: replace/insert_after/insert_before/delete, `path`, `old_content`, `new_content` |
| `bash` | 执行 Shell 命令 | `command`, `cwd`, `timeout` |
| `glob` | 按模式搜索文件 | `pattern`, `cwd`, `max_results` |
| `grep` | 正则搜索文件内容 | `pattern`, `path`, `file_pattern`, `context` |
| `git` | Git 版本控制 | `operation`: status/log/add/commit/branch/checkout/push/pull |

## AI 模型 (Models)

### Ollama (本地)

- 自动选择第一个可用模型
- 支持手动切换到指定模型
- 通过 System Prompt 指令模型输出 JSON 格式工具调用

```bash
> /models              # 列出所有可用模型
> /model qwen3.5:35B  # 切换到指定模型
```

### MiniMax (云端)

- 需要设置 `MINIMAX_API_KEY` 环境变量
- 与 Ollama 使用相同的工具调用机制

## CLI 命令

```bash
fly-code init <project_name>     # 初始化新项目
fly-code interactive             # 启动交互式 REPL
fly-code spec create <title>     # 创建规格文档
fly-code plan [spec_file]        # 规划方案
fly-code develop [spec_file]     # 生成代码
fly-code test [test_file]        # 运行测试
fly-code analyze [target]        # 分析代码
fly-code deploy [target]         # 部署
```

## REPL 斜杠命令

### 项目命令
```bash
/init <name>              # 初始化项目
/spec create <title>...   # 创建规格
/plan [spec_file]         # 规划
/test [file]              # 测试
/analyze [target]         # 分析
/deploy [target]          # 部署
/status                   # 状态
```

### Agent 模式
```bash
/agent                    # 启动 Agent 模式（AI 自动使用工具）
/code <描述>             # 生成代码
/fix <bug>               # 修复 bug
/explain <code>          # 解释代码
/review [file]           # AI 代码审查
/model <name>            # 切换 AI 模型（Agent 模式内也可用）
/models                  # 列出可用模型（Agent 模式内也可用）
/debug                   # 切换 debug 模式（更多日志，50次迭代）
/verbose                 # 切换 verbose 模式
```

### Git 命令
```bash
/git status               # 查看状态
/git log                  # 查看提交历史
/git add [files]         # 暂存文件
/git commit <msg>        # 提交更改
/git checkout <branch>   # 切换分支
/git push [remote]       # 推送到远程
/git pull [remote]       # 从远程拉取
```

### AI 模型
```bash
/model [name]            # 查看/切换 AI 模型
/models                  # 列出可用模型
/tools                   # 列出可用工具
```

### 输出控制
```bash
/stream                  # 切换流式输出（逐字显示AI响应）
/debug                   # 切换 debug 模式（更多日志）
/verbose                 # 切换 verbose 模式
```

### 通用
```bash
/help                     # 显示帮助
/exit                    # 退出
```

## 开发

```bash
# 安装依赖
pip install -e .

# 运行测试
pytest tests/

# 环境变量
export MINIMAX_API_KEY="your_key"    # 可选
```

## 工作流示例

### Agent 模式（推荐）

```bash
fly-code interactive
> /agent
agent> 创建一个用户认证模块，包含登录和注册功能
agent> /done
```

### CLI 模式

```bash
fly-code spec create "用户认证"
fly-code plan
fly-code develop
fly-code test
fly-code analyze
```
