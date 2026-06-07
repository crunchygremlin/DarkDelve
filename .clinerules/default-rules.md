# Local Agent Protocol (.clinerules)

## VRAM & Context Hygiene Constraints
You are running on a local GTX 1080 Ti with a strict context cap. You must minimize token consumption to prevent GPU memory crashes.
1. NEVER read more than 2 files simultaneously unless explicitly ordered. 
3. Keep all explanations, pleasantries, and code comments to an absolute minimum. Be concise.

## basic plan
- there will be a plan file in the project that explains what to do next. 
- currently that plan file is /home/danny/Code/DarkDelve/LLM_ROGUELIKE_PLAN.md
- if a section of the plan is completed write in the file that that step is completed. 
- exit act mode and wait for instructions. 

## Code & Environment Specifications
- Operating System: Kubuntu (KDE Plasma Desktop)
- Language/Framework: Python backend for a 2D roguelike clone.
- Pathfinding requirements: Explicitly track 2D coordinates `(x, y)` using traditional deterministic logic before applying LLM narrative layers.
-