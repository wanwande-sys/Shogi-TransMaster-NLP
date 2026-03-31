# utils.py
import subprocess

def format_time(seconds):
    return f"{int(seconds // 3600):02d}:{int((seconds % 3600) // 60):02d}:{seconds % 60:06.3f}"

def extract_urls(text_input, uploaded_file):
    urls = [line.strip() for line in text_input.split('\n') if line.strip()]
    if uploaded_file is not None:
        file_content = uploaded_file.getvalue().decode("utf-8")
        urls.extend([line.strip() for line in file_content.split('\n') if line.strip()])
    return list(dict.fromkeys(urls))

def enforce_line_breaks(vtt_str, is_vertical):
    """智能断句防溢出算法"""
    if not is_vertical: return vtt_str
    lines = vtt_str.split('\n')
    new_lines = []
    for line in lines:
        if '-->' in line or line.startswith('WEBVTT') or not line.strip():
            new_lines.append(line)
        else:
            limit = 16  # 竖排超过16字强制分列
            wrapped = '\n'.join([line[i:i + limit] for i in range(0, len(line), limit)])
            new_lines.append(wrapped)
    return '\n'.join(new_lines)

def get_video_duration(video_path):
    """获取视频总秒数"""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
               'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except:
        return 0.0