import shutil
import os

def check_command_exists(command: str) -> bool:
    """
    检查系统命令是否存在。
    """
    return shutil.which(command) is not None
