prompt = """Users consult about some experimental questions related to LAMMPs, such as the acquisition of xx parameter, the setting of xx parameter, etc.
**Important LAMMPS Parameters**: temperature, surface tension, density, heat capacity at constant pressure, dynamic viscosity, thermal conductivity, melting point, etc.
Examples are as follows:
- How to obtain the xx parameter?
- How to set the xx parameter to yyy?
- What is the melting point of gallium?"""

prompt_with_backslash_n = prompt.replace("\n", "\\n")
print(prompt_with_backslash_n)