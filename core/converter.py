import html2text
import asyncio
from bs4 import BeautifulSoup
from core.image_handler import download_image

async def process_wechat_html(html_content, assets_dir=None, download_images=False, session=None):
    """
    异步预处理 HTML：
    1. 清洗无关内容 (二维码、广告、工具栏)
    2. 解决图片懒加载 (data-src -> src)
    3. (并行) 下载图片并替换为本地路径
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
            tag.decompose()

    content_div = soup.find(id="js_content")
    if not content_div:
        content_div = soup
    
    imgs = content_div.find_all("img")
    
    # 提取所有有效的图片 URL
    img_tasks = []
    img_nodes = []
    
    for img in imgs:
        img_url = img.get("data-src") or img.get("src")
        if img_url:
            img_nodes.append((img, img_url))
            if download_images and assets_dir:
                # 仅在需要下载时创建任务
                img_tasks.append(download_image(img_url, assets_dir, session=session))
            else:
                # 仅修正 src 属性
                img["src"] = img_url
                if "data-src" in img.attrs: del img.attrs["data-src"]

    # 并行下载图片
    if img_tasks:
        results = await asyncio.gather(*img_tasks)
        
        # 将下载结果映射回 HTML 节点
        for (img, img_url), local_filename in zip(img_nodes, results):
            if local_filename:
                img["src"] = f"assets/{local_filename}"
            else:
                img["src"] = img_url
            if "data-src" in img.attrs: del img.attrs["data-src"]
            
    return str(content_div)

async def html_to_markdown(html_content, title, original_url, assets_dir=None, download_images=False, session=None):
    """
    异步将 HTML 转换为 Markdown 格式。
    """
    # 1. 预处理 HTML (异步并行下载图片)
    processed_html = await process_wechat_html(html_content, assets_dir, download_images, session=session)
    
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