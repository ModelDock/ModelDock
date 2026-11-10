"""
ModelDock Studio - Media & Document Processor
Parses documents (PDF, Excel, CSV, DOCX, Text), images/screenshots, and video files
for multimodal chat interaction.
"""

import os
import io
import csv
import base64
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image

# Temporary upload staging folder
CURRENT_DIR = Path(__file__).resolve().parent.parent
MEDIA_UPLOAD_DIR = CURRENT_DIR / "downloads" / "uploads"
MEDIA_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class MediaProcessor:
    @staticmethod
    def process_file(filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Detect file type and parse text/data/frames.
        Returns a structured dictionary with preview, extracted text, and metadata.
        """
        ext = Path(filename).suffix.lower()
        size_bytes = len(file_bytes)
        size_formatted = MediaProcessor._format_size(size_bytes)
        attachment_id = f"att_{uuid.uuid4().hex[:10]}"

        # 1. Image Files & Screenshots
        if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
            return MediaProcessor._process_image(attachment_id, filename, file_bytes, size_formatted)

        # 2. PDF Documents
        elif ext == ".pdf":
            return MediaProcessor._process_pdf(attachment_id, filename, file_bytes, size_formatted)

        # 3. Excel Spreadsheets
        elif ext in {".xlsx", ".xls"}:
            return MediaProcessor._process_excel(attachment_id, filename, file_bytes, size_formatted)

        # 4. CSV Tabular Data
        elif ext == ".csv":
            return MediaProcessor._process_csv(attachment_id, filename, file_bytes, size_formatted)

        # 5. Microsoft Word Documents
        elif ext in {".docx", ".doc"}:
            return MediaProcessor._process_docx(attachment_id, filename, file_bytes, size_formatted)

        # 6. Video Files
        elif ext in {".mp4", ".mkv", ".avi", ".mov", ".webm"}:
            return MediaProcessor._process_video(attachment_id, filename, file_bytes, size_formatted)

        # 7. Plain Text / Code / Markdown
        elif ext in {".txt", ".md", ".json", ".py", ".js", ".html", ".css", ".xml", ".yaml", ".yml", ".log", ".sql", ".sh"}:
            return MediaProcessor._process_text_file(attachment_id, filename, file_bytes, size_formatted)

        else:
            # Fallback text decoder
            try:
                text_content = file_bytes.decode("utf-8", errors="replace")
                return {
                    "id": attachment_id,
                    "filename": filename,
                    "file_type": "text",
                    "size_formatted": size_formatted,
                    "preview_url": "",
                    "extracted_text": f"### Document: {filename}\n```text\n{text_content[:8000]}\n```",
                    "metadata": {"type": "raw_text"},
                }
            except Exception:
                return {
                    "id": attachment_id,
                    "filename": filename,
                    "file_type": "unknown",
                    "size_formatted": size_formatted,
                    "preview_url": "",
                    "extracted_text": f"[Attached File: {filename} ({size_formatted})]",
                    "metadata": {},
                }

    @staticmethod
    def _process_image(attachment_id: str, filename: str, file_bytes: bytes, size_formatted: str) -> Dict[str, Any]:
        """Process image or pasted screenshot."""
        try:
            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size
            img_format = img.format or "PNG"

            # Resize thumbnail for UI preview
            thumb = img.copy()
            thumb.thumbnail((120, 120))
            thumb_buffer = io.BytesIO()
            thumb.save(thumb_buffer, format="JPEG" if thumb.mode == "RGB" else "PNG")
            thumb_b64 = base64.b64encode(thumb_buffer.getvalue()).decode("utf-8")
            preview_url = f"data:image/jpeg;base64,{thumb_b64}"

            # High resolution image for vision models (limit to 1280px max dim for RAM/VRAM speed)
            max_dim = 1280
            if width > max_dim or height > max_dim:
                img.thumbnail((max_dim, max_dim))
                res_buffer = io.BytesIO()
                img.save(res_buffer, format="JPEG" if img.mode == "RGB" else "PNG", quality=85)
                full_b64 = base64.b64encode(res_buffer.getvalue()).decode("utf-8")
            else:
                full_b64 = base64.b64encode(file_bytes).decode("utf-8")

            image_url = f"data:image/jpeg;base64,{full_b64}"

            extracted_text = (
                f"[Attached Image / Screenshot: {filename} | Resolution: {width}x{height} | Size: {size_formatted}]\n"
                f"Image Description & Context: This user attached an image with filename '{filename}'."
            )

            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "image",
                "size_formatted": size_formatted,
                "preview_url": preview_url,
                "image_data": image_url,
                "extracted_text": extracted_text,
                "metadata": {
                    "width": width,
                    "height": height,
                    "format": img_format,
                },
            }
        except Exception as e:
            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "image",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": f"[Image attachment: {filename} (Error processing: {str(e)})]",
                "metadata": {"error": str(e)},
            }

    @staticmethod
    def _process_pdf(attachment_id: str, filename: str, file_bytes: bytes, size_formatted: str) -> Dict[str, Any]:
        """Extract text and metadata from PDF document."""
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            num_pages = len(reader.pages)
            extracted_pages = []

            # Extract up to first 25 pages to prevent prompt overflow
            max_pages = min(25, num_pages)
            for idx in range(max_pages):
                page_text = reader.pages[idx].extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(f"--- Page {idx + 1} ---\n{page_text.strip()}")

            full_text = "\n\n".join(extracted_pages)
            if num_pages > max_pages:
                full_text += f"\n\n[... Note: PDF has {num_pages} total pages. Showing first {max_pages} pages.]"

            prompt_content = (
                f"### Attached PDF Document: {filename} ({num_pages} pages, {size_formatted})\n"
                f"```text\n{full_text}\n```"
            )

            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "pdf",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": prompt_content,
                "metadata": {"pages": num_pages},
            }
        except Exception as e:
            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "pdf",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": f"[PDF attachment: {filename} (Error parsing text: {str(e)})]",
                "metadata": {"error": str(e)},
            }

    @staticmethod
    def _process_excel(attachment_id: str, filename: str, file_bytes: bytes, size_formatted: str) -> Dict[str, Any]:
        """Extract spreadsheets into formatted Markdown tables."""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            sheet_summaries = []

            for sheet_name in wb.sheetnames[:5]:  # Limit to first 5 sheets
                sheet = wb[sheet_name]
                rows = list(sheet.iter_rows(values_only=True))
                if not rows:
                    continue

                # Format as markdown table (limit to first 50 rows)
                table_lines = [f"#### Sheet: {sheet_name}"]
                headers = [str(c) if c is not None else "" for c in rows[0]]
                table_lines.append("| " + " | ".join(headers) + " |")
                table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

                for row in rows[1:51]:
                    row_vals = [str(c) if c is not None else "" for c in row]
                    table_lines.append("| " + " | ".join(row_vals) + " |")

                if len(rows) > 51:
                    table_lines.append(f"\n*(Showing 50 of {len(rows)} rows from sheet '{sheet_name}')*")

                sheet_summaries.append("\n".join(table_lines))

            full_table_text = "\n\n".join(sheet_summaries)
            prompt_content = (
                f"### Attached Excel Spreadsheet: {filename} ({size_formatted})\n"
                f"{full_table_text}"
            )

            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "excel",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": prompt_content,
                "metadata": {"sheets": wb.sheetnames},
            }
        except Exception as e:
            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "excel",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": f"[Excel spreadsheet: {filename} (Error parsing: {str(e)})]",
                "metadata": {"error": str(e)},
            }

    @staticmethod
    def _process_csv(attachment_id: str, filename: str, file_bytes: bytes, size_formatted: str) -> Dict[str, Any]:
        """Extract CSV tabular data and format as markdown table."""
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)

            if not rows:
                return {
                    "id": attachment_id,
                    "filename": filename,
                    "file_type": "document",
                    "doc_type": "csv",
                    "size_formatted": size_formatted,
                    "preview_url": "",
                    "extracted_text": f"[Empty CSV file: {filename}]",
                    "metadata": {"rows": 0},
                }

            # Convert to Markdown table (limit to first 60 rows)
            table_lines = [f"### Attached CSV Data: {filename} ({len(rows)} rows, {size_formatted})"]
            headers = [c.strip() for c in rows[0]]
            table_lines.append("| " + " | ".join(headers) + " |")
            table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

            for row in rows[1:61]:
                table_lines.append("| " + " | ".join(c.strip() for c in row) + " |")

            if len(rows) > 61:
                table_lines.append(f"\n*(Showing first 60 of {len(rows)} rows)*")

            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "csv",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": "\n".join(table_lines),
                "metadata": {"rows": len(rows), "columns": len(headers)},
            }
        except Exception as e:
            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "csv",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": f"[CSV file: {filename} (Error reading: {str(e)})]",
                "metadata": {"error": str(e)},
            }

    @staticmethod
    def _process_docx(attachment_id: str, filename: str, file_bytes: bytes, size_formatted: str) -> Dict[str, Any]:
        """Extract text and tables from Word document (.docx)."""
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            # Extract tables if present
            table_texts = []
            for t in doc.tables[:5]:
                for row in t.rows:
                    row_vals = [cell.text.strip() for cell in row.cells]
                    table_texts.append(" | ".join(row_vals))

            content_parts = []
            if paragraphs:
                content_parts.append("\n".join(paragraphs[:100]))
            if table_texts:
                content_parts.append("\n**Tables Extracted:**\n" + "\n".join(table_texts[:50]))

            full_text = "\n\n".join(content_parts)
            prompt_content = (
                f"### Attached Word Document: {filename} ({size_formatted})\n"
                f"```text\n{full_text}\n```"
            )

            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "docx",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": prompt_content,
                "metadata": {"paragraphs": len(paragraphs)},
            }
        except Exception as e:
            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "document",
                "doc_type": "docx",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": f"[Word document: {filename} (Error parsing: {str(e)})]",
                "metadata": {"error": str(e)},
            }

    @staticmethod
    def _process_video(attachment_id: str, filename: str, file_bytes: bytes, size_formatted: str) -> Dict[str, Any]:
        """Sample keyframes and extract timeline metadata from video files."""
        temp_video_path = MEDIA_UPLOAD_DIR / f"{attachment_id}_{filename}"
        try:
            # Write video to temp staging file for OpenCV
            with open(temp_video_path, "wb") as f:
                f.write(file_bytes)

            import cv2
            cap = cv2.VideoCapture(str(temp_video_path))
            if not cap.isOpened():
                return {
                    "id": attachment_id,
                    "filename": filename,
                    "file_type": "video",
                    "size_formatted": size_formatted,
                    "preview_url": "",
                    "extracted_text": f"[Attached Video: {filename} ({size_formatted})]",
                    "metadata": {},
                }

            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_sec = round(total_frames / max(1.0, fps), 1)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Sample 5 representative keyframes (at 10%, 30%, 50%, 70%, 90% of duration)
            sample_percentages = [0.10, 0.30, 0.50, 0.70, 0.90]
            keyframes_b64 = []
            preview_b64 = ""

            for idx, pct in enumerate(sample_percentages):
                frame_idx = int(total_frames * pct)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # Convert BGR (cv2) to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_frame = Image.fromarray(frame_rgb)
                    
                    # Create thumbnail for the first frame
                    if not preview_b64:
                        thumb = pil_frame.copy()
                        thumb.thumbnail((140, 100))
                        buf = io.BytesIO()
                        thumb.save(buf, format="JPEG", quality=80)
                        preview_b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

                    # Scale down frame to standard vision size (max 640px)
                    pil_frame.thumbnail((640, 640))
                    f_buf = io.BytesIO()
                    pil_frame.save(f_buf, format="JPEG", quality=80)
                    timestamp_sec = round(duration_sec * pct, 1)
                    keyframes_b64.append({
                        "timestamp": f"{timestamp_sec}s",
                        "data": f"data:image/jpeg;base64,{base64.b64encode(f_buf.getvalue()).decode('utf-8')}",
                    })

            cap.release()

            timestamps_str = ", ".join(f"{kf['timestamp']}" for kf in keyframes_b64)
            extracted_text = (
                f"### Attached Video: {filename}\n"
                f"- **Duration:** {duration_sec} seconds ({total_frames} total frames at {round(fps, 1)} FPS)\n"
                f"- **Resolution:** {width}x{height} pixels\n"
                f"- **Size:** {size_formatted}\n"
                f"- **Extracted Keyframes:** {len(keyframes_b64)} visual frames sampled across the timeline at timestamps [{timestamps_str}].\n"
                f"Analyze this video based on its timeline and extracted visual keyframes."
            )

            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "video",
                "size_formatted": size_formatted,
                "preview_url": preview_b64,
                "extracted_text": extracted_text,
                "keyframes": keyframes_b64,
                "metadata": {
                    "duration_sec": duration_sec,
                    "resolution": f"{width}x{height}",
                    "fps": round(fps, 1),
                    "total_frames": total_frames,
                    "keyframes_count": len(keyframes_b64),
                },
            }
        except Exception as e:
            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "video",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": f"[Video attachment: {filename} (Error analyzing: {str(e)})]",
                "metadata": {"error": str(e)},
            }
        finally:
            # Clean up temp file
            if temp_video_path.exists():
                try:
                    temp_video_path.unlink()
                except Exception:
                    pass

    @staticmethod
    def _process_text_file(attachment_id: str, filename: str, file_bytes: bytes, size_formatted: str) -> Dict[str, Any]:
        """Read plain text, code, or markdown files."""
        try:
            content = file_bytes.decode("utf-8", errors="replace")
            # Limit to first 12,000 characters to keep context size manageable
            truncated = content[:12000]
            if len(content) > 12000:
                truncated += f"\n\n[... Truncated for context: showing first 12,000 of {len(content)} characters]"

            prompt_content = (
                f"### Attached File: {filename} ({size_formatted})\n"
                f"```{Path(filename).suffix.lstrip('.') or 'text'}\n{truncated}\n```"
            )

            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "text",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": prompt_content,
                "metadata": {"characters": len(content)},
            }
        except Exception as e:
            return {
                "id": attachment_id,
                "filename": filename,
                "file_type": "text",
                "size_formatted": size_formatted,
                "preview_url": "",
                "extracted_text": f"[File: {filename} (Error reading: {str(e)})]",
                "metadata": {"error": str(e)},
            }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes >= 1024 * 1024:
            return f"{round(size_bytes / (1024 * 1024), 2)} MB"
        elif size_bytes >= 1024:
            return f"{round(size_bytes / 1024, 1)} KB"
        return f"{size_bytes} B"
