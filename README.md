# fly-code

文档驱动的编程智能体 CLI

## 理念

**文档优先**: 每个任务都从 SPEC.md 开始——先设计，后实现。

## 特性

- **Agent 模式**: AI 自动使用工具执行任务，实时显示执行过程
- **文档驱动开发**: 先写 SPEC.md，再写代码
- **AI 辅助工作流**: 集成 Ollama（本地）和 MiniMax（云端）
- **交互式 REPL**: 斜杠命令实现快速开发
- **完整工具链**: 规划，开发、测试，分析、部署

## 快速开始

```bash
# 安装
pip install -e .

# 启动交互式 REPL
fly-code interactive

# Agent 模式（推荐）
> /agent
agent> 创建一个计算器模块
agent> /done
```

## Agent 执行示例

```
────────────────────────────────────────────────────
  Agent 开始处理
────────────────────────────────────────────────────

22:30:01 [INFO] [1/10] 正在思考...
22:30:01 [INFO] [工具调用 #1] file_operations
22:30:01 [SUCCESS] 结果: Created directory tank-battle
22:30:02 [INFO] [2/10] 正在思考...
22:30:02 [INFO] [工具调用 #2] file_operations
22:30:02 [SUCCESS] 结果: Created tank-battle/index.html
...

────────────────────────────────────────────────────
  Agent 完成
────────────────────────────────────────────────────
```

## 核心命令

```bash
# REPL 模式
fly-code interactive

# 项目命令
> /init <name>              # 初始化项目
> /spec create <title>...   # 创建规格文档
> /plan                      # 从规格生成计划
> /test [file]              # 运行测试
> /analyze [target]         # 分析代码
> /deploy [target]          # 部署

# Agent 模式
> /agent                     # 启动 Agent 模式（AI自动使用工具）
> /code <描述>              # 生成代码
> /fix <bug>                # 修复 bug
> /explain <code>           # 解释代码
> /review [file]            # AI代码审查
> /model <name>             # 切换 AI 模型
> /debug                     # 开启 debug 模式（更多日志，50次迭代）
> /verbose                   # 开启 verbose 模式

# Git 命令
> /git status               # 查看状态
> /git log                  # 查看提交历史
> /git add [files]         # 暂存文件
> /git commit <msg>        # 提交更改
> /git checkout <branch>   # 切换分支

# AI 模型
> /models                    # 列出可用模型
> /model qwen3.5:35B       # 切换模型
> /tools                     # 列出可用工具

# 通用
> /help                      # 显示帮助
> /exit                      # 退出
```

## AI 模型

**Ollama (本地)**
- 自动选择可用模型
- `/models` 查看所有模型
- `/model <name>` 切换模型

**MiniMax (云端)**
- 需要设置 `MINIMAX_API_KEY`

## 工具

| 工具 | 功能 |
|------|------|
| `file_operations` | 文件读写、目录创建 |
| `edit_file` | 文件编辑（replace/insert） |
| `bash` | 执行 Shell 命令 |
| `glob` | 文件搜索 |
| `grep` | 内容搜索 |
| `git` | Git 版本控制 |

## 工作流

```
1. /spec create "功能"     # 创建 SPEC.md
2. /plan                    # 生成实施计划
3. /develop                 # 生成代码
4. /test                    # 运行测试
5. /analyze                 # 检查问题
```

## 文档

- [ARCHITECTURE.md](ARCHITECTURE.md) - 详细系统架构
- [CLAUDE.md](CLAUDE.md) - Claude Code 使用指南
