"""
AI Metadata Generator using Pollinations AI
Generates viral titles, Instagram captions, Facebook posts, and hashtags
based on the HTML animation topic and filename.
"""

import os
import sys
import json
import re
import urllib.request
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

POLLINATIONS_API_URL = "https://gen.pollinations.ai/v1/chat/completions"

def clean_filename_to_title(filename: str) -> str:
    """Extract a clean, readable topic title from an HTML filename."""
    stem = Path(filename).stem
    # Replace underscores and hyphens with spaces
    title = re.sub(r'[_\-]+', ' ', stem)
    # Remove reel/html/visualizer keywords if trailing
    title = re.sub(r'\b(reel|visualizer|html|v\d+)\b', '', title, flags=re.IGNORECASE)
    # Collapse whitespace
    title = ' '.join(title.split())
    return title.strip()

def generate_ai_metadata(topic: str, api_key: str = None) -> dict:
    """
    Calls Pollinations AI API to generate structured social media metadata.
    """
    if not api_key:
        api_key = os.environ.get("POLLINATIONS_API_KEY")

    prompt = f"""You are a world-class viral tech creator and social media strategist.
Create a high-converting, educational social media release package for a 9:16 vertical video animation:
Topic: "{topic}"

RETURN ONLY A VALID JSON OBJECT with these exact keys:
- "title": "Ultra-engaging hook title (under 80 chars, e.g. {topic}: What Actually Happens?)"
- "ig_caption": "Captivating Instagram Reels caption (1000-1500 chars). Hook the audience in the first line, explain the core mechanics simply, break down 3-4 key insights with bullet emojis, and end with a curiosity question to drive comments."
- "fb_caption": "Conversational, highly engaging post for Facebook tech communities with key insights and a discussion hook."
- "threads_caption": "Snappy, punchy developer takeaway for Threads (under 400 chars)."
- "hashtags": ["#Tech", "#Programming", "#Coding", "#ComputerScience", "#SoftwareEngineering", "#WebDev", "#LearnToCode"]

Rules:
- Output raw valid JSON only. Do NOT include markdown code fences, backticks, or extra explanation.
"""

    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "gemini-fast",
        "jsonMode": True
    }

    try:
        req = urllib.request.Request(
            POLLINATIONS_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()
            
            # Extract JSON from potential markdown wrapping
            json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', content) or re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group(1) if json_match.lastindex else json_match.group(0))
                return result
            return json.loads(content)
    except Exception as e:
        print(f"⚠️  Pollinations API call warning ({e}). Generating fallback metadata...")
        return {
            "title": f"{topic}: What Really Happens Behind the Scenes",
            "ig_caption": f"Ever wondered what actually happens during: {topic}?\n\nHere is the complete visual breakdown of how modern computer systems and AI models process this step-by-step.\n\nKey takeaways:\n⚡ Every step happens in milliseconds\n⚡ Multiple layers of abstraction work together\n⚡ High-efficiency architectures ensure low latency\n\nWhich part surprised you most? Drop your thoughts below! 👇",
            "fb_caption": f"Deep dive into {topic}!\n\nHere is a step-by-step breakdown of how the architecture works under the hood. Watch the reel to see how each phase connects seamlessly.",
            "threads_caption": f"{topic} explained visually in 15 seconds. Incredible how much engineering happens under the hood.",
            "hashtags": ["#Tech", "#Programming", "#ComputerScience", "#SoftwareEngineering", "#Coding"]
        }

if __name__ == "__main__":
    sample_topic = sys.argv[1] if len(sys.argv) > 1 else "What Happens When You Hit Enter.html"
    title = clean_filename_to_title(sample_topic)
    print(f"🤖 Generating AI metadata for topic: '{title}'...")
    meta = generate_ai_metadata(title)
    print(json.dumps(meta, indent=2, ensure_ascii=False))
