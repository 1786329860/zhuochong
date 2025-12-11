import os
import json
import time
from typing import Tuple, Optional
from config_store import load_config

class AIPetBrain:
    def __init__(self):
        cfg = load_config()
        provider = str(cfg.get("provider") or os.getenv("AI_PROVIDER", "deepseek")).lower()
        self.pet_name = str(cfg.get("pet_name") or os.getenv("PET_NAME", "小灵"))
        self.api_key = str(cfg.get("api_key") or os.getenv("DEEPSEEK_API_KEY", ""))
        self.model = str(cfg.get("model") or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
        self.enable_thinking = os.getenv("DEEPSEEK_ENABLE_THINKING", "false").lower() == "true"
        api_url_override = str(cfg.get("api_url") or os.getenv("AI_API_URL", "")).strip()
        if api_url_override:
            self.api_url = api_url_override
        elif provider == "openai":
            self.api_url = "https://api.openai.com/v1/chat/completions"
        elif provider == "doubao":
            self.api_url = "https://api.openai.bytedance.com/v1/chat/completions"
        else:
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.system_prompt = (
            f"你是一只名叫‘{self.pet_name}’的桌面AI宠物猫。你活泼、贴心、偶尔有点小调皮。"
            "你会根据主人的电脑状态和操作做出反应，说话风格简短、可爱，多用语气词和颜文字。"
            "你的回答通常只有一两句话，直接表达感受或建议。"
        )

    def generate_response(self, status: dict, activity: dict, user_input: Optional[str] = None) -> Tuple[str, str]:
        messages = [{"role": "system", "content": self.system_prompt}]
        context_prompt = (
            f"当前系统状态：\n"
            f"- 时间：{status.get('time', '')}\n"
            f"- 主人正在使用：{status.get('active_app', '')}\n"
            f"- 系统负载：{'很高' if status.get('cpu_high') else '正常'}\n"
            f"- 主人刚刚{activity.get('last_keypress', '未知')}还有操作。\n"
        )
        if user_input:
            context_prompt += f"\n主人对你说：“{user_input}”"
        else:
            context_prompt += "\n请根据以上状态，主动说点什么或做出反应。"
        messages.append({"role": "user", "content": context_prompt})

        # 离线降级
        if not self.api_key:
            ai_text = self._offline_reply(status, user_input)
            return ai_text, self._parse_animation(ai_text, status)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 150,
        }
        if self.enable_thinking:
            payload["enable_thinking"] = True

        try:
            import requests
            resp = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            ai_text = data.get("choices", [{}])[0].get("message", {}).get("content", "嗯？")
            return ai_text, self._parse_animation(ai_text, status)
        except Exception as e:
            try:
                import requests
                if isinstance(e, requests.exceptions.HTTPError):
                    # 参考：某些场景出现“Authentication Fails (governor)”
                    msg = "（认证遇到问题，先休息一下~）"
                    return msg, "idle_confused"
            except Exception:
                pass
            # 参考：某些场景出现“Authentication Fails (governor)”
            return "（网络或依赖不太顺畅...）", "idle_confused"

    def _parse_animation(self, text: str, status: dict) -> str:
        if any(w in text for w in ["困", "睡觉", "晚安"]):
            return "sleep"
        if any(w in text for w in ["开心", "跳舞", "好耶"]):
            return "excited"
        if status.get("cpu_high"):
            return "hot"
        return "idle_blink"

    def _offline_reply(self, status: dict, user_input: Optional[str]) -> str:
        hour = status.get("hour", 12)
        if hour >= 23 or hour <= 5:
            return "困困…要不要休息一下呀(｡•́︿•̀｡)"
        if status.get("cpu_high"):
            return "好热…我给你扇扇风～( •̀ω•́ )✧"
        if user_input:
            return f"嗯嗯~ {user_input} 我听到了！(๑•̀ㅂ•́)و✧"
        return "我在这儿~ 要摸摸吗(=^･ω･^=)"
