===项目说明==
本项目基于意图识别，实现了一个集材料领域知识问答、lammps仿真、自主参数补全仿真的多agent协同体。

**chatting模式**
- 处理与实验无关的交流对话，主要围绕多agent自主仿真领域展开对话。

**lammps模式**
- 功能描述：为进行液滴模拟的LAMMPS用户提供关键的物性参数与模拟设置支持。
- 核心能力：提供关键物性参数（如熔点、表面张力、密度、粘度、热导率等）的查询，并解答相关参数在LAMMPS中的设置方法与获取途径。
- 典型应用场景：
“如何获取镓的动态粘度参数？”
“金属镓的熔点是多少？”

**experiment模式**
- 功能描述：基于Comsol-Matlab， 结合功能2 lammps 模式 完成液滴三维仿真实验
- 核心能力：能够根据用户提供的液滴材料、基板材料等，进行参数补全，完成接触角仿真实验，获得三维仿真数据。
- 典型应用场景：
“一滴镓液滴介于30°C的硅基板和40°C的氮化镓基板之间，其在两种基板上的接触角分别是多少？”

===代码说明===
**运行环境**
- 提供了requirements.txt文档，包含当前环境配置说明

**运行方式**
- 在lammps_work环境下直接运行main.py文件即可

**API接口说明**
- agent运行时，需要把 main.py 以及tools目录下的chatting.py 、 experiment.py 以及 lammps.py 中的api_key换成个人的

**文件路径说明**
- 由于电脑及操作系统版本的差异，可能会出现‘\’转移出错的问题，一般换成‘/’或者‘\\’即可解决
- tools目录下的 const_config.py 中的 m_run_m 变量中的两个cd后有关COMSOL-MATLAB软件的路径需要根据具体工作环境下的安装目录进行调整
- experiment模式中最后生成仿真三维数据结果保存在 comsol_matlab\txtresult 目录下
- tools目录下的 const_config.py 中的 txt_files_path 以及 m_files_path 需要修改为当前文件夹的绝对路径
