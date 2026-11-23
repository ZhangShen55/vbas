# 环境与约束

本机/Users/zhangshen/Documents/workspace/vbas，perf；ssh zhangs12，/home/zhangs/workspace/vbas；vbas-trt Python3.11。仅物理GPU1 RTX3090 UUID GPU-8c6b7efd-2b4f-04f3-db71-b50d2482fc49，四件既有TensorRT FP16 Engine及manifest、固定batch1，不改阈值/NMS/模型/依赖。每worker私有b512/q0、外部注册关闭、trace off；SyncTasks2不经过该准入控制。保护jy-tias、其他GPU/服务、驱动、main_910b_npu及用户AGENTS；不部署。

全部GPU阶段串行，持有既有GPU锁；每阶段/每实例组核对目标GPU空闲、独立端口未占用及主机预算8+1.5×模型worker数GiB（W6=17GiB）。记录所有实际模型、管理和发生器进程CPU/RSS，避免旧压力报告遗漏管理脚本的问题。测量提交冻结，阶段中不拉后续文档提交。
