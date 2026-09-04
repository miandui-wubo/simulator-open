# 定义你的prompt变量
prompt = """Users consult about some information related to droplet simulation experiments, including the purposes of conducting the experiments.
Examples are as follows:
- A drop of gallium is dripped between a silicon substrate at 30°C and a gallium nitride substrate at 40°C. What are the contact angles of the gallium droplet on the surface of the silicon substrate and on the surface of the gallium nitride substrate respectively?
- A drop of Ga₆₈.₅In₂₁.₅Sn₁₀ is dripped between a silicon substrate at 25°C and a gallium nitride substrate at 40°C. What is the ratio of the contact angle of the gallium-based droplet on the surface of the silicon substrate to that on the surface of the gallium arsenide substrate?
**Special Reminder**Only calculations related to contact angle will be categorized under this type; calculations of other parameters will be classified under the "lammps" category."""

prompt_with_backslash_n = prompt.replace("\n", "\\n")
print(prompt_with_backslash_n)