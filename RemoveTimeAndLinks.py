import os
import re
import chardet

def remove_time_and_links_from_md(folder_path):
    # 遍历文件夹中的所有 .md 文件
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                content = None
                encoding = None

                # 检测文件编码
                with open(file_path, "rb") as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']

                # 使用检测到的编码读取文件
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                except Exception as e:
                    print(f"无法读取文件 {file_path}，错误: {e}")
                    continue

                # 删除 Markdown 链接格式 [链接文本](链接地址)
                content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", "", content)

                # 删除时间格式，例如 [06:57] 或 00:31
                content = re.sub(r"\[?\d{1,2}:\d{2}\]?", "", content)

                # 使用原始编码写回文件
                try:
                    with open(file_path, "w", encoding=encoding) as f:
                        f.write(content)
                except Exception as e:
                    print(f"无法写入文件 {file_path}，错误: {e}")

if __name__ == "__main__":
    folder_path = os.path.dirname(os.path.abspath(__file__))
    remove_time_and_links_from_md(folder_path)
    print("时间和链接已删除，文件编码已保留。")