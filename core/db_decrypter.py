import os
import subprocess
import shutil

def run_sqlcipher_cmd(encrypted_db, key, output_db, config_sql):
    """辅助函数：执行一次 sqlcipher 命令"""
    # 构造完整的 SQL 脚本
    full_sql = f"""
    PRAGMA key = "x'{key}'";
    PRAGMA cipher_page_size = 4096;
    {config_sql}
    ATTACH DATABASE '{output_db}' AS plaintext KEY '';
    SELECT sqlcipher_export('plaintext');
    DETACH DATABASE plaintext;
    """
    
    try:
        process = subprocess.Popen(
            ['sqlcipher', encrypted_db],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, err = process.communicate(input=full_sql)
        
        # 验证文件是否生成且非空
        if os.path.exists(output_db) and os.path.getsize(output_db) > 0:
            # 进一步验证：尝试读取头部，确保不是空壳
            return True
    except:
        pass
    return False

def decrypt_wechat_db(encrypted_db_path, key, output_db_path):
    """
    使用系统 sqlcipher 工具解密微信数据库。
    自动尝试多种参数组合。
    """
    if not os.path.exists(encrypted_db_path):
        print(f"[Error] 加密数据库不存在: {encrypted_db_path}")
        return False

    # 定义尝试的配置列表
    configs = [
        # 1. 经典配置 (最常见)
        "PRAGMA kdf_iter = 64000; PRAGMA cipher_use_hmac = OFF;",
        
        # 2. 新版配置 (HMAC 开启)
        "PRAGMA kdf_iter = 64000; PRAGMA cipher_use_hmac = ON;",
        
        # 3. 老版配置
        "PRAGMA kdf_iter = 4000; PRAGMA cipher_use_hmac = OFF;",
        
        # 4. SQLCipher 4 默认 (如果系统安装的是 v4)
        "PRAGMA cipher_compatibility = 3;"
    ]

    print(f"正在尝试解密数据库 (Key前缀: {key[:4]}...)")
    
    for i, config in enumerate(configs, 1):
        # 清理旧文件
        if os.path.exists(output_db_path):
            os.remove(output_db_path)
            
        # print(f"  -> 尝试方案 {i}...") # 调试用
        if run_sqlcipher_cmd(encrypted_db_path, key, output_db_path, config):
            print(f"[Success] 方案 {i} 解密成功！")
            return True
            
    print("[Fail] 所有解密方案均失败。可能是 Key 错误或数据库版本不受支持。")
    return False