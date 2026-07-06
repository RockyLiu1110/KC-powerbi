# Krannert Center — Audience Engagement & Belonging Analysis

> **一句话总结：** 对 Krannert Center for the Performing Arts 的 600+ 名观众进行问卷调研，通过 Python ETL + Power BI 构建了一套**归属感（Belonging）、NPS 和服务满意度**的分析仪表板，并提出了可落地的战略建议。

---

## 📋 项目背景

**Krannert Center for the Performing Arts (KCPA)** 是伊利诺伊大学香槟分校（UIUC）的表演艺术中心。本项目基于 REDCap 问卷数据，旨在回答以下核心问题：

- 不同观众群体（学生、教职工、社区成员）在 KCPA 的**归属感（Belonging）**如何？
- 哪些人对 KCPA 最满意？谁会推荐 KCPA 给他人（NPS）？
- 不参加活动的观众面临哪些障碍？
- 无障碍服务、票务体验、宣传渠道各维度表现如何？

---

## 🧰 技术栈

| 层级 | 工具 |
|------|------|
| 数据处理 | Python 3.x, pandas, numpy |
| 数据来源 | REDCap 问卷导出 (CSV) |
| 数据建模 | 星型模型 (Star Schema)：1 张事实表 + 8 张维度表 |
| 可视化 | Power BI (`.pbix`) |
| 版本控制 | Git + GitHub |

---

## 📁 项目结构

```
powerbi-prep/
│
├── raw-data/                          # 原始数据
│   └── CampusEngagementWith_DATA_2026-06-27_1054.csv   # REDCap 原始导出
│
├── output/                            # 处理后可直接导入 Power BI 的 CSV
│   ├── FACT_RESPONSES.csv             # ★ 核心事实表（每位受访者一行）
│   ├── DIM_AFFILIATION.csv            # 身份类别维度
│   ├── DIM_UNDERREP.csv               # 弱势群体维度
│   ├── DIM_EVENT_TYPES.csv            # 出席活动类型维度
│   ├── DIM_ATTEND_REASONS.csv         # 出席原因维度
│   ├── DIM_BARRIERS.csv              # 缺席障碍维度
│   ├── DIM_COMMUNICATION.csv          # 信息渠道维度
│   ├── DIM_PATRON_TYPE.csv            # 观众关系维度
│   ├── DIM_COLLEGE.csv               # 学院维度
│   ├── KPI_SUMMARY.csv               # KPI 汇总卡片
│   ├── NPS_DETAIL.csv                # NPS 按群体分解
│   ├── SERVICE_SCORES.csv            # 服务维度评分
│   ├── BELONGING_BY_SEGMENT.csv      # 归属感按群体对比
│   └── GEO_DATA.csv                  # 受访者地理分布
│
├── prepare_powerbi_data.py           # ETL 脚本（REDCap → 星型模型）
├── 人工产出.pbix                      # Power BI 仪表板文件
└── README.md
```

---

## 🔄 数据流水线

```
REDCap 原始 CSV (600+ 行, 100+ 列, checkbox 格式)
        │
        ▼
prepare_powerbi_data.py
  ├── 删除测试行
  ├── 字段映射（100+ 列 → 26 列核心指标）
  ├── Unpivot checkbox → 维度表
  ├── 计算 NPS / 归属感等级 / 观众分类
  └── 输出 14 个标准化 CSV
        │
        ▼
Power BI 导入 → 仪表板
```

---

## ⭐ 星型模型设计

```
                    ┌──────────────────┐
                    │  FACT_RESPONSES   │
                    │  (核心事实表)      │
                    │  ├─ record_id     │
                    │  ├─ belonging     │
                    │  ├─ nps_score     │
                    │  ├─ engagement    │
                    │  └─ ... (26列)    │
                    └──────┬───────────┘
           ┌───────────────┼───────────────┐
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │DIM_         │ │DIM_        │ │DIM_         │  ...
    │AFFILIATION  │ │EVENT_TYPES │ │ATTEND_      │
    │身份维度      │ │活动类型     │ │REASONS      │
    └─────────────┘ └─────────────┘ └─────────────┘
```

设计原则：事实表每行一个受访者 + 所有评分字段，维度表通过 `record_id` 关联，支持一对多查询。

---

## 📊 关键洞察 (Key Findings)

### 1. NPS 表现优异，忠诚度很高
- **总体 NPS = 77.6**，远超行业基准线（通常 30-50 即为良好）
- 各群体 Promoter 占比均超过 73%，Faculty/Staff 和 Community 达到 81-85%

### 2. 归属感存在群体差异
| 群体 | 归属感 | 文化认同感 |
|------|--------|------------|
| Faculty/Staff | **3.89** ⬆ | 3.87 |
| Community | 3.66 | **3.93** ⬆ |
| Student | 3.68 | 3.50 ⬇ |
| Other | 3.51 ⬇ | **4.07** ⬆ |

> 🔍 **学生群体的文化认同感最低（3.50）**，是重点改进方向。

### 3. 无障碍服务存在"知晓度鸿沟"
- 仅有 **36.9%** 的参与者知道如何使用无障碍导航服务（目标 80%）
- 但知道的人群中，无障碍评分高达 **4.11/5** —— 说明服务本身没问题，是**信息传达不到位**

### 4. 服务体验整体优秀
- Staff Welcoming: 4.34 | Ticket Experience: 4.36 | Mobile Ticket Ease: 4.35
- **Will Call Ready 仅 3.15**，是服务链中最薄弱的一环

### 5. 缺席的主要原因
| 障碍 | 提及次数 |
|------|----------|
| Schedule Conflict | 最多 |
| Didn't Know About Events | 第二 |
| Ticket Price | 第三 |

> 🔍 "不知道有活动" 和 "票价" 是可干预的，建议加强宣传 + 学生优惠。

### 6. Workshop 参与率低
- 仅 **18.8%** 出席者参加过 Workshop（目标 50%），有巨大增长空间

---

## 🚀 如何复现

### 前提条件
```bash
pip install pandas numpy
```

### 运行 ETL
```bash
cd powerbi-prep
python prepare_powerbi_data.py
# → 在 output/ 目录生成 14 个 CSV 文件
```

### 导入 Power BI
1. 打开 `人工产出.pbix` 或新建 Power BI 项目
2. 将 `output/` 目录下所有 CSV 导入为数据源
3. 在 Power BI 中建立 FACT ↔ DIM 表的关系（关联字段：`record_id`）

---

## 🔮 可扩展方向

- [ ] 统计检验（t-test/ANOVA）：验证群体间差异是否显著
- [ ] 文本分析：开放题回复的情感分析
- [ ] 预测模型：基于人口统计特征预测 NPS / 归属感
- [ ] 自动化刷新：连接 REDCap API 实现数据自动更新
- [ ] Jupyter Notebook EDA：替代 Power BI 的 Python 版探索性分析

---

*Built with Python, pandas, and Power BI · Data collected via REDCap at UIUC*
