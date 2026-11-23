# 环境与保护

本机/服务器仓库沿用vbas，分支perf。本机起点c36fe02，服务器冻结3f77bfd；两者服务代码相同，后续只提交文档，不在测量中pull。服务器/home/zhangs/workspace/vbas；环境/home/zhangs/.conda/envs/vbas-trt；私有根/home/zhangs/workspace/vbas-benchmarks。

唯一GPU UUID GPU-8c6b7efd-2b4f-04f3-db71-b50d2482fc49，物理GPU1 RTX3090。FP16四Engine从项目model加载，教师ImageSize640。启动前校验manifest/四Engine、配置、代码、图片池SHA；要求GPU<=100MiB、主机可用>=9.5GiB、端口18985空闲、独占本任务GPU锁且没有既有benchmark进程。不碰GPU0/其他服务、jy-tias、驱动、main_910b_npu。

私有副本配置关闭注册、开启旧人数路由、b512/q0，不覆盖源config.toml。直接Uvicorn --workers 1 --host127.0.0.1，无reload/Nginx/benchmark包装入口。保留全部模型、旧报告/备份及用户AGENTS.md。不安装升级运行库。
