import os
from pathlib import Path

# EOS environmental variables
EOS = os.path.join(str(Path.home()), "eos")
EOS_MCP = os.path.join(EOS, "mcp")
if not os.path.exists(EOS_MCP):
    os.makedirs(EOS_MCP)
