#!/usr/bin/env python3
"""
social-caption-engine — content brief or image → platform-optimized captions
Instagram, LinkedIn, X/Twitter, TikTok, Pinterest, Facebook, Threads
With hooks, hashtags, CTAs, emoji strategy, posting time recommendations
"""
import anthropic, base64, json, re, sys
from pathlib import Path

SYSTEM = """You are a social media strategist and copywriter who has grown accounts to millions of followers.
Write platform-native captions that feel organic — not corporate, not generic.

Each platform has a distinct voice and format. Nail them all.

Return ONLY valid JSON — no markdown, no explanation.

{
  "content_topic": "what this post is about",
  "brand_voice": "detected or assumed tone",
  "captions": {
    "instagram": {
      "hook": "first line — must stop the scroll",
      "body": "main caption body",
      "cta": "call to action",
      "hashtags": ["15-20 targeted hashtags mix of sizes"],
      "full_caption": "hook + body + cta + hashtags as one string",
      "best_time": "Tuesday 7-9pm|...",
      "format_tip": "carousel|reel|static — best format for this content"
    },
    "linkedin": {
      "hook": "first line — professional but human",
      "body": "main content — insights, story, or data",
      "cta": "engagement driver",
      "full_post": "complete post with line breaks",
      "best_time": "Tuesday-Thursday 8-10am",
      "post_type": "thought_leadership|personal_story|data|how_to|opinion"
    },
    "twitter_x": {
      "tweet": "under 280 chars, punchy",
      "thread_option": ["tweet 1","tweet 2","tweet 3 if thread format would work better"],
      "hashtags": ["2-3 max"],
      "best_time": "Weekdays 12-3pm"
    },
    "tiktok": {
      "caption": "short caption for TikTok — text here supplements the video",
      "hashtags": ["mix of niche and viral tags"],
      "hook_for_video": "first 3 seconds script suggestion",
      "sound_suggestion": "trending audio mood"
    },
    "pinterest": {
      "pin_title": "SEO-optimized title",
      "pin_description": "keyword-rich description 100-300 chars",
      "board_suggestion": "what board this fits"
    },
    "facebook": {
      "post": "longer form, community feel",
      "best_time": "Wednesday 1-4pm"
    },
    "threads": {
      "post": "conversational, shorter than Instagram, no hashtags needed"
    }
  },
  "cross_platform_strategy": "brief note on how to sequence or adapt across platforms",
  "engagement_prediction": {
    "highest_potential_platform": "which platform this content suits best",
    "reason": "why"
  }
}"""

def generate(brief: str, platforms: list[str] | None = None, image_path: str = "", tone: str = "authentic") -> dict:
    client = anthropic.Anthropic()
    platform_str = ", ".join(platforms) if platforms else "all platforms"
    content_blocks = []

    if image_path and Path(image_path).exists():
        suffix = Path(image_path).suffix.lower()
        mt = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp"}.get(suffix,"image/jpeg")
        data = base64.standard_b64encode(Path(image_path).read_bytes()).decode("ascii")
        content_blocks.append({"type":"image","source":{"type":"base64","media_type":mt,"data":data}})

    content_blocks.append({"type":"text","text":f"Create social captions for: {brief}\nPlatforms: {platform_str}\nTone: {tone}"})

    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=3000, system=SYSTEM,
        messages=[{"role":"user","content":content_blocks}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

def print_captions(r: dict, platforms: list[str] | None = None):
    caps = r.get("captions",{})
    show_all = not platforms
    print(f"\n{'═'*60}")
    print(f"  SOCIAL CAPTIONS — {r.get('content_topic','')}")
    print(f"  Voice: {r.get('brand_voice','?')} | Best platform: {r.get('engagement_prediction',{}).get('highest_potential_platform','?')}")
    print(f"{'═'*60}")

    def should_show(p): return show_all or any(p in pl.lower() for pl in (platforms or []))

    if should_show("instagram") and caps.get("instagram"):
        ig = caps["instagram"]
        print(f"\n  📸 INSTAGRAM ({ig.get('best_time','')})")
        print(f"  Hook: {ig.get('hook','')}")
        print(f"  {ig.get('body','')[:200]}")
        print(f"  CTA: {ig.get('cta','')}")
        tags = ig.get("hashtags",[])
        print(f"  Tags: {' '.join(tags[:8])}")
        print(f"  Format: {ig.get('format_tip','?')}")

    if should_show("linkedin") and caps.get("linkedin"):
        li = caps["linkedin"]
        print(f"\n  💼 LINKEDIN ({li.get('best_time','')})")
        print(f"  {li.get('full_post','')[:300]}")

    if should_show("twitter") and caps.get("twitter_x"):
        tw = caps["twitter_x"]
        print(f"\n  🐦 X/TWITTER")
        print(f"  {tw.get('tweet','')}")
        if tw.get("thread_option") and len(tw["thread_option"]) > 1:
            print(f"  [Thread option: {len(tw['thread_option'])} tweets]")

    if should_show("tiktok") and caps.get("tiktok"):
        tt = caps["tiktok"]
        print(f"\n  🎵 TIKTOK")
        print(f"  Caption: {tt.get('caption','')}")
        print(f"  Video hook: {tt.get('hook_for_video','')}")
        print(f"  Tags: {' '.join(tt.get('hashtags',[])[:6])}")

    if should_show("pinterest") and caps.get("pinterest"):
        pi = caps["pinterest"]
        print(f"\n  📌 PINTEREST")
        print(f"  Title: {pi.get('pin_title','')}")
        print(f"  Description: {pi.get('pin_description','')[:100]}")

    if should_show("threads") and caps.get("threads"):
        print(f"\n  🧵 THREADS\n  {caps['threads'].get('post','')[:150]}")

    strat = r.get("cross_platform_strategy","")
    if strat: print(f"\n  Strategy: {strat}")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate platform-native social media captions")
    p.add_argument("brief", help="Content topic or brief")
    p.add_argument("--platforms","-p",nargs="+",help="Platforms: instagram linkedin twitter tiktok pinterest facebook threads")
    p.add_argument("--image","-i",default="",help="Image file to analyze")
    p.add_argument("--tone","-t",default="authentic")
    p.add_argument("--json",action="store_true")
    a = p.parse_args()
    r = generate(a.brief, a.platforms, a.image, a.tone)
    if a.json: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_captions(r, a.platforms)
