# 基线与留存

W1复用docs/20261123-uvicorn-fixed100/reports/20261123-fixed100/的72组，原始包612文件/SHA84e71ec06ae175199bbfe763fc7c5df0b5f4b08d76b258ee262b7a260219b02e。模型/输入/代码/b/queue/计时/连接策略相同；新W仅日志增加PID且运行时点不同，不是同时间配对，不能作因果或置信区间声明。W1不重跑。

新阶段run_id为uvicorn-workers-fixed100-20261123-w2-r1/w4-r1/w6-r1，已存在拒绝覆盖。服务器私有根/home/zhangs/workspace/vbas-benchmarks；本机/Users/zhangshen/.codex/backups/vbas-benchmark-20261118。保存基线plan指纹、300输入、源配置/副本、模型/manifest指纹、代码bundle、环境、命令/日志/PID拓扑/逐组分配/完整响应/资源/关闭记录。整包源前后相同，本机整包/成员/解包核验；不推照片/完整私有配置/日志/Engine，旧包保留。


W2-r1为预热覆盖保护停止，无正式组，保留不覆盖；正式计划改用各W-r2独立run。原r1调度器未启动W4/W6。
