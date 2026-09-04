prompt = """Users are chatting, which has nothing to do with droplet simulation experiments or LAMMPS parameters/experiments.
Examples are as follows:
- Hello
- Are you a droplet simulation experiment assistant?"""


prompt_with_backslash_n = prompt.replace("\n", "\\n")
print(prompt_with_backslash_n)