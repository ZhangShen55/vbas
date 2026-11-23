# 基线与证据

旧串行：3f77bfd，固定100 W1/W2/4/6、W4 C8/C16、压力九点、功能/全量audit参考均保留；最近并行改造f549db0九组仅检查点，不替代本次完整96组。现行服务变化仅SyncTasks2同ROI双模型线程并行，多ROI顺序和模型参数/响应保持。

所有阶段使用独立run_id（sync-trt-revalidation-20261123-r1主索引及各阶段独立目录），存在即拒绝覆盖。记录计划/代码/配置/模型/数据/脚本SHA、实际命令/进程拓扑、原始响应/请求、资源/事件/异常/清理。服务器/home/zhangs/workspace/vbas-benchmarks，本机/Users/zhangshen/.codex/backups/vbas-benchmark-20261118。阶段静止后整包源前后不变，本机整包/全部成员/解包核验；不将照片/完整配置/日志/密钥/Engine入Git，不改旧备份。派生统计由本机原始记录独立重算，图表检查数据与视觉。

受影响文档索引覆盖20261123-uvicorn-fixed100、20261123-uvicorn-workers-knee、20261120-trt-concurrency-knee、20261123-sync-model-parallel及迁移/原优化任务中人数相关引用；旧PT/模型级精度/加密/一次性C256保留对应版本，不用当前性能结果改写。新报告区分本轮、历史串行与小规模并行检查点，单张时延与吞吐摊销分别统计；每路2帧只折算，不称实际视频长稳路数。
