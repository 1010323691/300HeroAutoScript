"""抓取游戏窗口客户区截图到 captures/，用于制作模板。用法: python grab.py name"""
import sys, os
import cv2
from game import capture_client

img, _ = capture_client()
out = os.path.join(os.path.dirname(__file__), "captures")
os.makedirs(out, exist_ok=True)
p = os.path.join(out, (sys.argv[1] if len(sys.argv) > 1 else "shot") + ".png")
import vision; vision.imwrite(p, img)
print(p, img.shape)
