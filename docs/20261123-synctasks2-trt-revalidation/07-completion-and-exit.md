# 完成与退出

确认范围为现行TRT，不包括PT、旧30分钟稳态、C256、加密部署或C++。工作完成须105个性能窗口、功能/全量业务、统计/失败/实际PID资源和清理、中文报告/图表/文档索引、完整原始备份和本机逐文件核验齐备，提交perf且干净。预算跳过/未知失败或缺资源不能当矩阵完成；可形成不推荐/无收益有限结论，不改阈值或无限重跑。

不部署/合并，不删除历史报告/模型/旧环境；全部任务服务关闭、端口和真实进程/目标GPU空闲核对，不影响其他服务。本次确认范围的工作已完成；原历史PT/长稳/C256及旧管理采样限制不据此改写。

完成证据：[最终报告](reports/20261123-current-trt/report.md)、[独立QA](reports/20261123-current-trt/qa.json)、[文档对应表](08-document-impact-index.md)。105性能窗口全部执行；固定9600零失败，压力41543成功/1读取失败及全部可达异常链保留；2162全量业务一致、1002功能调用符合预期，31份运行schema相同。固定100最快W6/C8，资源取舍W2/C8；持续压力最高零失败点I4/C50为26.28图/秒，低并发持续窗口拐点未由此网格定位。模型/原配置/完整池不变。没有生产延迟SLO、实际视频到达/30分钟长稳或新PT框级复测，不宣称生产峰值/真实准确率/部署验收。

原始包：服务器/home/zhangs/workspace/vbas-benchmarks/sync-trt-revalidation-checkpoint-20261123-r1，本机/Users/zhangshen/.codex/backups/vbas-benchmark-20261118/同名目录；3516文件/795366761字节，SHA d84a3bc493bd6e37573b3c5413582c93f9fef071081f80ff26c8751296df7319，源前后不变，整包/全部成员/解包后核验通过。两端私有summary SHA d0704f5f87ad0c6b6729fb423194f036ea5890e6385c5ac4a3c5a341824f9ad1，逐字节相等。派生交接包sync-trt-revalidation-artifacts-checkpoint-20261123-r1保存报告/脚本/图表/QA及验证记录，整包/成员校验另见同名私有package-result/local-verification。源代码bundle及四Engine关联已保留；Engine复用原完整handoff备份并核对SHA。

清理：331个已采PID按start_ticks核对、原父及接续父退出，七个独立端口关闭，指定GPU连续三次3MiB/0%。原启动bind errno98保留，只从未启动阶段接续，不覆盖已完成轮；没有对其他服务发信号、改驱动或部署。启动/停止及历史串行整版回退见最终报告与RUNNING.md，不自动切换。

最终交付为perf分支本目录报告提交及其文档交接提交，使用`git log -1 --format=%H -- docs/20261123-synctasks2-trt-revalidation/`定位；测量提交固定9b2884997bd9dd0c6b83d6b4e75e99d9f1aa24d7。提交推送后核对工作区干净；不重建定时任务、不归档聊天。
