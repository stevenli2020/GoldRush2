# GoldRush2 DR3 权重分配与动态聚合机制 — 改进版方案（终稿）

**版本：** V1.1（评审修订版）  
**日期：** 2026-09-04  
**状态：** V1.1 已批准并完成实现验证  
**前置文档：** DR3 原始提案、第三方评审报告、双方讨论记录

---

## 一、方案概述

本方案定义 GoldRush2 (GR2) 数据分析阶段 (DR3) 的权重分配逻辑与动态聚合引擎设计。其核心目标是：

1. 基于因果架构理论，为 45 个变量在 4 个时间跨度上分配具有经济学依据的相对权重。
2. 实现运行时动态归一化，使系统能够自适应变量的增删与数据缺失。
3. 通过数据完整性阈值检查和低置信度变量追踪，确保评分的可解释性与可靠性。

**设计约束（源自 `PROJECT.md`）：**
- V1 使用固定权重，无层级权重、无交互调整、无动态机制切换。
- 权重直接分配给单个变量，每个 Horizon 内权重归一化为 1.0。
- 不引入双轨制评分、不引入引擎级去重算法。

---

## 二、权重分配逻辑

### 2.1 理论基础：因果角色分层

权重分配的核心原则源自 GR1《金价因果模型 v2.2》：

> **必须严格区分"原始驱动因素"、"传导变量"、"市场放大因素"和"同步/滞后指标"。**

单一宏观冲击（如美联储政策转向）会依次经过多个层级传导：

```
FOMC预期变化 → 实际收益率 → 美元 → ETF资金流 → 期货头寸 → 金价
```

如果对所有变量平均赋权，底层逻辑会被重复计算多次。因此，权重分配遵循以下原则：

| 因果角色 | 权重策略 | 示例 |
|---|---|---|
| **原始驱动因素** | 在其主导的时间跨度上给予高权重 | L4-007 债务/GDP（长期）、L5-003 储备构成（长期） |
| **传导变量** | 给予中等权重，避免与上游驱动因素重复计算 | L1-001 10Y TIPS（传导货币政策至机会成本） |
| **市场放大因素** | 仅在极短期给予较高权重，中长期大幅降权 | L10-001 COMEX 头寸（1-5d 高，3-10y 极低） |
| **同步/滞后指标** | 给予低权重或仅在特定跨度使用 | L9-004 印度需求（季度，仅 1-3y/3-10y） |

### 2.2 时间跨度差异化分配

#### 1-5d（极短期）：微观结构与事件驱动主导

| 层级 | 权重倾向 | 理由 |
|---|---|---|
| L10 微观结构 | **极高** (15/8) | 头寸和未平仓合约是短期价格的主要放大器 |
| L3 政策预期 | **高** (12/8/8) | 事件驱动，FOMC 概率和期货定价直接影响日内走势 |
| L1 实际利率 | **中高** (10/8/6) | 算法交易的核心锚点 |
| L2 美元 | **中高** (10/5) | 高频联动的对冲资产 |
| L8 ETF 流 | **中** (8) | 短期资金流的直接体现 |
| L0/L4/L5 存量与宏观 | **极低** (1-2) | 结构性变量，短期内为噪音 |

#### 1-3m（短中期）：宏观周期与资金流主导

| 层级 | 权重倾向 | 理由 |
|---|---|---|
| L1 实际利率 | **高** (12/10/8) | 中期机会成本的核心度量 |
| L8 ETF 流 | **极高** (12) | 西方机构战术性配置的直接指标 |
| L4 通胀预期 | **中高** (5/5/6/6) | 购买力对冲逻辑开始显现 |
| L9 区域实物 | **中** (6/2) | 东西方定价权博弈的代理指标 |
| L10 微观结构 | **降权** (8/4) | 头寸在数月尺度下更多是趋势的结果 |

#### 1-3y（中长期）：结构性转变与流动性主导

| 层级 | 权重倾向 | 理由 |
|---|---|---|
| L4 财政与通胀 | **极高** (10/10/8/8) | 财政主导和货币贬值预期成为核心驱动 |
| L5 央行行为 | **极高** (10/8/8) | 储备配置战略和去美元化趋势 |
| L7 全球流动性 | **高** (8/6/5) | 系统性法币流动性决定中期估值 |
| L1 实际利率 | **中** (8/6/5) | 仍重要但不再单独主导 |
| L3 事件驱动 | **大幅压缩** (4/3/4/2) | 短期政策噪音在三年尺度下失去意义 |
| L10 微观结构 | **极低** (2/1) | 完全剥离短期噪音 |

#### 3-10y（长期）：货币架构与财政主导

| 层级 | 权重倾向 | 理由 |
|---|---|---|
| L4 财政可信度 | **极高** (15/12/10) | 主权债务可持续性是长期黄金的终极驱动 |
| L5 储备架构 | **极高** (12/12/10) | 去美元化和储备多元化是结构性趋势 |
| L0 存量/流量 | **高** (8/8/5) | 供给约束和官方锁仓效应 |
| L7 长期流动性 | **中高** (8/6) | 货币体系的长期通胀倾向 |
| L1 长期实际利率 | **中** (6/4/5/8) | 结构性机会成本，5Y5Y 远期权重回升 |
| L3/L8/L10 短期因素 | **极低** (1-2) | 在十年尺度下完全无效 |

### 2.3 重叠变量治理策略

以下变量对存在因果重叠或数据重叠风险，通过差异化时间跨度权重和 YAML 注释进行治理（不引入引擎级去重算法）：

| 重叠对 | 重叠类型 | 治理策略 |
|---|---|---|
| L0-002 (央行持有量-存量) vs L5-001 (央行购买量-流量) | 存量/流量 | 短期给 L5-001 更高权重（边际冲击），长期给 L0-002 更高权重（结构性趋势） |
| L1-001 (10Y TIPS) vs L1-002 (5Y TIPS) | 期限重叠 | 短期 5Y 权重略高（对政策更敏感），长期 10Y 权重更高（结构性锚点） |
| L1-006 (L1 预期政策利率) vs L3-001 (L3 联邦基金期货) | 跨层重叠 | L1-006 定位为"当前机会成本分解"，L3-001 定位为"未来路径重定价"；在 YAML 注释中明确区分 |
| L0-003 (ETF 持有量-存量) vs L8-001 (ETF 净流入-流量) | 存量/流量 | L0-003 在短期权重较低（存量变化慢），L8-001 在短中期权重较高（边际定价力量） |

---

## 三、动态权重处理机制

### 3.1 机制一：相对权重与运行时自动归一化

**设计：** `DR3_data_analytics/config/weights_v1.yaml` 中的数值为**相对重要性**，非绝对百分比。

**引擎行为：** 每次运行时，对当前配置中存在的所有变量权重求和，然后归一化：

$$W_i^{\text{effective}} = \frac{W_i^{\text{raw}}}{\sum_{j \in \text{configured}} W_j^{\text{raw}}}$$

**适应场景：**
- 新增变量：在 YAML 中添加条目即可，引擎自动重新分配。
- 删除变量：注释掉或移除条目即可，剩余变量权重等比例放大。
- 无需人工确保权重总和等于 1.0。

### 3.2 机制二：基于置信度的动态再分配

**设计：** 当变量 `confidence = 0.0`（数据过期、提取失败、数据源不可达）时，该变量不参与得分计算，其权重自动被其他有效变量瓜分。

**计算公式：**

$$\text{Raw Score} = \frac{\sum_{i \in \text{Valid}} (S_i \times W_i^{\text{raw}} \times C_i)}{\sum_{i \in \text{Valid}} (W_i^{\text{raw}} \times C_i)}$$

其中：
- $S_i \in \{-1, 0, +1\}$：变量 $i$ 的方向性信号
- $W_i^{\text{raw}}$：变量 $i$ 在 YAML 中的原始相对权重
- $C_i \in [0.0, 1.0]$：变量 $i$ 的数据置信度
- $\text{Valid}$：所有 $C_i > 0$ 的变量集合

**最终得分：** $\text{Score} = \text{round}(\text{Raw Score} \times 100)$，范围 $[-100, +100]$。

**数据可用性指标：**

$$\text{Data Availability} = \sum_{i \in \text{Valid}} W_i^{\text{effective}}$$

由于 $W^{\text{effective}}$ 已归一化至总和为 1.0，该指标直接表示"当前参与计算的有效权重占总配置权重的比例"。

### 3.3 机制三：数据完整性阈值检查（评审修订新增）

**设计：** 防止大量变量同时缺失时，少数可用变量被过度放大产生虚假信号。

**规则：**
- 若 $\text{Data Availability} \geq 0.6$：状态为 `NORMAL`。
- 若 $\text{Data Availability} < 0.6$：状态为 `DEGRADED`。

**DEGRADED 状态下的行为：**
- 得分仍然计算并输出（反映当前可用证据的共识方向）。
- `HorizonScore.status` 标记为 `"DEGRADED"`。
- CLI 输出中以醒目方式标注降级状态。
- `warnings` 中列出所有缺失变量及其原始权重。

### 3.4 机制四：高权重变量健康度监控（评审修订新增）

**设计：** 对归一化后权重排名前 5 的核心变量实施轻量级监控。

**规则：** 当 Top-5 核心变量的 `confidence = 0.0` 或变量缺失时：
- 在 `warnings` 中标记为 `HIGH_WEIGHT_MISSING: {variable_id}`。
- CLI 输出中使用 `🔴` 标识。

### 3.5 机制五：未知变量安全隔离

**设计：** 在 `data/current/` 中存在但未在 `weights_v1.yaml` 中配置的变量，不参与评分。

**行为：**
- 引擎忽略该变量。
- 在 `warnings` 中输出：`UNMAPPED: {variable_id} found in data but not in weight config; ignoring`。
- 防止未经审查的新变量意外干扰核心评分。

### 3.6 机制六：低置信度贡献者追踪（评审修订新增）

**设计：** 提供透明度，帮助用户理解哪些变量以较低的置信度参与了评分。

**规则：** 对于 $0 < C_i < 0.5$ 且 $C_i > 0$ 的变量，将其 `variable_id` 和 `confidence` 记录到 `HorizonScore.low_confidence_contributors` 列表中。

---

## 四、数据结构变更（评审修订）

### 4.1 `HorizonScore` 新增字段

```python
@dataclass
class HorizonScore:
    horizon: str
    score: int                          # -100 to +100
    raw_score: float                    # -1.0 to +1.0
    confidence: float                   # weighted average confidence
    data_availability: float            # fraction of configured weight available
    status: str                         # "NORMAL" or "DEGRADED"  ← 新增
    contributing_variables: int
    total_configured_variables: int
    top_bullish: list[str]
    top_bearish: list[str]
    low_confidence_contributors: list[dict]  # ← 新增
```

`low_confidence_contributors` 格式：
```json
[
  {"variable_id": "L4-001", "confidence": 0.3},
  {"variable_id": "L7-003", "confidence": 0.45}
]
```

### 4.2 `AggregatedResult` 输出结构

```json
{
  "generated_at": "2026-09-04T12:00:00Z",
  "weight_schema_version": "v1",
  "horizons": {
    "1-5d": {
      "horizon": "1-5d",
      "score": 45,
      "raw_score": 0.45,
      "confidence": 0.87,
      "data_availability": 0.92,
      "status": "NORMAL",
      "contributing_variables": 40,
      "total_configured_variables": 45,
      "top_bullish": ["L1-001", "L3-001", "L10-001"],
      "top_bearish": ["L2-001"],
      "low_confidence_contributors": [
        {"variable_id": "L6-002", "confidence": 0.4}
      ]
    }
  },
  "warnings": [
    "HIGH_WEIGHT_MISSING: L4-007 (weight=15)",
    "UNMAPPED: L4-010 found in data but not in weight config; ignoring"
  ]
}
```

---

## 五、配置文件示例（含注释与重叠治理标注）

```yaml
# GoldRush2 Weight Schema V1
# Strategy: Relative weights with runtime auto-normalization.
# Values represent relative importance; the aggregator normalizes them to sum to 1.0 per horizon.

version: "v1"
description: "Initial causal-aware relative weights based on GR1 causal model v2.2"
created: "2026-09-04"

horizons:
  "1-5d":
    # Layer 10 - Market Microstructure (Amplifier)
    # OVERLAP NOTE: L10-001 and L10-002 are complementary (positioning vs participation).
    L10-001: 15  # COMEX Managed-Money: primary short-term amplifier
    L10-002: 8   # COMEX Open Interest: participation breadth
    # Layer 3 - Monetary Policy Expectations (Event-driven)
    # OVERLAP NOTE: L1-006 (current opp. cost) vs L3-001 (future path repricing).
    # Strategy: L3-001 captures the CHANGE in expectations, L1-006 captures the LEVEL.
    L3-001: 12   # Fed Funds Futures: primary policy anchor
    L3-004: 8    # Policy Probability: tail risk pricing
    L3-002: 8    # OIS Curve: forward curve breadth
    L3-003: 5    # Terminal Rate: cycle endpoint
    L3-006: 5    # FOMC Statements: qualitative guidance
    L3-005: 2    # Dot Plot: quarterly, low short-term relevance
    # Layer 1 - Real Interest Rates
    # OVERLAP NOTE: L1-001 (10Y) vs L1-002 (5Y).
    # Strategy: 5Y slightly higher in short-term (more policy-sensitive).
    L1-001: 10   # 10Y TIPS: core opportunity cost anchor
    L1-002: 8    # 5Y TIPS: intermediate policy sensitivity
    L1-004: 6    # 2Y TIPS: front-end policy anchor
    L1-006: 8    # Expected Policy Rate: current opp. cost decomposition
    L1-003: 4    # Forward Real Rates: curve shape
    L1-005: 2    # Term Premium: duration compensation
    L1-007: 1    # 5Y5Y Forward: long-term, minimal short-term relevance
    # Layer 2 - USD / FX
    L2-001: 10   # DXY: primary FX anchor for gold
    L2-002: 5    # Broad USD: trade-weighted breadth
    L2-003: 2    # USD/CNY: China channel
    # Layer 4 - Inflation (monthly data, lower short-term weight)
    L4-001: 2    # CPI
    L4-002: 2    # Core PCE
    L4-003: 4    # 5Y Breakeven
    L4-004: 4    # 10Y Breakeven
    L4-006: 1    # Fiscal Deficit/GDP (quarterly)
    L4-007: 1    # Debt/GDP (quarterly)
    L4-008: 1    # Interest Expense/Revenue (annual)
    L4-009: 1    # Treasury Maturity Structure
    # Layer 5 - Official Sector (structural, minimal short-term)
    L5-001: 1    # Monthly CB Purchases
    L5-002: 1    # Gold Share of Reserves
    L5-003: 1    # Reserve Composition Change
    L5-006: 1    # Official Sales/Lending
    # Layer 6 - Geopolitics (event-driven)
    L6-001: 4    # Active Conflict Signal
    L6-002: 2    # Sanctions Events
    # Layer 7 - Global Liquidity
    L7-001: 3    # CB Balance Sheet
    L7-003: 1    # Credit Growth (quarterly)
    L7-004: 4    # Credit Spread Stress
    L7-005: 4    # Repo Funding Stress
    # Layer 8 - Investment Flows
    # OVERLAP NOTE: L0-003 (ETF stock) vs L8-001 (ETF flow).
    # Strategy: L8-001 captures marginal pricing power, L0-003 captures structural holding.
    L8-001: 8    # Gold ETF Net Flows: marginal investment demand
    # Layer 9 - Regional Physical
    L9-001: 4    # Shanghai Premium
    L9-004: 1    # India Demand (quarterly)
    # Layer 0 - Stock/Flow Architecture
    L0-001: 1    # Above-Ground Stock
    # OVERLAP NOTE: L0-002 (stock) vs L5-001 (flow).
    # Strategy: L5-001 dominates short-term (marginal impact), L0-002 dominates long-term.
    L0-002: 1    # Central-Bank Gold Holdings
    L0-003: 3    # Gold ETF Holdings (stock)
    L0-005: 1    # Bar-and-Coin Investment
    L0-006: 1    # Gold Recycling Flow
    L0-009: 3    # Gold Lease/Forward Rates

  # ... (1-3m, 1-3y, 3-10y horizons follow same pattern)
```

---

## 六、聚合引擎伪代码

```
FUNCTION run_analytics():
    weight_config ← load_yaml("DR3_data_analytics/config/weights_v1.yaml")
    variables ← load_all_json("data/current/L*.json")
    
    FOR each horizon IN ["1-5d", "1-3m", "1-3y", "3-10y"]:
        raw_weights ← weight_config.horizons[horizon]
        normalized ← normalize(raw_weights)  // sum to 1.0
        
        valid_sum ← 0
        weighted_signal ← 0
        weighted_conf ← 0
        low_conf_list ← []
        
        FOR each (var_id, weight) IN normalized:
            IF var_id NOT IN variables:
                WARN "configured but no data"
                CONTINUE
            IF horizon NOT IN variables[var_id].horizons:
                WARN "missing horizon"
                CONTINUE
            
            signal ← variables[var_id].horizons[horizon].signal
            conf ← variables[var_id].horizons[horizon].confidence
            
            IF conf ≤ 0:
                CONTINUE  // weight auto-redistributed
            
            valid_sum += weight × conf
            weighted_signal += signal × weight × conf
            weighted_conf += conf × weight
            
            IF 0 < conf < 0.5:
                APPEND {var_id, conf} TO low_conf_list
        
        // Check for unmapped variables
        FOR each var_id IN variables NOT IN normalized:
            WARN "UNMAPPED: ignoring"
        
        IF valid_sum ≤ 0:
            score ← 0; status ← "DEGRADED"; availability ← 0
        ELSE:
            raw_score ← weighted_signal / valid_sum
            score ← round(raw_score × 100)
            availability ← sum(weight for contributing variables)  // normalized configured weight
            aggregate_confidence ← weighted_conf / availability
            status ← "NORMAL" IF availability ≥ 0.6 ELSE "DEGRADED"
        
        // Top-5 normalized-weight monitoring
        FOR each var_id IN top_5(normalized):
            IF var_id NOT contributing:
                WARN "🔴 HIGH_WEIGHT_MISSING: {var_id}"
        
        SAVE HorizonScore(score, status, availability, low_conf_list, ...)
    
    WRITE "DR3_data_analytics/data/current_scores.json"
```

---

## 七、验证策略

### 7.1 单元测试覆盖

| 测试场景 | 预期行为 |
|---|---|
| 所有变量信号一致（全看多） | Score = +100 |
| 所有变量信号一致（全看空） | Score = -100 |
| 多空信号等权抵消 | Score = 0 |
| 单个变量缺失（confidence=0） | 权重自动再分配，分数不受影响 |
| 所有变量缺失 | Score = 0, status = DEGRADED, availability = 0 |
| 超过 40% 权重缺失 | status = DEGRADED |
| 未配置权重的新变量出现 | 忽略并输出 UNMAPPED 警告 |
| 权重 > 10 的变量缺失 | 输出 🔴 HIGH_WEIGHT_MISSING 警告 |
| 变量从 YAML 中删除 | 剩余权重自动归一化 |

### 7.2 端到端验证

- 使用 `data/current/` 下的 45 个真实变量 JSON 文件运行 `gr2 analyze`。
- 验证 `current_scores.json` 结构完整性和数值合理性。
- 验证 CLI 输出的得分条、警告和贡献者列表。

---

## 八、与项目约束的合规性检查

| 约束（源自 PROJECT.md / AGENTS.md） | 合规状态 |
|---|---|
| V1 使用固定权重，无层级权重 | ✅ 权重直接分配给变量 |
| 无交互调整 | ✅ 无引擎级去重或相关性惩罚 |
| 无动态机制切换 | ✅ 单一权重版本，无自动切换 |
| 选择最简单的实现 | ✅ 无多余抽象，逻辑线性 |
| 不保留向后兼容性 | ✅ 全新模块，无兼容层 |
| 模块化与关注点分离 | ✅ 独立的 `analytics/` 模块，只读不写 DR2 产出 |
| 使用现有依赖 | ✅ 仅使用 `yaml`, `json`, `dataclasses` |

---

## 九、后续工作（DR4/DR5 衔接）

本方案完成后，DR4 将：
1. 读取 `current_scores.json` 中的 4 个 Score 和 Confidence。
2. 使用 Gemini 生成 `current_report.md`（≤5000 字）。
3. 报告内容限于当前运行的证据和结果，不添加外部事实。

本方案完成后，DR5 将：
1. 提供 `gr2 run-all` 一键命令。
2. 串联收集 → 提取 → 分析 → 评分 → 报告全流程。
3. 在终端输出最终得分、降级状态和所有警告。

---

*本方案经第三方评审、双方讨论并达成共识后，已完成 V1.1 编码、测试及真实数据端到端验证。*
