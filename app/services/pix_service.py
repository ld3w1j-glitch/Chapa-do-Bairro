"""Utilitários simples para gerar código PIX Copia e Cola (BR Code).

Não confirma pagamento automaticamente. Para confirmação real é necessário usar
um provedor como Mercado Pago, Gerencianet/Efi, PagSeguro ou banco com webhook.
"""
import re


def _only_ascii(text: str, max_len: int) -> str:
    text = (text or "").strip()
    replacements = {
        "á": "a", "à": "a", "ã": "a", "â": "a", "ä": "a",
        "é": "e", "ê": "e", "è": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "õ": "o", "ô": "o", "ö": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
    }
    text = "".join(replacements.get(ch.lower(), ch) for ch in text)
    text = re.sub(r"[^A-Za-z0-9 .@_\-+/]", "", text).upper()
    return text[:max_len]


def _field(field_id: str, value: str) -> str:
    value = str(value or "")
    return f"{field_id}{len(value):02d}{value}"


def _crc16(payload: str) -> str:
    polynomial = 0x1021
    result = 0xFFFF
    for byte in payload.encode("utf-8"):
        result ^= byte << 8
        for _ in range(8):
            if result & 0x8000:
                result = ((result << 1) ^ polynomial) & 0xFFFF
            else:
                result = (result << 1) & 0xFFFF
    return f"{result:04X}"


def build_pix_payload(*, pix_key: str, amount: float, merchant_name: str, merchant_city: str = "MONTES CLAROS", txid: str = "CHAPA") -> str:
    """Gera payload PIX estático compatível com QR Code."""
    pix_key = (pix_key or "").strip()
    if not pix_key:
        return ""

    merchant_account = _field("00", "BR.GOV.BCB.PIX") + _field("01", pix_key[:77])
    payload = "".join([
        _field("00", "01"),
        _field("26", merchant_account),
        _field("52", "0000"),
        _field("53", "986"),
        _field("54", f"{float(amount or 0):.2f}"),
        _field("58", "BR"),
        _field("59", _only_ascii(merchant_name or "CHAPA DO BAIRRO", 25)),
        _field("60", _only_ascii(merchant_city or "MONTES CLAROS", 15)),
        _field("62", _field("05", _only_ascii(txid or "CHAPA", 25))),
    ])
    payload_to_crc = payload + "6304"
    return payload_to_crc + _crc16(payload_to_crc)
