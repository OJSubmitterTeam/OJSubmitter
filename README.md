# OJSubmitter

OJSubmitter 是一个代码提交工具，旨在简化向在线判题系统提交作业代码的流程。它提供了命令行界面（CLI）和图形用户界面（GUI），以满足不同用户的需求。项目采用模块化设计，包含处理提交、管理账户以及与在线判题系统 API 交互的组件。

## 功能特点

- **CLI 和 GUI 支持**：用户可以选择使用命令行界面快速提交代码，或使用图形界面获得更友好的用户体验。

- **账户管理**：安全地管理多个在线判题系统账户。

- **提交记录追踪**：跟踪您的提交历史和状态。

- **自定义设置**：通过设置模块，根据您的需求定制工具。

## 安装

1. 克隆仓库：

   ```bash
   git clone https://github.com/quyansiyuanwang/OJSubmitter.git
   cd OJSubmitter
   ```

2. 使用 `uv` 安装依赖：

   ```bash
   uv sync
   ```

## 使用方法

### 命令行界面（CLI）

1. 运行 CLI 工具：

   ```bash
   uv run run --mode CLI
   ```

### 图形用户界面（GUI）

1. 运行 GUI 工具：

   ```bash
   uv run run --mode GUI
   ```

   或

   ```bash
   uv run run
   ```

## 项目结构

- `src/CLI`：包含 CLI 实现。

- `src/GUI`：包含 GUI 实现，包括处理程序和组件。

- `src/OJSubmitter`：与在线判题系统交互的核心逻辑。

- `src/Util`：常用任务的工具函数。

- `scripts`：用于构建、调试和开发的辅助脚本。

- `tools`：用于代码格式化、类型检查和清理的附加工具。

## 贡献

1. Fork 此仓库。

2. 为您的功能或 Bug 修复创建一个新分支：

   ```bash
   git checkout -b feature-name
   ```

3. 提交更改：

   ```bash
   git commit -m "Description of changes"
   ```

4. 推送到您的分支：

   ```bash
   git push origin feature-name
   ```

5. 打开一个 Pull Request。

## 许可证

此项目基于 Mozilla Public License Version 2.0 许可证授权。有关详细信息，请参阅 LICENSE 文件。

## 鸣谢

- 感谢所有贡献者和开源社区的支持
  