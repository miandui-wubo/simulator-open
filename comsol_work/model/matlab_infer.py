# import json
# import torch
# import warnings
# from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
# import os

# # 忽略torchvision警告（若不需图像处理）
# warnings.filterwarnings("ignore", message="Failed to load image Python extension")

# class TransformersInference:
#     def __init__(
#         self,
#         model_name_or_path: str,
#         torch_dtype: torch.dtype = torch.float16
#     ):
#         self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
#         self.model = AutoModelForCausalLM.from_pretrained(
#             model_name_or_path,
#             torch_dtype=torch_dtype,
#             trust_remote_code=True
#         ).to("cuda" if torch.cuda.is_available() else "cpu")  # 显式设备分配
        
#         if self.tokenizer.pad_token is None:
#             self.tokenizer.pad_token = self.tokenizer.eos_token

#     def infer(
#         self,
#         sys_central: str, 
#         query_rewrited: str,
#         temperature: float = 1e-7,
#         top_p: float = 0.8,
#         top_k: int = 20,
#         max_new_tokens: int = 4096,
#         repetition_penalty: float = 1,
#     ):    
#         messages = [
#             {"role": "system", "content": sys_central},
#             {"role": "user", "content": query_rewrited.strip()}
#         ]
#         input_str = self.tokenizer.apply_chat_template(
#             messages, tokenize=False, add_generation_prompt=True
#         )
#         inputs = self.tokenizer(
#             input_str, 
#             return_tensors="pt", 
#             return_attention_mask=True
#         ).to(self.model.device)

#         # 显式设置所有关键参数（避免覆盖警告）
#         generation_config = GenerationConfig(
#             temperature=temperature,
#             top_p=top_p,
#             top_k=top_k,
#             max_new_tokens=max_new_tokens,
#             repetition_penalty=repetition_penalty,
#             pad_token_id=self.tokenizer.eos_token_id,
#             eos_token_id=self.tokenizer.eos_token_id,
#             bos_token_id=getattr(self.tokenizer, 'bos_token_id', 1),  # 显式定义
#             do_sample=temperature > 1e-6
#         )

#         outputs = self.model.generate(
#             **inputs,
#             generation_config=generation_config
#         )
        
#         full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
#         start_marker = "<|im_start|>assistant\n"
#         start_idx = full_text.rfind(start_marker) + len(start_marker)
#         pred = full_text[start_idx:].split("<|im_end|>", 1)[0].strip()
#         return pred

# # 初始化模型
# inference_engine = TransformersInference(
#     model_name_or_path=os.path.abspath("./model/matlab_checkpoint-39"),
#     torch_dtype=torch.float16
# )

# # 文件处理（添加进度监控
# # input_jsonl_path = "E:/MATLAB_test_data_qy.jsonl"
# # output_jsonl_path = "E:/new_infer_result_2_en.jsonl"
# input_jsonl_path = "./model/matlab_input.jsonl"  # 输入文件路径
# output_jsonl_path = "./model/matlab_output.jsonl"  # 输出文件路径


# print(f"Processing {input_jsonl_path}...")
# with open(input_jsonl_path, "r", encoding="utf-8") as fin, \
#      open(output_jsonl_path, "w", encoding="utf-8") as fout:

#     for idx, line in enumerate(fin):
#         try:
#             if not line.strip():  # 跳过空行
#                 continue
#             data = json.loads(line)
#             response = inference_engine.infer(
#                 sys_central=data.get("instruction", ""),
#                 query_rewrited=data.get("input", "")
#             )
#             output_data = {
#                 "predict": response,
#                 "label": data.get("output", "")
#             }
#             fout.write(json.dumps(output_data, ensure_ascii=False) + "\n")
#             fout.flush()
            
#             # 每10条打印一次进度
#             if idx % 10 == 0:
#                 print(f"Processed {idx+1} lines...")
                
#         except Exception as e:
#             print(f"Error in line {idx}: {str(e)}")
#             continue

# print(f"Processing complete. Results saved to {output_jsonl_path}")


import json
import torch
import warnings
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import os

# 忽略torchvision警告（若不需图像处理）
warnings.filterwarnings("ignore", message="Failed to load image Python extension")

class TransformersInference:
    def __init__(
        self,
        model_name_or_path: str,
        torch_dtype: torch.dtype = torch.float16
    ):
        # 处理路径：转换为绝对路径+正斜杠，避免Windows反斜杠问题
        model_path = os.path.abspath(model_name_or_path).replace("\\", "/")
        # 检查路径是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
        
        # 加载分词器：添加local_files_only=True强制本地加载
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            local_files_only=True,  # 关键参数：跳过Hub仓库校验
            # trust_remote_code=True  # 若模型有自定义代码，需要这个参数
        )
        
        # 加载模型：同样添加local_files_only=True
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch_dtype,
            trust_remote_code=True,
            local_files_only=True,  # 关键参数：强制本地加载
            device_map="auto"  # 自动分配设备（比手动to()更智能）
        )
        
        # 设置pad_token（如果未定义）
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def infer(
        self,
        sys_central: str, 
        query_rewrited: str,
        temperature: float = 1e-7,
        top_p: float = 0.8,
        top_k: int = 20,
        max_new_tokens: int = 4096,
        repetition_penalty: float = 1,
    ):    
        messages = [
            {"role": "system", "content": sys_central},
            {"role": "user", "content": query_rewrited.strip()}
        ]
        input_str = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(
            input_str, 
            return_tensors="pt", 
            return_attention_mask=True
        ).to(self.model.device)

        # 显式设置所有关键参数
        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_new_tokens=max_new_tokens,
            repetition_penalty=repetition_penalty,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            bos_token_id=getattr(self.tokenizer, 'bos_token_id', 1),
            do_sample=temperature > 1e-6
        )

        outputs = self.model.generate(
            **inputs,
            generation_config=generation_config
        )
        
        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        start_marker = "<|im_start|>assistant\n"
        start_idx = full_text.rfind(start_marker) + len(start_marker)
        pred = full_text[start_idx:].split("<|im_end|>", 1)[0].strip()
        return pred

# 初始化模型：检查路径是否有冗余的model目录（关键！）
# 原路径可能多了一层model，根据实际目录结构修改
inference_engine = TransformersInference(
    # 若实际路径是./model/matlab_checkpoint-39，则保持如下
    # 若实际路径是./matlab_checkpoint-39，则改为"./matlab_checkpoint-39"
    model_name_or_path="./matlab_checkpoint-39",
    torch_dtype=torch.float16
)

# 文件处理
input_jsonl_path = "./matlab_input.jsonl"  # 输入文件路径
output_jsonl_path = "./matlab_output.jsonl"  # 输出文件路径


print(f"Processing {input_jsonl_path}...")
with open(input_jsonl_path, "r", encoding="utf-8") as fin, \
     open(output_jsonl_path, "w", encoding="utf-8") as fout:

    for idx, line in enumerate(fin):
        try:
            if not line.strip():  # 跳过空行
                continue
            data = json.loads(line)
            response = inference_engine.infer(
                sys_central=data.get("instruction", ""),
                query_rewrited=data.get("input", "")
            )
            output_data = {
                "predict": response,
                "label": data.get("output", "")
            }
            fout.write(json.dumps(output_data, ensure_ascii=False) + "\n")
            fout.flush()
            
            # 每10条打印一次进度
            if idx % 10 == 0:
                print(f"Processed {idx+1} lines...")
                
        except Exception as e:
            print(f"Error in line {idx}: {str(e)}")
            continue

print(f"Processing complete. Results saved to {output_jsonl_path}")
