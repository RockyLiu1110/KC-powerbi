# Krannert Center Power BI 看板 — 手把手操作指南

> **前提**：已运行 `prepare_powerbi_data.py`，所有CSV在 `output/` 文件夹中。
> 如果你还没运行，双击运行或在终端执行：`python prepare_powerbi_data.py`

---

## 第一步：导入数据到 Power BI

1. 打开 **Power BI Desktop**（如果没有，去微软官网免费下载）
2. 点击左上角 **Get data → CSV**
3. 进入 `powerbi-prep/output/` 文件夹，**按住 Ctrl 选中全部 14 个 CSV 文件**，一次性导入
4. 在弹出的预览窗口点 **Load**（不需要 Transform）
5. 左侧会看到 14 个表都加载好了

---

## 第二步：建立表关系（数据模型）

这是最关键的一步。左侧切换到 **Model 视图**（左边栏第三个图标）。

**所有表都通过 `record_id` 列连接到 `FACT_RESPONSES`**：

| 子表 | 连接方式 |
|------|---------|
| `DIM_AFFILIATION` | `record_id` ↔ `FACT_RESPONSES[record_id]` |
| `DIM_UNDERREP` | `record_id` ↔ `FACT_RESPONSES[record_id]` |
| `DIM_EVENT_TYPES` | `record_id` ↔ `FACT_RESPONSES[record_id]` |
| `DIM_ATTEND_REASONS` | `record_id` ↔ `FACT_RESPONSES[record_id]` |
| `DIM_BARRIERS` | `record_id` ↔ `FACT_RESPONSES[record_id]` |
| `DIM_COMMUNICATION` | `record_id` ↔ `FACT_RESPONSES[record_id]` |
| `DIM_PATRON_TYPE` | `record_id` ↔ `FACT_RESPONSES[record_id]` |
| `DIM_COLLEGE` | `record_id` ↔ `FACT_RESPONSES[record_id]` |

### 操作步骤：
1. 点击 `FACT_RESPONSES` 表的 `record_id`，**拖拽**到 `DIM_AFFILIATION` 的 `record_id`
2. 会自动生成一条连线，确认是 **一对多**（1→*）
3. **重复以上操作**，把其余 7 个 DIM_ 表全部连上
4. `KPI_SUMMARY`、`NPS_DETAIL`、`SERVICE_SCORES`、`BELONGING_BY_SEGMENT`、`GEO_DATA` 这几个表**不需要建立关系**，它们是独立汇总表

做完后模型图应该像一个星形：`FACT_RESPONSES` 在中间，所有 DIM_ 表围绕它。

---

## 第三步：逐个页面制作看板

现在切换到 **Report 视图**（左边栏第一个图标），开始做图。

---

### 📄 第1页：Executive Dashboard（高管总览）

#### 1.1 标题
- 插入 **Text box**，写：`Krannert Center 观众参与度看板 | 571份问卷 | 2025年4月`

#### 1.2 KPI 卡片行（顶部一排5个）
> 使用表：`KPI_SUMMARY`

- 视觉对象：**Card**（卡片）
- 把 `Value` 拖入 Fields
- 用 Filter 筛选不同的 KPI：

| 卡片内容 | 筛选条件 |
|----------|---------|
| 归属感均分 | `KPI_Name = "Overall Belonging Score (1-5)"` |
| NPS | `KPI_Name = "NPS (Net Promoter Score)"` |
| 无障碍知晓率 | `KPI_Name = "% Know Accessibility Navigation"` |
| 员工欢迎度 | `KPI_Name = "Staff Welcoming Score (1-5)"` |
| 工作坊参与率 | `KPI_Name = "Workshop Participation Rate"` |

操作：每插入一个Card → 拖入`Value` → 在Filters pane里对`KPI_Name`做筛选。

#### 1.3 受众构成环形图
> 使用表：`DIM_AFFILIATION`

- 视觉对象：**Donut chart**
- Legend：`affiliation_type`
- Values：`record_id`（右键选 **Count**）
- 点击右上角调色板，选择合适的颜色

#### 1.4 NPS 分类条形图
> 使用表：`NPS_DETAIL`

- 视觉对象：**Stacked bar chart**
- Y轴：`audience_segment`
- X轴：`Percentage`
- Legend：`NPS_Category`
- 颜色：Promoter=绿色, Passive=黄色, Detractor=红色

#### 1.5 归属感/代表感/文化认同 三个仪表盘
> 使用表：`KPI_SUMMARY`

- 视觉对象：**Gauge**
- Value：`Value`
- Maximum：手动设 5
- 筛选 `Category = "Belonging"` 的三个 KPI，放三个 Gauge 并排

---

### 📄 第2页：Belonging & Representation（归属感与代表感）

新建一页，命名为"归属感分析"。

#### 2.1 各 Segment 的归属感对比柱状图
> 使用表：`BELONGING_BY_SEGMENT`

- 视觉对象：**Clustered bar chart**
- Y轴：`metric`
- X轴：`average_score`
- Legend：`audience_segment`
- 从这个图可以一眼看出：Student 在三个维度都低于 Community

#### 2.2 弱势群体 vs 非弱势群体的归属感箱线图
> 使用表：`FACT_RESPONSES`

- 视觉对象：**Box and whisker chart**
- Category：`is_underrepresented_label`
- Values：`belonging_score`
- 看出两边分布差异

#### 2.3 归属感评级分布（按段）
> 使用表：`FACT_RESPONSES`

- 视觉对象：**Stacked column chart**
- X轴：`belonging_level`
- Y轴：`record_id`（Count）
- Legend：`audience_segment`
- 看 "Completely(5)" 那列各段占比

#### 2.4 各学院归属感热力图
> 使用表：先建立 `DIM_COLLEGE` ↔ `FACT_RESPONSES` 关系（应该已建好）

- 视觉对象：**Table** 或 **Matrix**
- Rows：`DIM_COLLEGE[college]`
- Values：`FACT_RESPONSES[belonging_score]`（设置为 Average）
- 排序：按平均值降序
- 用 **Conditional formatting** → Background color 做颜色渐变，高的是绿色，低的是红色

---

### 📄 第3页：Accessibility & Barriers（无障碍与障碍）

新建一页，命名为"无障碍分析"。

#### 3.1 无障碍认知漏斗
> 使用表：`FACT_RESPONSES`

做三张卡片并列：

| 卡片 | 数值来源 |
|------|---------|
| 出席过活动 | `attended_event = "Yes"` 的 record_id count |
| 知道无障碍导航 | `know_accessibility_nav = "Yes"` 的 count |
| 对感官友好演出感兴趣 | `sensory_interest = "Yes"` 的 count |

做法：
- 插入3个 **Card** 视觉对象
- 每个在 Filter 里设对应的筛选条件
- 用箭头形状连接它们（Insert → Shapes → Arrow），形成漏斗视觉效果

#### 3.2 无障碍各维度评分
> 使用表：`FACT_RESPONSES`（出席者）

- 视觉对象：**Radar chart**（雷达图）
- Category：手动创建一个小表（用 Enter data）：
  ```
  维度
  设施无障碍
  感官需求满足
  员工欢迎度
  传播有效性
  ```
- 但 Power BI 原生雷达图不太好用，换用 **Clustered bar chart**：
  - Y轴：分别拖入 `accessibility_rating`、`sensory_needs_met`、`staff_welcoming`、`communication_effectiveness`
  - 每个都设为 Average
  - 对比一目了然

#### 3.3 未出席原因
> 使用表：`DIM_BARRIERS`

- 视觉对象：**Horizontal bar chart**
- Y轴：`barrier`
- X轴：`record_id`（Count）
- 排序：降序

---

### 📄 第4页：Patron Services & Ticketing（票务与观众服务）

新建一页，命名为"观众服务"。

#### 4.1 六项服务满意度横向对比
> 使用表：`SERVICE_SCORES`

- 视觉对象：**Clustered bar chart**
- Y轴：`Service_Dimension`
- X轴：`Average_Score`
- 排序：按 `Average_Score` 升序 → 最低的在上面，一眼看到 **Mobile Ticket Ease** 是短板

#### 4.2 各Segment服务满意度差异
> 使用表：`FACT_RESPONSES`

- 视觉对象：**Clustered column chart**（分组柱状图）
- X轴：`audience_segment`
- Y轴：依次拖入6个服务指标（都设为Average）：
  - `staff_welcoming`
  - `patron_services_satisfaction`
  - `ticket_experience`
  - `mobile_ticket_ease`
  - `will_call_ready`
  - `informed_patron_services`

#### 4.3 工作坊参与
> 使用表：`FACT_RESPONSES`（出席者）

- 视觉对象：**Donut chart**
- Legend：`attended_workshop`
- Values：`record_id`（Count）
- 再放一个Card显示工作坊价值评分均值（`workshop_value`的平均值，筛掉空白）

#### 4.4 传播渠道效果
> 使用表：`DIM_COMMUNICATION`

- 视觉对象：**Treemap**
- Category：`communication_channel`
- Values：`record_id`（Count）
- 面积最大的 = 最强渠道

---

### 📄 第5页：NPS Drivers（NPS驱动因素分析）

新建一页，命名为"NPS分析"。

#### 5.1 NPS 分类占比（按受众）
> 使用表：`NPS_DETAIL`

- 视觉对象：**100% Stacked bar chart**
- Y轴：`audience_segment`
- X轴：`Percentage`
- Legend：`NPS_Category`

#### 5.2 归属感 vs NPS 散点图
> 使用表：`FACT_RESPONSES`

- 视觉对象：**Scatter chart**
- X轴：`belonging_score`
- Y轴：`nps_score`
- Legend：`audience_segment`
- 可以看出归属感高的人基本都打9-10分

#### 5.3 各维度与NPS的关系（平行柱状图）
> 使用表：`FACT_RESPONSES`

- 选中散点图上一个高 NPS 的点 → 右键 → **Analyze → Explain the increase**
- 更简单的方法：用 NPS_Category 做切片器，切换看各分类下归属感/服务满意度的均值差异

#### 5.4 出席活动类型偏好
> 使用表：`DIM_EVENT_TYPES`

- 视觉对象：**Bar chart**
- Y轴：`event_type`
- X轴：`record_id`（Count）
- 排序：降序

---

## 第四步：加交互式切片器（Slicer）

在每个页面顶部放以下切片器，让所有图表联动：

1. **受众分类切片器**
   - 视觉对象：**Slicer** → 拖入 `FACT_RESPONSES[audience_segment]`
   - 样式：Dropdown 或 Tile

2. **出席状态切片器**
   - 拖入 `FACT_RESPONSES[attended_event]`

3. **弱势群体切片器**
   - 拖入 `FACT_RESPONSES[is_underrepresented_label]`

4. **设置切片器同步**
   - 选中切片器 → View → **Sync slicers** → 勾选要同步到的页面

---

## 第五步：美化

1. **配色方案**：用 KCPA 品牌色
   ```
   深蓝 #1B3A5C   金色 #C8963E   酒红 #6B2737   灰 #6C757D
   ```
2. **背景**：每个页面设置 Page Background → 白色或浅灰
3. **字体**：标题用 Segoe UI Bold 16pt，数字用 12pt
4. **图例**：都放在图表下方或右侧

---

## 最终效果检查清单

看板做完后检查：

- [ ] 第1页能看到 KPI卡片 + 受众构成 + NPS分布
- [ ] 第2页能看到学生归属感低于社区成员
- [ ] 第3页能看到63%的人不知道无障碍服务
- [ ] 第4页能看到移动票务是最大服务短板(3.89)
- [ ] 第5页能看到归属感和NPS正相关
- [ ] 所有页面切换切片器时图表联动

---

## 常用 DAX 公式（可选进阶）

如果你要做复杂计算，在 Modeling → New Measure 中输入：

```DAX
// NPS 净推荐值
NPS_Score = 
VAR Total = COUNT(FACT_RESPONSES[nps_score])
VAR Promoters = CALCULATE(COUNT(FACT_RESPONSES[nps_score]), FACT_RESPONSES[nps_score] >= 9)
VAR Detractors = CALCULATE(COUNT(FACT_RESPONSES[nps_score]), FACT_RESPONSES[nps_score] <= 6)
RETURN DIVIDE(Promoters - Detractors, Total) * 100

// 归属感高分率 (≥4)
Belonging_High_Rate = 
VAR High = CALCULATE(COUNT(FACT_RESPONSES[belonging_score]), FACT_RESPONSES[belonging_score] >= 4)
VAR Total = COUNT(FACT_RESPONSES[belonging_score])
RETURN DIVIDE(High, Total)

// 无障碍认知率
Accessibility_Awareness = 
VAR Yes = CALCULATE(COUNT(FACT_RESPONSES[know_accessibility_nav]), FACT_RESPONSES[know_accessibility_nav] = "Yes")
VAR Total = COUNT(FACT_RESPONSES[know_accessibility_nav])
RETURN DIVIDE(Yes, Total)
```

---

> 💡 **提示**：如果某个图做不出来，检查表关系是否正确建立。所有 DIM_ 表必须和 FACT_RESPONSES 建立 `record_id` 一对多关系。
