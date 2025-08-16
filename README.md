# 🤖 智能代理設計模式與協調系統

## 📖 專案簡介

這是一個**智能代理設計模式與協調系統**的實作專案，展示了四種常見的智能代理設計模式，並提供了多種代理框架的完整實作範例。專案旨在幫助開發者理解如何構建智能AI系統，以及如何讓AI代理更有效地完成複雜任務。

## ✨ 主要功能特色

### 🔍 **四種核心設計模式**

#### 1. **反思模式 (Reflection Pattern)**
- **功能**：讓AI反思並改進自己的輸出
- **工作流程**：生成 → 反思 → 改進 → 重複直到滿意
- **應用場景**：程式碼生成與改進、文章寫作優化、創意內容迭代
- **優勢**：持續自我改進，提高輸出品質

#### 2. **規劃模式 (Planning Pattern)**
- **功能**：制定計劃並按步驟執行複雜任務
- **工作流程**：分析需求 → 制定計劃 → 選擇工具 → 按步驟執行
- **應用場景**：複雜任務分解、工作流程自動化、專案管理
- **優勢**：結構化思考，系統性解決問題

#### 3. **工具使用模式 (Tool Use Pattern)**
- **功能**：調用各種工具和API完成任務
- **工作流程**：識別需求 → 選擇工具 → 執行調用 → 整合結果
- **應用場景**：API整合、外部服務調用、數據處理
- **優勢**：擴展能力，整合外部資源

#### 4. **多代理協作模式 (Multi-Agent Collaboration)**
- **功能**：多個AI代理協同工作，分工合作
- **工作流程**：定義角色 → 建立依賴 → 協調執行 → 整合結果
- **應用場景**：團隊協作任務、複雜專案執行、多領域知識整合
- **優勢**：專業分工，提高效率

### 🚀 **四種代理框架實作**

#### 1. **AutoGen (微軟多代理框架)**
- **特色**：輕量級、易於使用、支援多代理對話
- **適用場景**：快速原型開發、簡單多代理協作
- **啟動方式**：`python agent_frameworks/autogen_multi_agent/main.py`

#### 2. **CrewAI (專門的多代理協作框架)**
- **特色**：專業的多代理協作、任務分解、角色定義
- **適用場景**：複雜專案管理、專業團隊協作
- **啟動方式**：`python agent_frameworks/crewai_multi_agent/main.py`

#### 3. **Swarm (OpenAI代理框架)**
- **特色**：OpenAI官方支援、整合度高、性能優化
- **適用場景**：企業級應用、大規模部署
- **啟動方式**：`python agent_frameworks/openai_swarm_agent/main.py`

#### 4. **LangGraph (LangChain圖形化框架)**
- **特色**：圖形化工作流程、狀態管理、複雜邏輯處理
- **適用場景**：複雜業務流程、狀態機應用
- **啟動方式**：`python agent_frameworks/langgraph/main.py`

## 🏗️ 專案架構

```
adpao/
├── 📁 src/                          # 核心設計模式實作
│   ├── reflection_agent/            # 反思代理模式
│   ├── planning_agent/              # 規劃代理模式
│   ├── tool_agent/                  # 工具使用代理模式
│   └── multi_agent/                 # 多代理協作模式
├── 📁 agent_frameworks/             # 代理框架實作
│   ├── autogen_multi_agent/         # AutoGen 實作
│   ├── crewai_multi_agent/          # CrewAI 實作
│   ├── openai_swarm_agent/          # Swarm 實作
│   └── langgraph/                   # LangGraph 實作
├── 📁 design_patterns/              # 設計模式教學範例
│   ├── reflection.ipynb             # 反思模式教學
│   ├── planning.ipynb               # 規劃模式教學
│   ├── tool_use.ipynb               # 工具使用教學
│   └── multiagent.ipynb             # 多代理協作教學
├── 📁 img/                          # 專案圖片資源
├── 📁 skills/                       # 技能定義
├── 📁 prompt_templates/             # 提示詞模板
├── requirements.txt                  # Python 依賴套件
└── README.md                        # 專案說明文件
```

## 🛠️ 技術架構

### **核心技術**
- **Python 3.11+**：主要開發語言
- **OpenAI API**：核心語言模型服務
- **Gradio**：Web 使用者介面
- **Graphviz**：代理關係圖形化

### **主要依賴套件**
- **langchain**：LangChain 框架
- **crewai**：CrewAI 多代理框架
- **autogen**：AutoGen 框架
- **langgraph**：LangGraph 圖形化框架
- **openai**：OpenAI API 客戶端
- **gradio**：Web 介面框架

## 🚀 快速開始

### **環境需求**
- Python 3.11 或更高版本
- OpenAI API 金鑰
- 穩定的網路連接

### **安裝步驟**

#### 1. **克隆專案**
```bash
git clone https://github.com/Kiwi1009/adpao.git
cd adpao
```

#### 2. **建立虛擬環境**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. **安裝依賴套件**
```bash
pip install -r requirements.txt
```

#### 4. **設定環境變數**
```bash
# 建立 .env 檔案
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

**⚠️ 重要提醒**：請將 `your_openai_api_key_here` 替換為你的真實 OpenAI API 金鑰

### **啟動應用程式**

#### **啟動 CrewAI 多代理系統**
```bash
python agent_frameworks/crewai_multi_agent/main.py
```
- 訪問：http://127.0.0.1:7860
- 功能：多代理協作、任務分解、角色管理

#### **啟動 AutoGen 多代理系統**
```bash
python agent_frameworks/autogen_multi_agent/main.py
```
- 訪問：http://127.0.0.1:7860
- 功能：輕量級多代理對話、快速原型開發

#### **啟動 Swarm 代理系統**
```bash
python agent_frameworks/openai_swarm_agent/main.py
```
- 功能：OpenAI 官方代理框架、企業級應用

#### **啟動 LangGraph 系統**
```bash
python agent_frameworks/langgraph/main.py
```
- 功能：圖形化工作流程、複雜業務邏輯處理

## 📚 學習資源

### **設計模式教學**
專案包含詳細的 Jupyter notebooks，展示每種設計模式的實作：

- **reflection.ipynb**：反思模式完整實作教學
- **planning.ipynb**：規劃模式實作範例
- **tool_use.ipynb**：工具使用模式教學
- **multiagent.ipynb**：多代理協作實作

### **實作範例**
每個代理框架都包含完整的實作範例，可以直接運行和學習。

## 💡 使用場景

### **開發者學習**
- 學習現代AI代理架構設計
- 理解提示工程最佳實踐
- 掌握工具整合方法
- 學習多代理協作系統

### **實際應用**
- **程式碼生成與改進**：使用反思代理
- **複雜任務規劃**：使用規劃代理
- **API整合與工具調用**：使用工具代理
- **團隊協作任務**：使用多代理系統

### **企業應用**
- 自動化工作流程
- 智能客服系統
- 內容生成與優化
- 數據分析與處理

## 🔧 故障排除

### **常見問題**

#### 1. **API 配額不足錯誤**
```
Error code: 429 - You exceeded your current quota
```
**解決方案**：檢查 OpenAI 帳戶餘額，確認 API 配額設定

#### 2. **端口被佔用**
```
ERROR: [Errno 10048] error while attempting to bind on address
```
**解決方案**：程式會自動選擇下一個可用端口（如 7861）

#### 3. **依賴套件安裝失敗**
**解決方案**：確保使用 Python 3.11+，並在虛擬環境中安裝

### **環境檢查**
```bash
# 檢查 Python 版本
python --version

# 檢查虛擬環境
pip list

# 檢查 API 金鑰
echo $OPENAI_API_KEY
```

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request 來改進這個專案！

### **貢獻方式**
1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 發起 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款，詳見 LICENSE 檔案。

## 🙏 致謝

感謝 OpenAI、LangChain、CrewAI 等開源社群提供的優秀框架和工具。

---

## 📞 聯絡資訊

如有問題或建議，請通過以下方式聯絡：
- GitHub Issues：https://github.com/Kiwi1009/adpao/issues
- 專案首頁：https://github.com/Kiwi1009/adpao

---

**�� 開始你的智能代理開發之旅吧！** 