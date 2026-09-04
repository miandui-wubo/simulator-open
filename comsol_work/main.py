import os
import json
import importlib
from openai import OpenAI

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

def get_intent(intent_res):
    try:
        intent_dict = json.loads(intent_res) 
        return intent_dict["intent_type"]
    except (json.JSONDecodeError, KeyError) as e:
        return f"Error parsing intent: {str(e)}"

def call_tool(intent_type, query):
    """根据意图类型调用对应的工具函数"""
    # 验证意图类型是否有效
    valid_intents = ["chatting", "lammps", "experiment"]
    if intent_type not in valid_intents:
        return f"Invalid intent type: {intent_type}. Must be one of {valid_intents}"
    
    try:
        # 动态导入对应的工具模块
        tool_module = importlib.import_module(f"tools.{intent_type}")
        
        # 假设每个工具模块中都有一个与模块名相同的主函数
        tool_function = getattr(tool_module, intent_type)
        
        # 调用工具函数并返回结果
        return tool_function(query)
        
    except ImportError:
        return f"Tool module {intent_type}.py not found in tools folder"
    except AttributeError:
        return f"Tool function {intent_type} not found in {intent_type}.py"
    except Exception as e:
        return f"Error calling {intent_type} tool: {str(e)}"

if __name__ == "__main__":
    with open("prompt/prompt_1_intent.md", "r", encoding="utf-8") as f:
        prompt_content = f.read()

    # ##chatting
    # user_input = "Hello!"

    # ##lammps
    # user_input = "Please help me calculate the density of Ga."

    ##experiment
    user_input = "Droplet name：Ga；Droplet density：6095kg/m^3；Droplet dynamic viscosity：0.00181；Left substrate name：Si；Left substrate constant pressure heat capacity：700/(kg*K)；Left substrate thermal conductivity：130；Left substrate density：2329kg/m^3；；Right substrate name：GaN；Right substrate constant pressure heat capacity：492J/(kg*K)；Right substrate density：6150kg/m^3；Right substrate thermal conductivity：180；Left substrate temperature：273.15k，Right substrate temperature：383.15k；Surface tension：0.35N/m；Left substrate contact angle：27.27deg，Right substrate contact angle：13.43deg；Mesh fineness：4.Please help me simulate the contact angles of the gallium droplet on the surface of the silicon substrate and on the surface of the gallium nitride substrate"


    intent_res = call_deepseek_api(prompt_content, user_input)
    print(f"Intent recognition result: {intent_res}")
    
    intent_type = get_intent(intent_res)
    print(f"Determined intent type: {intent_type}")
  
    if isinstance(intent_type, str) and intent_type in ["chatting", "lammps", "experiment"]:
        result = call_tool(intent_type, user_input)
        print(f"Tool result: {result}")
    else:
        print(f"can't handle intent type: {intent_type}")
