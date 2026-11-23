# 环境与保护

沿用ssh zhangs12、/home/zhangs/workspace/vbas、用户vbas-trt Python、服务代码冻结3f77bfd；本机perf起点1944eaf，与服务器服务源码一致。只用物理GPU1 RTX3090 UUID GPU-8c6b7efd-2b4f-04f3-db71-b50d2482fc49。保留其他GPU/服务、驱动、jy-tias、旧模型和用户AGENTS。

每阶段GPU锁、指定GPU<=100MiB、端口18985未占用、主机可用>=8+1.5*W GiB；W6需17GiB。四Engine FP16、ImageSize640，同manifest/模型SHA，私有副本b512/q0、注册关闭、旧人数接口开启。Uvicorn父进程、所有真实GPU worker及辅助进程分别记录；只终止自身进程组。不升级依赖，不同步测量中代码。
