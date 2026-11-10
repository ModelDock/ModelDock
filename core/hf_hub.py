"""
ModelDock Studio - Hugging Face Hub Interface
Searches models, explores popular open-source architectures, checks repo permissions, and inspects GGUF files.
"""

from typing import List, Dict, Any, Optional
import httpx
from core.auth_manager import AuthManager

HF_API_BASE = "https://huggingface.co/api"

# Curated list of popular, high-performing open-source models ready for 1-click exploration
FEATURED_MODELS = [
    {
        "id": "unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF",
        "name": "DeepSeek R1 (7B Distill Qwen)",
        "author": "deepseek-ai / unsloth",
        "category": "Reasoning & Math",
        "description": "State-of-the-art open reasoning model. Outperforms OpenAI o1-mini on multiple coding & math benchmarks.",
        "parameters": "7B",
        "quant_rec": "Q4_K_M (4.68 GB)",
        "gated": False,
        "likes": 2840,
        "downloads": "1.2M",
    },
    {
        "id": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "name": "Llama 3.2 3B Instruct",
        "author": "meta-llama / bartowski",
        "category": "Fast & Lightweight Chat",
        "description": "Meta's ultra-compact, high-speed lightweight model designed for edge devices and rapid conversational AI.",
        "parameters": "3.2B",
        "quant_rec": "Q4_K_M (2.02 GB)",
        "gated": False,
        "likes": 1210,
        "downloads": "850K",
    },
    {
        "id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        "name": "Qwen 2.5 Coder 7B",
        "author": "Qwen",
        "category": "Code & Software Engineering",
        "description": "One of the best code-generation models available, supporting 92+ programming languages and 32k context.",
        "parameters": "7.6B",
        "quant_rec": "Q4_K_M (4.7 GB)",
        "gated": False,
        "likes": 3450,
        "downloads": "2.4M",
    },
    {
        "id": "bartowski/gemma-2-9b-it-GGUF",
        "name": "Gemma 2 9B Instruct",
        "author": "google / bartowski",
        "category": "General Knowledge & Creative",
        "description": "Google DeepMind's open architecture model with high parameter efficiency and natural prose.",
        "parameters": "9B",
        "quant_rec": "Q4_K_M (5.5 GB)",
        "gated": False,
        "likes": 2180,
        "downloads": "650K",
    },
    {
        "id": "bartowski/Mistral-7B-Instruct-v0.3-GGUF",
        "name": "Mistral 7B Instruct v0.3",
        "author": "mistralai / bartowski",
        "category": "Balanced Workhorse",
        "description": "Mistral AI's flagship 7B model with function calling, structured outputs, and 32k context.",
        "parameters": "7B",
        "quant_rec": "Q4_K_M (4.37 GB)",
        "gated": False,
        "likes": 1950,
        "downloads": "1.8M",
    },
    {
        "id": "bartowski/Phi-3.5-mini-instruct-GGUF",
        "name": "Phi-3.5 Mini Instruct",
        "author": "microsoft / bartowski",
        "category": "Reasoning on Low RAM",
        "description": "Microsoft's high-efficiency 3.8B model with 128k context support and strong multi-lingual reasoning.",
        "parameters": "3.8B",
        "quant_rec": "Q4_K_M (2.39 GB)",
        "gated": False,
        "likes": 1100,
        "downloads": "510K",
    },
    {
        "id": "meta-llama/Llama-3.1-8B-Instruct",
        "name": "Meta Llama 3.1 8B Instruct (Gated)",
        "author": "meta-llama",
        "category": "Flagship Open Source",
        "description": "Official Meta weights repository. Requires accepted license agreement and Hugging Face Authentication Token.",
        "parameters": "8B",
        "quant_rec": "Requires HF Token",
        "gated": True,
        "likes": 8700,
        "downloads": "4.5M",
    },
]

# Curated High-Speed Global Registry of Open-Source Models (Ollama, HF, GGUF)
POPULAR_OPEN_SOURCE_MODELS = [
    {"name": "DeepSeek R1 1.5B (Distill Qwen)", "id": "unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF", "tag": "deepseek-r1:1.5b", "size": "1.1 GB", "family": "DeepSeek", "params": "1.5B", "source": "Hugging Face / Ollama", "type": "Reasoning"},
    {"name": "DeepSeek R1 7B (Distill Qwen)", "id": "unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF", "tag": "deepseek-r1:7b", "size": "4.7 GB", "family": "DeepSeek", "params": "7B", "source": "Hugging Face / Ollama", "type": "Reasoning"},
    {"name": "DeepSeek R1 8B (Distill Llama)", "id": "unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF", "tag": "deepseek-r1:8b", "size": "4.9 GB", "family": "DeepSeek", "params": "8B", "source": "Hugging Face / Ollama", "type": "Reasoning"},
    {"name": "DeepSeek R1 14B (Distill Qwen)", "id": "unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF", "tag": "deepseek-r1:14b", "size": "9.0 GB", "family": "DeepSeek", "params": "14B", "source": "Hugging Face / Ollama", "type": "Reasoning"},
    {"name": "Llama 3.2 1B Instruct", "id": "bartowski/Llama-3.2-1B-Instruct-GGUF", "tag": "llama3.2:1b", "size": "1.3 GB", "family": "Llama", "params": "1B", "source": "Hugging Face / Ollama", "type": "Chat & Edge"},
    {"name": "Llama 3.2 3B Instruct", "id": "bartowski/Llama-3.2-3B-Instruct-GGUF", "tag": "llama3.2:3b", "size": "2.0 GB", "family": "Llama", "params": "3.2B", "source": "Hugging Face / Ollama", "type": "Fast Chat"},
    {"name": "Llama 3.1 8B Instruct", "id": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF", "tag": "llama3.1:8b", "size": "4.9 GB", "family": "Llama", "params": "8B", "source": "Hugging Face / Ollama", "type": "General"},
    {"name": "Llama 3.3 70B Instruct", "id": "bartowski/Llama-3.3-70B-Instruct-GGUF", "tag": "llama3.3:70b", "size": "42.0 GB", "family": "Llama", "params": "70B", "source": "Hugging Face / Ollama", "type": "Flagship"},
    {"name": "Qwen 2.5 Coder 1.5B Instruct", "id": "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF", "tag": "qwen2.5-coder:1.5b", "size": "1.0 GB", "family": "Qwen", "params": "1.5B", "source": "Hugging Face / Ollama", "type": "Code"},
    {"name": "Qwen 2.5 Coder 7B Instruct", "id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF", "tag": "qwen2.5-coder:7b", "size": "4.7 GB", "family": "Qwen", "params": "7B", "source": "Hugging Face / Ollama", "type": "Code"},
    {"name": "Qwen 2.5 Coder 14B Instruct", "id": "Qwen/Qwen2.5-Coder-14B-Instruct-GGUF", "tag": "qwen2.5-coder:14b", "size": "9.0 GB", "family": "Qwen", "params": "14B", "source": "Hugging Face / Ollama", "type": "Code"},
    {"name": "Qwen 2.5 Coder 32B Instruct", "id": "Qwen/Qwen2.5-Coder-32B-Instruct-GGUF", "tag": "qwen2.5-coder:32b", "size": "19.8 GB", "family": "Qwen", "params": "32B", "source": "Hugging Face / Ollama", "type": "Code"},
    {"name": "Qwen 2.5 7B Instruct", "id": "Qwen/Qwen2.5-7B-Instruct-GGUF", "tag": "qwen2.5:7b", "size": "4.7 GB", "family": "Qwen", "params": "7B", "source": "Hugging Face / Ollama", "type": "General"},
    {"name": "Phi 4 14B Instruct", "id": "bartowski/phi-4-GGUF", "tag": "phi4:14b", "size": "9.1 GB", "family": "Phi", "params": "14B", "source": "Hugging Face / Ollama", "type": "Reasoning"},
    {"name": "Phi 3.5 Mini 3.8B Instruct", "id": "bartowski/Phi-3.5-mini-instruct-GGUF", "tag": "phi3.5:3.8b", "size": "2.4 GB", "family": "Phi", "params": "3.8B", "source": "Hugging Face / Ollama", "type": "Lightweight"},
    {"name": "Mistral 7B Instruct v0.3", "id": "bartowski/Mistral-7B-Instruct-v0.3-GGUF", "tag": "mistral:7b", "size": "4.4 GB", "family": "Mistral", "params": "7B", "source": "Hugging Face / Ollama", "type": "General"},
    {"name": "Mistral Nemo 12B Instruct", "id": "bartowski/Mistral-Nemo-Instruct-2407-GGUF", "tag": "mistral-nemo:12b", "size": "7.5 GB", "family": "Mistral", "params": "12B", "source": "Hugging Face / Ollama", "type": "General"},
    {"name": "Gemma 2 2B Instruct", "id": "bartowski/gemma-2-2b-it-GGUF", "tag": "gemma2:2b", "size": "1.6 GB", "family": "Gemma", "params": "2B", "source": "Hugging Face / Ollama", "type": "Edge Chat"},
    {"name": "Gemma 2 9B Instruct", "id": "bartowski/gemma-2-9b-it-GGUF", "tag": "gemma2:9b", "size": "5.5 GB", "family": "Gemma", "params": "9B", "source": "Hugging Face / Ollama", "type": "General"},
    {"name": "Gemma 2 27B Instruct", "id": "bartowski/gemma-2-27b-it-GGUF", "tag": "gemma2:27b", "size": "16.8 GB", "family": "Gemma", "params": "27B", "source": "Hugging Face / Ollama", "type": "Flagship"},
    {"name": "SmolLM2 135M Instruct", "id": "HuggingFaceTB/SmolLM2-135M-Instruct-GGUF", "tag": "smollm2:135m", "size": "140 MB", "family": "SmolLM", "params": "135M", "source": "Hugging Face / Ollama", "type": "Ultra-light"},
    {"name": "SmolLM2 360M Instruct", "id": "HuggingFaceTB/SmolLM2-360M-Instruct-GGUF", "tag": "smollm2:360m", "size": "260 MB", "family": "SmolLM", "params": "360M", "source": "Hugging Face / Ollama", "type": "Ultra-light"},
    {"name": "SmolLM2 1.7B Instruct", "id": "HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF", "tag": "smollm2:1.7b", "size": "1.1 GB", "family": "SmolLM", "params": "1.7B", "source": "Hugging Face / Ollama", "type": "Fast Chat"},
    {"name": "LLaVA 1.5 7B (Vision)", "id": "mys/ggml_llava-v1.5-7b", "tag": "llava:7b", "size": "4.5 GB", "family": "LLaVA", "params": "7B", "source": "Hugging Face / Ollama", "type": "Vision"},
    {"name": "MiniCPM-V 2.6 (Vision)", "id": "openbmb/MiniCPM-V-2_6-gguf", "tag": "minicpm-v:8b", "size": "5.5 GB", "family": "MiniCPM", "params": "8B", "source": "Hugging Face / Ollama", "type": "Vision"},
    {"name": "Qwen2-VL 7B (Vision)", "id": "Qwen/Qwen2-VL-7B-Instruct-GGUF", "tag": "qwen2-vl:7b", "size": "4.8 GB", "family": "Qwen", "params": "7B", "source": "Hugging Face / Ollama", "type": "Vision"},
]


class HFHubClient:
    def __init__(self, auth_manager: Optional[AuthManager] = None):
        self.auth_manager = auth_manager or AuthManager()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "ModelDock-Studio/1.0",
            "Accept": "application/json",
        }
        headers.update(self.auth_manager.get_auth_headers())
        return headers

    def get_featured_models(self) -> List[Dict[str, Any]]:
        """Return curated list of high-quality open-source models."""
        return FEATURED_MODELS

    async def omni_search(
        self,
        query: str,
        installed_models: Optional[List[Dict[str, Any]]] = None,
        limit: int = 15,
    ) -> Dict[str, Any]:
        """
        Ultra-fast instant type-ahead search matching across:
        1. Locally installed models (0ms instant)
        2. Curated Open-Source catalog (Ollama / HF registry)
        3. Live Hugging Face Hub GGUF repositories
        """
        q = query.strip().lower()
        if not q:
            return {
                "local": installed_models[:3] if installed_models else [],
                "catalog": POPULAR_OPEN_SOURCE_MODELS[:8],
                "huggingface": [],
            }

        # 1. Match locally installed models
        matched_local = []
        if installed_models:
            for m in installed_models:
                m_name = m.get("name", "").lower()
                m_fn = m.get("filename", "").lower()
                if q in m_name or q in m_fn:
                    matched_local.append(m)

        # 2. Match curated open-source catalog (Ollama / HF)
        matched_catalog = []
        for m in POPULAR_OPEN_SOURCE_MODELS:
            name = m["name"].lower()
            tag = m["tag"].lower()
            mid = m["id"].lower()
            fam = m["family"].lower()
            if q in name or q in tag or q in mid or q in fam:
                matched_catalog.append(m)

        # 3. Live search on Hugging Face Hub (limit 6 for ultra-responsive speed)
        hf_results = []
        try:
            hf_matches = await self.search_models(query=query, filter_type="gguf", sort="downloads", limit=6)
            hf_results = hf_matches[:6]
        except Exception:
            pass

        return {
            "local": matched_local[:5],
            "catalog": matched_catalog[:8],
            "huggingface": hf_results,
        }

    async def search_models(
        self,
        query: str = "",
        filter_type: str = "gguf",
        sort: str = "downloads",
        limit: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Search Hugging Face Hub with optional GGUF filter, sort, and pagination.
        """
        params = {
            "limit": limit,
            "direction": "-1",
        }
        if query.strip():
            params["search"] = query.strip()
        if filter_type:
            params["filter"] = filter_type
        if sort:
            params["sort"] = sort

        url = f"{HF_API_BASE}/models"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, params=params, headers=self._headers())
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for item in data:
                        model_id = item.get("id", "")
                        gated = item.get("gated", False)
                        likes = item.get("likes", 0)
                        downloads = item.get("downloads", 0)
                        tags = item.get("tags", [])
                        results.append(
                            {
                                "id": model_id,
                                "name": model_id.split("/")[-1] if "/" in model_id else model_id,
                                "author": model_id.split("/")[0] if "/" in model_id else "Community",
                                "likes": likes,
                                "downloads": downloads,
                                "gated": bool(gated),
                                "tags": tags[:6],
                                "pipeline_tag": item.get("pipeline_tag", "text-generation"),
                                "last_modified": item.get("lastModified", "")[:10],
                            }
                        )
                    return results
                else:
                    return []
        except Exception:
            return []

    async def inspect_repo_files(self, repo_id: str) -> Dict[str, Any]:
        """
        Inspect all files in a Hugging Face repository and extract GGUF quantizations.
        """
        url = f"{HF_API_BASE}/models/{repo_id}"
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.get(url, headers=self._headers())
                if res.status_code == 401 or res.status_code == 403:
                    return {
                        "error": "Access Denied. This model is gated or private. Please provide an authorized Hugging Face Token in the Authentication tab.",
                        "gated": True,
                        "files": [],
                    }
                elif res.status_code != 200:
                    return {
                        "error": f"Failed to fetch model info (Status {res.status_code}): {res.text}",
                        "files": [],
                    }

                data = res.json()
                siblings = data.get("siblings", [])
                gguf_files = []

                # Try to fetch exact file sizes from repository tree API
                file_sizes = {}
                try:
                    tree_url = f"{HF_API_BASE}/models/{repo_id}/tree/main"
                    tree_res = await client.get(tree_url, headers=self._headers())
                    if tree_res.status_code == 200:
                        for item in tree_res.json():
                            if item.get("type") == "file" and "size" in item:
                                file_sizes[item.get("path")] = item["size"]
                except Exception:
                    pass

                for f in siblings:
                    rfilename = f.get("rfilename", "")
                    if rfilename.lower().endswith(".gguf"):
                        # Download URL
                        download_url = f"https://huggingface.co/{repo_id}/resolve/main/{rfilename}"
                        
                        # Infer quantization tier from filename
                        fn_upper = rfilename.upper()
                        quant = "Unknown"
                        for q in ["Q4_K_M", "Q4_K_S", "Q5_K_M", "Q5_K_S", "Q8_0", "Q2_K", "Q3_K_L", "Q3_K_M", "Q6_K", "F16", "BF16"]:
                            if q in fn_upper:
                                quant = q
                                break

                        # Format exact file size if available
                        size_bytes = file_sizes.get(rfilename, 0)
                        if size_bytes > 0:
                            if size_bytes >= 1024**3:
                                size_formatted = f"{size_bytes / (1024**3):.2f} GB"
                            else:
                                size_formatted = f"{size_bytes / (1024**2):.1f} MB"
                        else:
                            size_formatted = ""

                        gguf_files.append(
                            {
                                "filename": rfilename,
                                "download_url": download_url,
                                "quantization": quant,
                                "size_bytes": size_bytes,
                                "size_formatted": size_formatted,
                                "recommended": quant in ["Q4_K_M", "Q5_K_M"],
                            }
                        )

                # Sort so recommended Q4_K_M appears on top
                gguf_files.sort(key=lambda x: (not x["recommended"], x["filename"]))

                # Check if repo is in curated featured models for rich metadata
                featured_match = next((m for m in FEATURED_MODELS if m["id"] == repo_id), None)
                
                # Infer Architecture, Parameters, Context, and VRAM
                name_str = (featured_match["name"] if featured_match else repo_id.split("/")[-1]).replace("-", " ")
                clean_name = featured_match["name"] if featured_match else repo_id.split("/")[-1]
                author_name = featured_match["author"] if featured_match else data.get("author", repo_id.split("/")[0])
                
                # Parameters
                params = "7B"
                if featured_match and featured_match.get("parameters"):
                    params = featured_match["parameters"]
                else:
                    import re
                    param_match = re.search(r"(\d+(?:\.\d+)?)[bB]", repo_id)
                    if param_match:
                        params = f"{param_match.group(1)}B"
                
                # Architecture
                raw_tags = data.get("tags", [])
                arch = "Transformer"
                lower_id = repo_id.lower()
                if "deepseek" in lower_id:
                    arch = "DeepSeek-R1 / Qwen2"
                elif "qwen" in lower_id:
                    arch = "Qwen2.5"
                elif "llama" in lower_id:
                    arch = "Llama 3.2" if "3.2" in lower_id else "Llama 3"
                elif "gemma" in lower_id:
                    arch = "Gemma 2"
                elif "mistral" in lower_id:
                    arch = "Mistral"
                elif "phi" in lower_id:
                    arch = "Phi-3.5"

                # Context Length
                context_length = "32,768 tokens (32K)"
                if "deepseek" in lower_id or "128k" in lower_id or "llama-3" in lower_id or "llama3" in lower_id:
                    context_length = "131,072 tokens (128K)"
                elif "gemma" in lower_id or "8k" in lower_id:
                    context_length = "8,192 tokens (8K)"

                # Estimated VRAM
                vram_est = "~4.8 GB VRAM (Runs on 6GB / 8GB GPUs or CPU)"
                try:
                    num_p = float(params.replace("B", "").replace("b", ""))
                    if num_p <= 3.5:
                        vram_est = f"~{round(num_p * 0.75 + 0.6, 1)} GB VRAM (Ultra-lightweight: Runs smoothly on 4GB GPUs or CPU)"
                    elif num_p <= 8.0:
                        vram_est = f"~{round(num_p * 0.65 + 0.8, 1)} GB VRAM (Standard: Recommended for 6GB / 8GB GPUs or CPU RAM)"
                    else:
                        vram_est = f"~{round(num_p * 0.65 + 1.2, 1)} GB VRAM (High capacity: 12GB+ GPU or partial CPU RAM offload)"
                except Exception:
                    pass

                card_data = data.get("cardData") or {}
                license_name = card_data.get("license") or "Open Source / Community"
                base_model = card_data.get("base_model") or ""
                description = (
                    (featured_match.get("description") if featured_match else None)
                    or data.get("description")
                    or card_data.get("description")
                    or f"{clean_name} is an open-source neural weights repository hosted on Hugging Face, optimized for local inference with GGUF quantization."
                )

                quant_guides = {
                    "Q4_K_M": "Recommended: Best balance of inference speed, accuracy, and VRAM efficiency.",
                    "Q5_K_M": "High precision: Reduced perplexity loss with ~12% higher VRAM usage.",
                    "Q8_0": "Near lossless: 8-bit quantization retaining >99.5% FP16 fidelity.",
                    "Q2_K": "Ultra compact: Smallest footprint for memory-constrained edge devices.",
                    "Q3_K_M": "Compact: Moderate precision for lightweight environments.",
                    "Q6_K": "Very high accuracy: Sits between Q5_K_M and Q8_0 in quality.",
                    "F16": "Full precision: Original 16-bit floating point weights without quantization.",
                }

                # Recommended download size
                rec_size = "--"
                if featured_match and featured_match.get("quant_rec"):
                    rec_size = featured_match["quant_rec"]
                else:
                    rec_f = next((f for f in gguf_files if f.get("recommended") and f.get("size_formatted")), None)
                    if not rec_f:
                        rec_f = next((f for f in gguf_files if f.get("size_formatted")), None)
                    if rec_f:
                        rec_size = f"{rec_f['quantization']} ({rec_f['size_formatted']})"
                    else:
                        try:
                            rec_size = f"~{round(float(params.replace('B', '').replace('b', '')) * 0.62, 1)} GB (Q4_K_M)"
                        except Exception:
                            rec_size = "Standard (Q4_K_M)"

                # Attach quant guide descriptions to files
                for f in gguf_files:
                    q = f.get("quantization", "Unknown")
                    f["guide"] = quant_guides.get(q, "Standard GGUF quantization format for local execution.")

                return {
                    "id": repo_id,
                    "name": clean_name,
                    "author": author_name,
                    "architecture": arch,
                    "parameters": params,
                    "recommended_size": rec_size,
                    "context_length": context_length,
                    "estimated_vram": vram_est,
                    "license": license_name,
                    "base_model": base_model,
                    "tags": raw_tags[:12],
                    "gated": bool(data.get("gated", False)),
                    "pipeline_tag": data.get("pipeline_tag", "text-generation"),
                    "downloads": featured_match.get("downloads") if featured_match else data.get("downloads", 0),
                    "likes": featured_match.get("likes") if featured_match else data.get("likes", 0),
                    "files": gguf_files,
                    "description": description,
                    "source_url": f"https://huggingface.co/{repo_id}",
                    "source_platform": "Hugging Face Hub",
                    "category": featured_match.get("category", "General Open LLM") if featured_match else "Community GGUF",
                }
        except Exception as e:
            return {"error": f"Error inspecting model: {str(e)}", "files": []}
