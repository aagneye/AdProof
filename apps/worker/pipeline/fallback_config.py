"""Centralized fallback model chains per pipeline step."""

FALLBACK_CHAINS = {
    "storyboard": ["flux-kontext-pro", "imagen-4"],
    "animate": ["runway-gen4-turbo", "luma-ray-2"],
    "voiceover": ["nvidia-magpie-tts"],
    "score": ["gmicloud-minimax"],
}
