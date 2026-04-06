# fly-code 架构文档

## 概述

fly-code 是一个文档驱动的编程智能体 CLI。核心原则是**文档优先**：每个任务都从 SPEC.md 开始，然后进行代码实现。

## 核心架构：Tools + Body

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户输入 (Body)                             │
│   - user_input: 用户需求、bug、功能描述                             │
│   - project_context: SPEC.md + 项目文件                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          System Prompt                               │
│   - 角色定义: 专家编程智能体                                         │
│   - 能力描述: 文件读写、命令执行、代码搜索分析                        │
│   - 工作流: 文档优先                                                 │
│   - 工具列表: 所有可用 tools 的 JSON Schema                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Agent                                      │
│   - 编排 tools + model                                             │
│   - 解析 AI 响应中的 tool_call                                      │
│   - 执行工具并反馈结果                                              │
│   - 迭代直到完成                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AI 模型层                                    │
│   ┌─────────────────┐          ┌─────────────────┐                │
│   │   OllamaModel   │          │  MiniMaxModel   │                │
│   │   (本地)        │          │   (云端)         │                │
│   └─────────────────┘          └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          工具层                                      │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│   │file_tool  │ │edit_tool  │ │bash_tool  │ │glob_tool  │      │
│   │ 文件读写   │ │ 文件编辑   │ │ 命令执行   │ │ 文件搜索   │      │
│   └────────────┘ └────────────┘ └────────────┘ └────────────┘      │
│   ┌────────────┐                                                │
│   │grep_tool  │  内容搜索                                        │
│   └────────────┘                                                │
└─────────────────────────────────────────────────────────────────────┘
```

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                            CLI 层                                   │
│  ┌──────────────┐  ┌─────────────────────────────────────────────┐  │
│  │   main.py    │  │                    repl.py                 │  │
│  │  (argparse)  │  │           交互式 REPL，斜杠命令              │  │
│  └──────────────┘  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Agent 核心层                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                        agent.py                              │  │
│  │  - run(user_input) → AI 响应                                │  │
│  │  - get_system_prompt()                                      │  │
│  │  - get_project_context()                                    │  │
│  │  - _extract_tool_call()                                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────┐  ┌────────────┐  ┌─────────┐  ┌─────────┐  ┌──────┐ │
│  │ Planner  │  │ Developer  │  │ Tester  │  │ Analyzer│  │Deploy│ │
│  └──────────┘  └────────────┘  └─────────┘  └─────────┘  └──────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│          工具层              │    │         模型层               │
│  ┌─────────────────────┐   │    │  ┌─────────────────────┐    │
│  │ tools/__init__.py    │   │    │  │ models/__init__.py  │    │
│  │ - TOOL_REGISTRY     │   │    │  │ - MODEL_REGISTRY    │    │
│  │ - get_tool()        │   │    │  │ - get_model()       │    │
│  │ - get_all_tools()   │   │    │  └─────────────────────┘    │
│  └─────────────────────┘   │    │  ┌─────────────────────┐    │
│  ┌─────────────────────┐   │    │  │ models/base.py     │    │
│  │ tools/base.py       │   │    │  │ - AIModel (ABC)    │    │
│  │ - BaseTool (ABC)   │   │    │  │ - AIResponse       │    │
│  │ - ToolResult        │   │    │  └─────────────────────┘    │
│  └─────────────────────┘   │    │  ┌─────────────────────┐    │
│  ┌─────────────────────┐   │    │  │ ollama_model.py    │    │
│  │ file_tool.py        │   │    │  │ minimax_model.py   │    │
│  │ edit_tool.py        │   │    │  └─────────────────────┘    │
│  │ bash_tool.py        │   │    │                            │
│  │ glob_tool.py        │   │    │                            │
│  │ grep_tool.py        │   │    │                            │
│  │ git_tool.py         │   │    │                            │
│  └─────────────────────┘   │    │                            │
└─────────────────────────────┘    └─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        文档管理层                                    │
│  ┌──────────────────────┐      ┌─────────────┐                    │
│  │   SpecManager        │      │  DocReader  │                    │
│  │   (SPEC.md 增删改查) │      │  (解析)     │                    │
│  └──────────────────────┘      └─────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

## 模块设计

### Agent (`core/agent.py`)

核心编排器，将用户输入和工具发送给 AI 模型。

```python
class Agent:
    def run(self, user_input: str, verbose=True) -> str:
        """运行 agent，返回 AI 响应"""
        # 构建消息
        system = self.get_system_prompt()
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": user_input}]

        while iterations < max_iterations:
            print(f"[{iterations}/{max}] 正在思考...")  # 实时输出

            response = self.model.chat(messages, tools=None)  # Ollama 不使用 tools API
            tool_call = self._extract_tool_call(response.content)

            if not tool_call:
                return response.content  # 无工具调用，返回响应

            # 执行工具
            result = tool.execute(**tool_params)
            print(f"[工具调用] {tool_name}: {result.content[:100]}")

            # 将结果返回给模型继续
            messages.append({"role": "assistant", "content": last_response})
            messages.append({"role": "user", "content": f"Tool result: {result.to_dict()}"})
```

**执行输出示例:**
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

**System Prompt 结构:**
```python
def get_system_prompt(self) -> str:
    return """You are an expert programming agent designed to actually create files.

CRITICAL RULES:
1. When asked to create code - you MUST use file_operations tool to CREATE IT
2. NEVER just describe - actually DO IT by calling tools
3. When you need a tool, output ONLY JSON: {"tool": "name", "parameters": {...}}

Workflow for creating projects:
1. directory_create - create project folder
2. file_write - create each source file with REAL CODE
3. bash - run commands if needed

Available tools:
{"name": "file_operations", ...},
{"name": "edit_file", ...},
{"name": "bash", ...},
{"name": "glob", ...},
{"name": "grep", ...},
{"name": "git", ...}

After each tool result, continue until task is COMPLETE.
"""
```

---

### 工具层 (`core/tools/`)

#### BaseTool (`base.py`)

```python
class BaseTool(ABC):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters(self) -> dict: ...  # JSON Schema

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: ...

@dataclass
class ToolResult:
    success: bool
    content: str
    error: str | None
    metadata: dict
```

#### FileTool (`file_tool.py`)

```python
class FileTool(BaseTool):
    # 操作: file_read, file_write, directory_create
    def execute(self, operation, path, content="", **kwargs) -> ToolResult:
        if operation == "file_read":
            return ToolResult(True, path.read_text())
        elif operation == "file_write":
            path.write_text(content)
            return ToolResult(True, "Written")
        elif operation == "directory_create":
            path.mkdir(parents=True, exist_ok=True)
            return ToolResult(True, "Created")
```

#### EditTool (`edit_tool.py`)

```python
class EditTool(BaseTool):
    # 操作: replace, insert_after, insert_before, delete
    def execute(self, operation, path, old_content="", new_content="", **kwargs):
        # replace: 替换第一次出现的 old_content
        # insert_after: 在包含 search_line 的行后插入
        # insert_before: 在包含 search_line 的行前插入
```

#### BashTool (`bash_tool.py`)

```python
class BashTool(BaseTool):
    def execute(self, command, cwd="", timeout=30, **kwargs):
        result = subprocess.run(command, shell=True, capture_output=True)
        return ToolResult(
            success=(result.returncode == 0),
            content=result.stdout + result.stderr,
            metadata={"returncode": result.returncode}
        )
```

#### GlobTool / GrepTool

文件搜索和内容搜索工具。

---

### 模型层 (`core/models/`)

#### AIModel (`base.py`)

```python
class AIModel(ABC):
    @abstractmethod
    def complete(self, prompt, system="", tools=None) -> AIResponse: ...

    @abstractmethod
    def chat(self, messages, system="", tools=None) -> AIResponse: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

@dataclass
class AIResponse:
    content: str
    model: str
    usage: dict | None
    finish_reason: str | None
```

#### OllamaModel (`ollama_model.py`)

```python
class OllamaModel(AIModel):
    def __init__(self, base_url="http://localhost:11434", model=""):
        # 自动选择第一个可用模型
        self._model = model or self._select_first_available()

    def switch_model(self, model_name: str) -> tuple[bool, str]:
        """切换到指定模型"""
        available = self.list_models()
        if model_name not in available:
            return False, f"Model not found. Available: {available}"
        self._model = model_name
        return True, f"Switched to {model_name}"

    def chat(self, messages, system="", tools=None) -> AIResponse:
        # 注意：不发送 tools 参数，通过 System Prompt 指令模型输出 JSON
        payload = {"model": self._model, "messages": all_messages, "stream": False}
        response = httpx.post(f"{self.base_url}/api/chat", json=payload)
        return AIResponse(content=data["message"]["content"], model=self.name)
```

---

### CLI 层 (`cli/repl.py`)

```python
class REPL:
    def handle_slash_command(self, line):
        if line == "/agent":
            self._cmd_agent(args)  # 启动 Agent 模式
        elif line == "/code":
            self._cmd_code(desc)   # AI 生成代码
        elif line == "/vibe":
            self._cmd_vibe()       # Vibe 模式

    def _cmd_agent(self, args):
        # 交互式 Agent 模式
        while True:
            line = input("agent> ")
            if line == "/done": break
            response = self.agent.run(line, verbose=self.verbose)
            print(response)
```

---

## 数据流

### Agent 执行流程

```
1. 用户输入
   user_input = "创建用户登录模块"

2. Agent 构建请求
   system = get_system_prompt()
   messages = [
       {"role": "system", "content": system},
       {"role": "user", "content": user_input}
   ]

3. AI 模型响应
   response = model.chat(messages, tools=tools)
   # 可能返回:
   # {"tool": "file_operations", "parameters": {"operation": "file_write", "path": "auth.py", "content": "..."}}

4. Agent 解析工具调用
   tool_call = _extract_tool_call(response.content)
   if tool_call:
       result = get_tool(tool_call["tool"]).execute(**tool_call["parameters"])
       messages.append({"role": "tool", "content": result.to_dict()})
       # 继续循环...

5. 返回最终响应
   return response.content
```

### 工具调用解析

```python
def _extract_tool_call(self, text):
    # 尝试从 markdown 代码块中提取 JSON
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 或直接匹配 JSON 对象
    match = re.search(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"parameters"\s*:\s*\{', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None
```

---

## 项目结构

```
fly-code/
├── cli/
│   ├── __init__.py
│   ├── main.py          # argparse CLI，入口
│   └── repl.py          # 交互式 REPL，支持斜杠命令
├── core/
│   ├── __init__.py
│   ├── agent.py         # Agent 编排器 ⭐
│   ├── planner.py
│   ├── developer.py
│   ├── tester.py
│   ├── analyzer.py
│   ├── deployer.py
│   ├── tools/           # 工具封装 ⭐
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── file_tool.py
│   │   ├── edit_tool.py
│   │   ├── bash_tool.py
│   │   ├── glob_tool.py
│   │   ├── grep_tool.py
│   │   └── git_tool.py
│   ├── models/          # AI 模型封装 ⭐
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── ollama_model.py
│   │   └── minimax_model.py
│   └── ai_client.py
├── docs/
│   ├── spec_manager.py
│   └── reader.py
├── utils/
│   └── logger.py        # 日志模块（彩色输出、文件日志）
├── tests/
├── pyproject.toml
├── README.md
├── ARCHITECTURE.md
└── CLAUDE.md
```

---

## 扩展点

### 添加新工具

1. 继承 `BaseTool`
2. 实现 `name`, `description`, `parameters`, `execute`
3. 在 `tools/__init__.py` 的 `TOOL_REGISTRY` 注册

```python
class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    def execute(self, param1, **kwargs) -> ToolResult:
        return ToolResult(True, f"Done: {param1}")

# 注册
TOOL_REGISTRY["my_tool"] = MyTool
```

### 添加新模型

1. 继承 `AIModel`
2. 实现 `complete`, `chat`, `name`, `set_api_key`
3. 在 `models/__init__.py` 的 `MODEL_REGISTRY` 注册
