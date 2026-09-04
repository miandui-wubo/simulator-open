import os
from openai import OpenAI
import time
import subprocess
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
def lammps_calculate(query, prompt_path="./prompt/prompt_2_lammps.md", max_retries=10):
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

def log_analyze(query, prompt_path = "./prompt/prompt_lammps_log_analyze.md", log_path="./lammps_simulation/log.lammps"):
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        return call_deepseek_api(prompt_content, log_content+query)
    except Exception as e:
        return f"Error reading log file: {str(e)}"
    
def lammps(query):
    start_time = time.time()
    ######MD######
    lammps_input = query
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
