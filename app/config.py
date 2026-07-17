"""
AFlam-Api V3 - Configuration
Resolver-based (RC4/RC6 decryption + HTTP extraction)
"""
import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", 5))
TIMEOUT = int(os.getenv("TIMEOUT", 30000))
CACHE_TTL = int(os.getenv("CACHE_TTL", 900))  # 15 minutes cache
