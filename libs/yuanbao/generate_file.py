import asyncio
import glob
import os
from urllib.parse import urlparse
import aiofiles
import jsbeautifier
from playwright.async_api import async_playwright


def remove_sourcemap_from_bytes(raw_bytes):
    """直接从 bytes 移除 //# sourceMappingURL= 行"""
    lines = raw_bytes.split(b'\n')  # 按字节分行
    filtered_lines = [
        line for line in lines
        if not line.strip().startswith(b'//# sourceMappingURL=')
    ]
    return b'\n'.join(filtered_lines)


def remove_closure(js_content):
    """移除 IIFE 闭包 (() => { ... })() 或 (function() { ... })()"""
    stripped = js_content.strip()
    # 匹配箭头函数或传统函数闭包
    if (stripped.startswith("(()=>{") and stripped.endswith("})();")) or \
       (stripped.startswith("(function() {") and stripped.endswith("})();")):
        # 提取闭包内部内容（去掉首尾闭包语法）
        inner_start = stripped.find("{") + 1
        inner_end = stripped.rfind("}")
        return stripped[inner_start:inner_end].strip()
    return js_content


async def save_js_files(url, save_dir='libs/yuanbao/static'):
    if os.path.exists(save_dir):
        print(f"目录 {save_dir} 已存在，清空目录...")
        for file in glob.glob(os.path.join(save_dir, '*')):
            if os.path.isfile(file):
                os.remove(file)
    else:
        os.makedirs(save_dir)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        async def handle_response(response):
            if response.request.resource_type == "script" or response.headers.get('content-type', '') == 'application/wasm':
                js_url = response.url
                if 'https://static.yuanbao.tencent.com' not in js_url:
                    return
                
                parsed = urlparse(js_url)
                file_path = os.path.join(save_dir, parsed.path.lstrip('/'))
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                try:
                    raw_bytes = await response.body()
                    
                    # 如果是 wasm 文件，直接保存
                    if '.wasm' in js_url:
                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(raw_bytes)
                    else:
                        raw_bytes = remove_sourcemap_from_bytes(raw_bytes)
                        
                        if 'runtime' in file_path or 'yb_index' in file_path:
                            js_content = raw_bytes.decode('utf-8')
                            if 'runtime' in file_path:
                                js_content = remove_closure(js_content)
                                js_content += '\nmodule.exports = {b, r, t};'
                                js_content = jsbeautifier.beautify(js_content)
                            elif 'yb_index' in file_path:
                                js_content = jsbeautifier.beautify(js_content)

                            async with aiofiles.open(file_path, 'w', encoding="utf-8") as f:
                                await f.write(js_content)
                        else:
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(raw_bytes)
                    
                    print(f"Saved: {file_path}")
                except Exception as e:
                    print(f"Error saving {js_url}: {e}")
        
        page.on('response', handle_response)
        await page.goto(url)
        # input('回车关闭...')
        await page.wait_for_timeout(5000)
        await browser.close()


def generate_import_statements(
        js_dir='js_files',
        output_file='imports.js',
        template_file=None,
        placeholder='/* AUTO_IMPORTS */'):
    # 获取目录下所有js文件
    js_files = glob.glob(os.path.join(js_dir, '*.js'))
    
    # 生成导入语句
    imports = []
    for js_file in js_files:
        filename = os.path.basename(js_file)
        var_name = os.path.splitext(filename)[0].replace('.', '_').replace('-', '_')
        if 'runtime' in filename:
            imports.append(f"runtime = require(`${{dirPath}}/{filename}`);")
        else:
            imports.append(f"var {var_name} = require(`${{dirPath}}/{filename}`);")

    if template_file and os.path.exists(template_file):
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 替换模板中的占位符
        if placeholder in template_content:
            output_content = template_content.replace(placeholder, '\n    '.join(imports))
        else:
            output_content = f"/* 自动生成的导入语句 */\n{'\n'.join(imports)}\n\n{template_content}"
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"Generated {len(imports)} import statements in {output_file}")


if __name__ == '__main__':
    asyncio.run(save_js_files('https://yuanbao.tencent.com/chat/naQivTmsDa'))
    generate_import_statements('libs/yuanbao/static', 'libs/yuanbao/main.js', 'libs/yuanbao/template.js')