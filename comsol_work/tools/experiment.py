import os
from openai import OpenAI
import tools.const_config as cc
import subprocess
import json
import time
import ast
import sys

def call_deepseek_api(prompt, text_input):
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text_input},
            ],
            stream=False
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error occurred during API call: {str(e)}"
    
def save_code_to_file(code_content, filename):
    """将生成的代码保存到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(code_content)
        print(f"The code has been successfully saved to: {filename}")
        return True
    except Exception as e:
        print(f"Error while saving file: {e}")
        return False

def experiment_main(query, prompt_path="./prompt/prompt_3_ experiment.md"):
    try:
        # Read system prompt from file
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        
        # Call the core API function
        return call_deepseek_api(prompt_content, query)
        
    except Exception as e:
        return f"Error reading prompt file: {str(e)}"
    
def log_analyze(query, prompt_path = "./prompt/prompt_lammps_log_analyze.md", log_path="./lammps_simulation/log.lammps"):
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        return call_deepseek_api(prompt_content, log_content+query)
    except Exception as e:
        return f"Error reading log file: {str(e)}"
    
# def lammps_calculate(query, prompt_path="./prompt/prompt_3_exp_lammps_calculate.md"):
#     try:
#         # Read system prompt from file
#         with open(prompt_path, "r", encoding="utf-8") as f:
#             prompt_content = f.read()
        
#         # Call the core API function
#         lammps_code = call_deepseek_api(prompt_content, query)
#         save_code_to_file(lammps_code, "./lammps_simulation/simulation.in")
#         l_path, l_name = "./lammps_simulation", "simulation.in"
#         combined_command = f'cd /d "{l_path}" && lmp -in {l_name}'
#         subprocess.run(combined_command, shell=True, check=True)  
#         print('success')
#         input()  
#         # return log_analyze(query)
#         return True

def lammps_calculate(query, prompt_path="./prompt/prompt_3_exp_lammps_calculate.md", max_retries=10):
    try:
        # Read system prompt from file
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        
        current_query = query  # 保存当前查询
        
        # 添加重试机制
        for attempt in range(max_retries):
            try:
                # Call the core API function
                lammps_code = call_deepseek_api(prompt_content, current_query)
                save_code_to_file(lammps_code, "./lammps_simulation/simulation.in")
                l_path, l_name = "./lammps_simulation", "simulation.in"
                combined_command = f'cd /d "{l_path}" && lmp -in {l_name}'
                
                # 运行 LAMMPS 模拟
                result = subprocess.run(combined_command, shell=True, check=True, 
                                      capture_output=True, text=True)
                print('LAMMPS simulation completed successfully')
                
                # 如果运行成功，跳出循环
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"LAMMPS simulation failed on attempt {attempt + 1}/{max_retries}")
                print(f"Error output: {e.stderr}")
                
                # 如果不是最后一次尝试，重新生成代码
                if attempt < max_retries - 1:
                    print("Regenerating LAMMPS code...")
                    # 添加错误信息到查询中，帮助模型生成更好的代码
                    error_context = f"Previous LAMMPS code failed with error: {e.stderr}. Please generate corrected LAMMPS code."
                    current_query = f"{query}\n\nError context: {error_context}"
                else:
                    # 最后一次尝试也失败了
                    print(f"All {max_retries} attempts failed. Last error: {e.stderr}")
                    return False
                    
            except Exception as e:
                print(f"Unexpected error in LAMMPS calculation on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    # 添加错误信息到查询中
                    error_context = f"Previous attempt failed with error: {str(e)}. Please generate corrected LAMMPS code."
                    current_query = f"{query}\n\nError context: {error_context}"
                else:
                    return False
        
    except Exception as e:
        return f"Error reading prompt file: {str(e)}" 
    
def para_extract(query, prompt_path="prompt\prompt_3_exp_para_extract.md"):
    try:
        # Read system prompt from file
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        
        # Call the core API function
        return call_deepseek_api(prompt_content, query)
        
    except Exception as e:
        return f"Error reading prompt file: {str(e)}"
    
def para_judge(user_query: dict):
    """
    Judge whether all parameters are provided.
    If all parameters are provided, return True.
    Otherwise, return a dictionary containing Droplet_Name, Left/Right_Substrate_Material_Name, and the name of the first None parameter.
    """
    # If user_query is a string, try to parse it as JSON
    if isinstance(user_query, str):
        try:
            # user_query = json.loads(user_query)
            user_query = ast.literal_eval(user_query)
        except json.JSONDecodeError as e:
            return f"Error: 无法解析 user_query 为 JSON 格式。详细信息: {str(e)}"

    # Check if user_query is a dictionary
    if not isinstance(user_query, dict):
        return "Error: user_query 必须是 dict 或 JSON 字符串。"

    # Check if all parameters are provided
    missing_key = next((key for key, value in user_query.items() if value is None), None)
    
    if missing_key is None:
        return {"status": True}
    else:
        return {
            "status": False,
            "Droplet_Name": user_query.get("Droplet_Name"),
            "Left_Substrate_Material_Name": user_query.get("Left_Substrate_Material_Name"),
            "Right_Substrate_Material_Name": user_query.get("Right_Substrate_Material_Name"),
            "Missing_Parameter": missing_key
        }
    
def FEM_model_infer(model_input):
    """
    Simulate a FEM model inference process.
    """
    # 构造 JSON 数据（input 字段存储 model_input）
    json_data = {"instruction":cc.model_instruct, "input": model_input}
    
    # 转换为 JSON 字符串（确保非 ASCII 字符正确编码）
    json_line = json.dumps(json_data, ensure_ascii=False)
    
    # 写入文件（追加模式，自动创建目录需提前确保 model 目录存在）
    with open("./model/matlab_input.jsonl", "w", encoding="utf-8") as f:
        f.write(json_line + "\n")
    print("json")
    script_path = "./model"
    script_name = "matlab_infer.py"
    # 构建命令：切换到脚本目录，然后用python执行脚本
    combined_command = f'cd /d "{script_path}" && python "{script_name}"'
    # 执行命令
    subprocess.run(combined_command, shell=True, check=True)
    with open("./model/matlab_output.jsonl", encoding='utf-8') as f:
        model_output = json.loads(f.readline())['predict']
        print (model_output)
    return model_output

def run_matlab_script(m_path, m_name):
    combined_command = f'cd /d "{m_path}" && matlab -nodesktop -nosplash -r "{m_name}; exit"'
    subprocess.run(combined_command, shell=True, check=True)

def experiment(query):
    start_time = time.time()
    user_query = para_extract(query)
    print(user_query)
    flag = para_judge(user_query)["status"]
    # print(flag)
    # input()
    ######MD######
    while not flag:
        Droplet_Name, Left_Substrate_Material_Name, Right_Substrate_Material_Name,  Missing_Parameter = para_judge(user_query)["Droplet_Name"], para_judge(user_query)["Left_Substrate_Material_Name"], para_judge(user_query)["Right_Substrate_Material_Name"], para_judge(user_query)["Missing_Parameter"]
        lammps_input = f"Droplet name is {Droplet_Name}, Left Substrate Material Name is {Left_Substrate_Material_Name}, Right Substrate Material Name is {Right_Substrate_Material_Name}, Please help me calculate {Missing_Parameter}"
        print(lammps_input)
        if lammps_calculate(lammps_input):
            tmp_query = log_analyze(lammps_input)
        else:
            print("LAMMPS calculation failed after all retries. Exiting program.")
            sys.exit(1)  # 非0退出码表示异常退出
        user_query += tmp_query
        flag = para_judge(user_query)["status"]
 
    ######FEM######
    print("Complete material parameters, conduct MATLAB simulation")
    matlab_input = experiment_main(user_query)
    print(matlab_input)
    print(type(matlab_input))
    for i in range(len(matlab_input)): 
        model_output = FEM_model_infer(matlab_input)
        print(model_output)
        suffix = "matlabcode" + str(i) 
        suffix_txt = "simulation_result" + str(i)
        m_code = cc.matlab_code1 + model_output + cc.matlab_code2
        m_code = m_code.replace("xxxxxxxxxxxx", cc.txt_files_path + "\\" + suffix_txt)
        m_path = cc.m_files_path + "\\" + suffix + ".m"
        with open(m_path, 'w') as f:
            f.write(m_code)
        core_m_code = cc.m_run_m.replace('xxxxxxxx',suffix)
        with open(cc.m_files_path + "\\core.m", 'w') as f:
            f.write(core_m_code)
        run_matlab_script(cc.m_files_path, "core")    

    print(f"All simulation experiments have been completed. Simulation data has been saved to {cc.m_files_path}.")
    #Calculate and print the total running time of the program
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total running time of the program: {total_time:.2f} seconds")     


if __name__ == "__main__":
    start_time = time.time()
    # Droplet density：6095kg/m^3；
    test_query = "Droplet name：Ga；Droplet dynamic viscosity：0.00181；Left substrate name：Si；Left substrate constant pressure heat capacity：700/(kg*K)；Left substrate thermal conductivity：130；Left substrate density：2329kg/m^3；；Right substrate name：GaN；Right substrate constant pressure heat capacity：492J/(kg*K)；Right substrate density：6150kg/m^3；Right substrate thermal conductivity：180；Left substrate temperature：273.15K-283.15k，Right substrate temperature：373.15K-383.15k；Surface tension：0.35N/m；Left substrate contact angle：27.27deg，Right substrate contact angle：13.43deg；Mesh fineness：4"

    user_query = para_extract(test_query)
    print(user_query)
    flag = para_judge(user_query)["status"]
    # print(flag)
    # input()
    ######MD######
    while not flag:
        Droplet_Name, Left_Substrate_Material_Name, Right_Substrate_Material_Name,  Missing_Parameter = para_judge(user_query)["Droplet_Name"], para_judge(user_query)["Left_Substrate_Material_Name"], para_judge(user_query)["Right_Substrate_Material_Name"], para_judge(user_query)["Missing_Parameter"]
        lammps_input = f"Droplet name is {Droplet_Name}, Left Substrate Material Name is {Left_Substrate_Material_Name}, Right Substrate Material Name is {Right_Substrate_Material_Name}, Please help me calculate {Missing_Parameter}"
        print(lammps_input)
        if lammps_calculate(lammps_input):
            tmp_query = log_analyze(lammps_input)
        else:
            print("LAMMPS calculation failed after all retries. Exiting program.")
            sys.exit(1)  # 非0退出码表示异常退出
        user_query += tmp_query
        flag = para_judge(user_query)["status"]
 
    ######FEM######
    print("Complete material parameters, conduct MATLAB simulation")
    matlab_input = experiment_main(user_query)
    print(matlab_input)
    print(type(matlab_input))
    for i in range(len(matlab_input)): 
        model_output = FEM_model_infer(matlab_input)
        print(model_output)
        suffix = "matlabcode" + str(i) 
        suffix_txt = "simulation_result" + str(i)
        m_code = cc.matlab_code1 + model_output + cc.matlab_code2
        m_code = m_code.replace("xxxxxxxxxxxx", cc.txt_files_path + "\\" + suffix_txt)
        m_path = cc.m_files_path + "\\" + suffix + ".m"
        with open(m_path, 'w') as f:
            f.write(m_code)
        core_m_code = cc.m_run_m.replace('xxxxxxxx',suffix)
        with open(cc.m_files_path + "\\core.m", 'w') as f:
            f.write(core_m_code)
        run_matlab_script(cc.m_files_path, "core")   

    print(f"All simulation experiments have been completed. Simulation data has been saved to {cc.m_files_path}.")
    #Calculate and print the total running time of the program
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total running time of the program: {total_time:.2f} seconds")        
        
