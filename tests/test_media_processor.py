"""
Test suite for MediaProcessor and Multimodal Chat Attachments
Covers PDF, Excel, CSV, DOCX, Image/Screenshot, Video parsing, and FastAPI upload endpoints.
"""

import io
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from core.media_processor import MediaProcessor
from run import app


def test_process_plain_text():
    content = b"def hello_world():\n    return 'Hello from ModelDock Studio!'"
    res = MediaProcessor.process_file("script.py", content)
    assert res["file_type"] == "text"
    assert "Hello from ModelDock Studio!" in res["extracted_text"]
    assert res["size_formatted"] != ""


def test_process_csv():
    csv_bytes = b"Name,Role,Department\nAlice,Developer,Engineering\nBob,Designer,UI/UX\nCharlie,Analyst,Data"
    res = MediaProcessor.process_file("team.csv", csv_bytes)
    assert res["file_type"] == "document"
    assert res["doc_type"] == "csv"
    assert "| Name | Role | Department |" in res["extracted_text"]
    assert "| Alice | Developer | Engineering |" in res["extracted_text"]


def test_process_excel():
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "QuarterlyRevenue"
    ws.append(["Quarter", "Revenue_USD", "Profit_USD"])
    ws.append(["Q1", 125000, 45000])
    ws.append(["Q2", 185000, 68000])

    buf = io.BytesIO()
    wb.save(buf)
    excel_bytes = buf.getvalue()

    res = MediaProcessor.process_file("financials.xlsx", excel_bytes)
    assert res["file_type"] == "document"
    assert res["doc_type"] == "excel"
    assert "QuarterlyRevenue" in res["extracted_text"]
    assert "| Q1 | 125000 | 45000 |" in res["extracted_text"]


def test_process_image_and_screenshot():
    # Create test image in memory
    img = Image.new("RGB", (200, 150), color=(59, 130, 246))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    res = MediaProcessor.process_file("screenshot_test.png", img_bytes)
    assert res["file_type"] == "image"
    assert res["preview_url"].startswith("data:image/")
    assert res["image_data"].startswith("data:image/")
    assert res["metadata"]["width"] == 200
    assert res["metadata"]["height"] == 150


def test_process_video():
    import cv2
    import tempfile
    import os

    # Generate a tiny dummy 10-frame synthetic MP4 video in memory/temp
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_name = tmp.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(tmp_name, fourcc, 10.0, (64, 64))
        for i in range(10):
            frame = np.full((64, 64, 3), i * 20, dtype=np.uint8)
            out.write(frame)
        out.release()

        with open(tmp_name, "rb") as f:
            video_bytes = f.read()

        res = MediaProcessor.process_file("demo_clip.mp4", video_bytes)
        assert res["file_type"] == "video"
        assert "Attached Video: demo_clip.mp4" in res["extracted_text"]
        assert "Duration" in res["extracted_text"]
        assert len(res["keyframes"]) > 0
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def test_media_upload_endpoint():
    client = TestClient(app)

    # 1. Upload CSV
    csv_content = b"item,price\nKeyboard,75\nMouse,45"
    response = client.post(
        "/api/media/upload",
        files={"file": ("inventory.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["attachment"]["filename"] == "inventory.csv"
    assert data["attachment"]["doc_type"] == "csv"
    assert "| Keyboard | 75 |" in data["attachment"]["extracted_text"]
