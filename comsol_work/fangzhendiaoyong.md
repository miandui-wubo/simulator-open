## 仿真调用函数
主要就是tools-lammps.py中的流程，其他用到的都是一样的

if __name__ == "__main__":
    start_time = time.time()
    # Test query
    test_query = "Please help me calculate the density of Ga."
    ######MD######
    lammps_input = test_query
    if lammps_calculate(lammps_input):
        answer = log_analyze(lammps_input)
        print(f'The LAMMPS calculation result is:{answer}')
    else:
        print("LAMMPS calculation failed after all retries. Exiting program.")
        sys.exit(1)  # 非0退出码表示异常退出
    #Calculate and print the total running time of the program
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total running time of the program: {total_time:.2f} seconds")   

test_query 输入要计算的参数
lammps_calculate(lammps_input) 重复生成lammps代码并运行lammps计算，返回True或False
log_analyze(lammps_input) 解析log文件，返回计算结果

具体运行的话主要是用命令行运行：
    combined_command = f'cd /d "{l_path}" && lmp -in {l_name}'
    
    # 运行 LAMMPS 模拟
    result = subprocess.run(combined_command, shell=True, check=True, 
                            capture_output=True, text=True)

