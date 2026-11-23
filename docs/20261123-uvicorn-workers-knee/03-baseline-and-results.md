# 基线与留存

W1复用docs/20261123-uvicorn-fixed100/reports/20261123-fixed100/的72组，原始包612文件/SHA84e71ec06ae175199bbfe763fc7c5df0b5f4b08d76b258ee262b7a260219b02e。模型/输入/代码/b/queue/计时/连接策略相同；新W仅日志增加PID且运行时点不同，不是同时间配对，不能作因果或置信区间声明。W1不重跑。

原计划run_id为uvicorn-workers-fixed100-20261123-w2-r1/w4-r1/w6-r1，已存在拒绝覆盖。服务器私有根/home/zhangs/workspace/vbas-benchmarks；本机/Users/zhangshen/.codex/backups/vbas-benchmark-20261118。保存基线plan指纹、300输入、源配置/副本、模型/manifest指纹、代码bundle、环境、命令/日志/PID拓扑/逐组分配/完整响应/资源/关闭记录。整包源前后相同，本机整包/成员/解包核验；不推照片/完整私有配置/日志/Engine，旧包保留。


W2-r1为预热覆盖保护停止，无正式组，保留不覆盖；正式计划改用各W-r2独立run。原r1调度器未启动W4/W6。


正式结果：W2/4/6各-r2均72组7200成功、合计216组21600成功0失败。完整原始包uvicorn-workers-fixed100-checkpoint-20261123-r1含2160文件、329274584字节，SHA256 e3cce039fbcbe45392d81f821a0643bfe4a649297c0ffaa2225014046aee703f；源前后不变、本机整包/成员/解包校验通过。最终采用uvicorn-workers-analysis-local-20261123-r3，summary SHA e82df6a95a1f71fc32cfa9e0b4bd0d8fd97c58d32abbe0af7270cd3bd6bc5d1d，与服务器portable-r2的summary和CSV逐字节一致；第一次CPU比例1 ULP跨Python版本差异保留，math.fsum修正仅用于新派生目录，不改原始记录。派生22文件包uvicorn-workers-artifacts-checkpoint-20261123-r1为736515字节，SHA256 62861111a4d693a5554f91e59a8be23947c29476c9917b048c79755dfc335e84。完整报告记录旧W1包与Engine交接包，保留全部历史结果。


## 追加：W4并发8与16复核（2026-11-23）

原W4-r2 C8/C16三轮作为历史参照不覆盖；本轮C8也重新执行，以本轮18组为直接对照，不将旧C8与新C16混合成配对。输入仍原每接口100张，完整响应/逐PID分配/资源/运行OpenAPI/脚本/环境/配置及Engine哈希独立留存。最终完整整包源前后不变、本机整包/成员/解包核验，日志和图片/完整私有配置不入Git。


追加证据：raw 417文件/82860825字节，SHA df42f6687bfbeca4d382bf93f832cc7ea7eacd5a0e2d1bf90bad5a34b270ce30；artifacts 8文件/16283字节，SHA faacf9d33777ffee58b4fee4bf7870276cace06cf6742348db6f11d4a0fe7889。均源前后不变并本机整包/成员/解包核验，派生另在服务器核验。summary SHA 2f8e758f804527469bd712e158e39fef125393c1d3cc78f611c4942f787360ff，两端独立重算summary/CSV逐字节相同；完整响应去除运行时字段后1800次与旧同后端参照相等，非新准确率验收。旧原始结果未改。
