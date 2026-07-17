"""
AFlam-Api V3 - Decoders for encrypted source URLs
RC4/RC6 decryption used by VidSrc providers
"""
import base64
from urllib.parse import unquote
from typing import Union


async def rc4_decrypt(encrypted_source_url: str, key: str) -> str:
    """
    RC4 decryption of encrypted source URLs.
    Used by VidSrc.to, VidSrc.me, and related providers.
    """
    standardized_input = encrypted_source_url.replace('_', '/').replace('-', '+')
    binary_data = base64.b64decode(standardized_input)
    encoded = bytearray(binary_data)
    key_bytes = bytes(key, 'utf-8')
    j = 0
    s = bytearray(range(256))

    for i in range(256):
        j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
        s[i], s[j] = s[j], s[i]

    decoded = bytearray(len(encoded))
    i = 0
    k = 0
    for index in range(len(encoded)):
        i = (i + 1) & 0xff
        k = (k + s[i]) & 0xff
        s[i], s[k] = s[k], s[i]
        t = (s[i] + s[k]) & 0xff
        decoded[index] = encoded[index] ^ s[t]

    decoded_text = decoded.decode('utf-8')
    return unquote(decoded_text)


async def xor_decrypt(encoded_hex: str, seed: str) -> str:
    """
    XOR decryption used by VidSrc.me RCP endpoint.
    The encoded data is hex-encoded bytes XORed with the IMDB ID seed.
    """
    encoded_buffer = bytes.fromhex(encoded_hex)
    decoded = ""
    for i in range(len(encoded_buffer)):
        decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
    
    if decoded.startswith("//"):
        decoded = f"https:{decoded}"
    return decoded


async def hex_decode(encoded: str) -> bytearray:
    """Decode hex-encoded string to bytearray."""
    return bytearray(bytes.fromhex(encoded))


async def decode_with_keys(data: Union[bytearray, str], keys: list) -> str:
    """
    Multi-step RC4 decode using multiple keys (VidPlay/vidplay pattern).
    """
    current = data
    for key in keys:
        key_bytes = bytes(key, 'utf-8')
        s = bytearray(range(256))
        j = 0
        for i in range(256):
            j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
            s[i], s[j] = s[j], s[i]
        
        decoded = bytearray(len(current))
        i = 0
        k = 0
        for index in range(len(current)):
            i = (i + 1) & 0xff
            k = (k + s[i]) & 0xff
            s[i], s[k] = s[k], s[i]
            t = (s[i] + s[k]) & 0xff
            if isinstance(current[index], str):
                decoded[index] = ord(current[index]) ^ s[t]
            else:
                decoded[index] = current[index] ^ s[t]
        current = decoded
    
    return current
