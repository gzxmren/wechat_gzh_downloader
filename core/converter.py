import html2text
from bs4 import BeautifulSoup
from core.image_handler import download_image

def process_wechat_html(html_content, assets_dir=None, download_images=False):
    """
    预处理 HTML：
    1. 清洗无关内容 (二维码、广告、工具栏)
    2. 解决图片懒加载 (data-src -> src)
    3. (可选) 下载图片并替换为本地路径
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    # --- 0. 内容清洗 (Content Cleaning) ---
    selectors_to_remove = [
        "script",                  # 脚本
        "#js_pc_qr_code",          # 底部二维码 (PC端)
        ".rich_media_tool",        # 底部工具栏 (阅读、点赞)
        "#js_toobar3",             # 底部工具栏容器
        ".rich_media_area_extra",  # 底部额外区域 (推荐阅读等)
        "#js_view_source",         # "阅读原文"链接
        ".reward_area",            # 赞赏区域
        "#js_sponsor_ad_area"      # 广告区域
    ]
    
    for selector in selectors_to_remove:
        for tag in soup.select(selector):
            tag.decompose() # 彻底移除标签

    # 查找正文区域，通常是 js_content
    content_div = soup.find(id="js_content")
    if not content_div:
        content_div = soup # 如果找不到特定容器，就处理整个
    
    # 遍历所有图片
    imgs = content_div.find_all("img")
    # print(f"  [Debug] Converter found {len(imgs)} images in content")
    
    for img in imgs:
        # print(f"    [Debug] Raw img tag: {img}")
        
        # 优先使用 data-src (微信图片的真实地址)
        img_url = img.get("data-src") or img.get("src")
        # print(f"    [Debug] Extracted URL: {img_url}")
        
        if img_url:
            # 如果开启了图片下载且提供了目录
            if download_images and assets_dir:
                # print(f"    -> Downloading: {img_url[:30]}...")
                local_filename = download_image(img_url, assets_dir)
                if local_filename:
                    # 替换为 Markdown 兼容的相对路径
                    # 注意：Markdown 文件和 assets 文件夹在同一级
                    img["src"] = f"assets/{local_filename}"
                else:
                    # 下载失败，保留远程链接
                    img["src"] = img_url
            else:
                # 仅修正 src 属性，不做下载
                img["src"] = img_url
            
            # 清理无用属性以净化 Markdown
            if "data-src" in img.attrs: del img.attrs["data-src"]
            
    return str(content_div)

def html_to_markdown(html_content, title, original_url, assets_dir=None, download_images=False):

    """

    将 HTML 转换为 Markdown 格式，支持本地图片处理。

    

    Returns:

        tuple: (markdown_content, processed_html)

    """

    # 1. 预处理 HTML (含图片下载逻辑)

    processed_html = process_wechat_html(html_content, assets_dir, download_images)

    

    # 2. 配置转换器

    converter = html2text.HTML2Text()

    converter.ignore_links = False

    converter.ignore_images = False

    converter.body_width = 0  

    converter.protect_links = True 

    

    # 3. 转换

    markdown_body = converter.handle(processed_html)

    

    # 4. 添加头部元数据

    final_md = f"# {title}\n\n"

    final_md += f"> 原文链接: {original_url}\n"

    if download_images:

        final_md += f"> 图片状态: 已本地化 (assets/)\n"

    final_md += "\n---\n\n"

    final_md += markdown_body

    

    return final_md, processed_html
