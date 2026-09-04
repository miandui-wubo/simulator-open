=== Project Description ===
This project utilizes intent recognition to implement a multi-agent collaborative system integrating material science domain knowledge Q&A, LAMMPS simulation, and autonomous parameter completion for simulation.

**Chatting Mode**
- Handles conversational dialogue unrelated to experiments, primarily focusing on discussions within the field of multi-agent autonomous simulation.

**LAMMPS Mode**
- Function Description:*Provides LAMMPS users conducting droplet simulations with key material property parameters and simulation setup support.
- Core Capabilities:Queries key material property parameters (such as melting point, surface tension, density, viscosity, thermal conductivity, etc.) and answers questions regarding the methods for setting and obtaining these parameters in LAMMPS.
- Typical Application Scenarios:
"How can I obtain the dynamic viscosity parameters for Gallium?"
"What is the melting point of metallic Gallium?"

**Experiment Mode**
- Function Description: Utilizes COMSOL-MATLAB, combined with the capabilities of Function 2 (LAMMPS Mode), to perform 3D simulation experiments of droplets.
- Core Capabilities: Can autonomously complete parameters based on the user-provided droplet material and substrate material, perform contact angle simulation experiments, and obtain 3D simulation data.
- Typical Application Scenarios:
"A gallium droplet is situated between a 30°C silicon substrate and a 40°C gallium nitride substrate. What are the respective contact angles on these two substrates?"

=== Code Description ===
**Runtime Environment**
- A `requirements.txt` file is provided, containing the specifications for the current environment configuration.

**Execution Method**
- Run the `main.py` file directly within the `lammps_work` environment.

**API Interface Instructions**
- When the agent runs, the `api_key` in `main.py` and in `chatting.py`, `experiment.py`, and `lammps.py` under the `tools` directory needs to be replaced with your personal key.

**File Path Instructions**
- Due to differences in computers and operating system versions, path separator issues (like '\' causing errors) might occur. Generally, replacing them with '/' or '\\' will resolve the problem.
- The two `cd` paths related to the COMSOL-MATLAB software in the `m_run_m` variable within `const_config.py` (located in the `tools` directory) need to be adjusted according to the actual installation directory in your specific working environment.
- In Experiment Mode, the final generated 3D simulation data results are saved in the `comsol_matlab\txtresult` directory.
- The txt_files_path and m_files_path in const. config. py under the tools directory need to be modified to the absolute path of the current folder