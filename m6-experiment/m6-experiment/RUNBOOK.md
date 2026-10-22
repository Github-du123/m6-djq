# M6 操作、报告与演示材料

## 你的工作内容

你负责设计可控实验、准备正常干扰事件、保管真实答案、比较两次调查结果，并把
实验结果转成报告和展示。M1搭平台，M2采集日志，M3处理格式，M4提供查询接口，
M5执行调查；M6验证在固定条件下调查能否重复、证据是否充分。

本次代码包已经提供实验工具和测试，真实系统实验尚未完成。请先阅读 README.md
的命令与接口，交给 M1/M5 确认后接入。不要把示例或测试数据写成真实实测结果。

## 合成数据与真实实验分开

`dataset` 只写 JSON 文件，没有执行 PowerShell、登录或发出网络请求。因此它可以验证
索引字段、证据引用和比较逻辑，但不能证明系统采集了真实事件。

真实演示由队友在自有、授权的隔离虚拟机内操作并保存时间记录：

1. M1/M2确认 Windows Security、Sysmon 和 Zeek 采集正常，三个模式分别展示。
2. 在实验账号/主机上记录多次失败登录和同源成功网络登录。M1/M2提供已验证的
   操作方法并检查锁定策略；M6无需编写口令猜测程序。
3. 执行只输出标记文字的编码命令，记录实际命令、父进程、PID、时间及 Sysmon 1。
4. 从同一实验终端手工请求团队 HTTP 服务 `/checkin`，确认 Zeek 记录。
   合成数据中的 10.10.10.50 仅为占位实验地址，不应直接作为真实请求目标。
5. 加入正常登录、其他主机的管理命令、普通网页访问，以及窗口前后活动。
6. M6保存独立事件清单和主机/IP映射，校准时区，核对采集遗漏；再冻结数据。

现有事件只能支持登录—进程—网络的时间/主机关联。没有 Sysmon 网络连接或其他
进程级网络证据时，不能断言某 HTTP 连接由 PowerShell 发起。更不能仅凭编码命令
断言恶意行为。`confirmed` 指预设指示序列存在，真实账号失陷仍需额外证据。

## 两次实验检查顺序

- 冻结同一索引导出/快照、假设、窗口、模型版本、参数、提示词、schema及工具。
- 检查真实 ES 数据哈希与冻结文件对应，记录配置；ground truth 不进入 agent上下文。
- A 使用新会话、新 run ID、新账本；保存原始报告、计划、完整工具响应和使用量。
- B重复同样流程，保持索引和配置不变；不能把A的结果放进B上下文。
- M6在两次报告完成后运行 compare，再阅读 private ground truth。
- 审查所有正文事实是否导出为 claims；逐条确认引用确实支持表述。
- 检查缺源/缺窗口应当 inconclusive；检查干扰事件是否被错误串联。
- 对 differences 中每项差异写原因：措辞、查询策略、截断、缺失数据或实现问题。

## Kibana建议视图（交由M1配置）

建立覆盖 `windows-security,sysmon,zeek` 的只读 data view，时间字段 `@timestamp`。
显示绝对窗口 `2026-10-22T14:00:00+08:00` 至 `14:30:00+08:00`，确认界面时区；
严格排除结束边界时可额外使用 `@timestamp < "2026-10-22T14:30:00+08:00"`。

- 登录表：`host.name : "WS-01" and user.name : "lab-user" and event.code : ("4624" or "4625")`。
- 进程表：`host.name : "WS-01" and process.name : "powershell.exe"`，显示命令行和父进程。
- 网络表：`source.ip : "10.10.10.21"`，显示目标IP/端口、URL和时间。
- 概览：按 event.dataset 分组计数、时间直方图、按 host.name 分组。

不要依赖 Zeek 的 user.name，它通常没有账号身份信息。合成bulk导入演示应明确标注
synthetic fixture；三种采集模式仍由M2单独展示。

## 报告英文草稿（结果空位须实测填写）

### Executive summary
TraceHunt investigates a threat-hunting hypothesis through typed, read-only MCP tools
on the Elastic Stack. Our evaluation design separates investigation inputs from a
private event manifest and compares two clean runs under frozen conditions. The
experiment assesses query selection, retrieved evidence, verdicts, factual claims and
citation traceability. At this stage, the M6 evaluation toolkit has passed offline tests;
end-to-end agent repeatability has not yet been measured.

### Experimental method
We prepared a controlled sequence containing repeated failed logons, a successful
network logon, an encoded PowerShell process and a subsequent host-correlated HTTP
connection. Benign events from other accounts, hosts and destinations were included
to test whether the investigation incorrectly linked unrelated activity. The current
fixtures are synthetic ECS documents and do not demonstrate live collection. Before
the final evaluation, the dataset, hypothesis, time interval, model settings, prompts,
schema and tool versions will be frozen. The hunt agent will run twice in separate
sessions without access to the evaluation manifest or the other run's output.

### Results table

| Measure | Run A | Run B | Comparison |
|---|---|---|---|
| Verdict | Not measured | Not measured | Not measured |
| Required sources queried | Not measured | Not measured | Target: 3/3 each |
| Verified collection interval | Not verified | Not verified | Target: all sources |
| Query overlap | — | — | Not measured |
| Evidence overlap | — | — | Not measured |
| Claim exact agreement | — | — | Not measured |
| Reference linkage coverage | Not measured | Not measured | Semantic review separate |
| Ground-truth verdict correctness | Not measured | Not measured | Evaluate privately |
| Runtime, tool calls, tokens | Not measured | Not measured | Not measured |

### Limitations
A single staged hypothesis cannot establish general detection accuracy. Synthetic
fixtures cannot validate real connector behavior or collection continuity. Event
bounds do not prove uninterrupted monitoring. Reference linkage does not establish
that a citation supports the associated claim. The current network evidence permits
host and time correlation, but not process-level attribution. Evidence-ledger
truncation may reduce measured overlap. A declared freeze ID must be checked against
independent dataset and configuration records. Matching verdicts can still be wrong.

### Conclusion before final runs
The M6 module provides a reproducible data preparation and evaluation procedure.
Offline tests verify key failure cases and compatibility with the supplied M1 mapping.
A final claim about agent repeatability requires two completed frozen runs, independent
coverage checks and a manual audit of factual support.

完成真实实验后，替换结果表与结论；目前不能改写为“系统已达到100%准确率”。

## 演示衔接（全组五分钟中M6约45秒）

“Here are two independent runs of the same frozen hypothesis and dataset. We compare
not only their final verdicts, but also their actual queries and index-qualified evidence
IDs. This table shows the measured overlap and any differences. We check the verdicts
against an event manifest kept outside the agent's context, and manually verify that
citations support each factual claim.”

此段仅在真实实验完成后使用。如果只能展示工具测试，应开头说明：
“This is an offline demonstration of the comparison tool, not a completed agent evaluation.”

## 五分钟pitch内容框架

1. 0:00–0:45 Problem: analysts must onboard heterogeneous logs and repeatedly reconstruct evidence.
2. 0:45–1:30 Product: hypothesis-driven investigation with validated schemas and bounded MCP access.
3. 1:30–2:30 Walkthrough: show one source event, query and evidence-backed statement.
4. 2:30–3:30 Evaluation: present actual frozen-run results and explain one meaningful difference.
5. 3:30–4:15 Customer: a proposed MSSP/SOC analyst use case; no validated demand or cost-saving claim.
6. 4:15–5:00 Limits and next step: larger blind scenarios, real collection coverage and analyst validation.

展示材料必须区分 proposed benefit 与 measured result。没有真实计时和对照组时，不声称
节省了多少时间。截图和录屏由团队在完成实验后补入。
