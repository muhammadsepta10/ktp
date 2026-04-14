import json
import logging
import httpx
from typing import Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# JSON Schema yang diharapkan dari model AI
KTP_JSON_SCHEMA = {
    "nik": "string (16 digit) atau null",
    "name": "string atau null",
    "province": "string atau null",
    "city": "string atau null",
    "sub_district": "string atau null",
    "village": "string atau null",
    "address": "string atau null",
    "rt": "string (3 digit) atau null",
    "rw": "string (3 digit) atau null",
    "virgin": "string (LAKI-LAKI/PEREMPUAN) atau null",
    "birthplace": "string atau null",
    "birthdate": "string (DD-MM-YYYY) atau null",
    "religion": "string atau null",
    "status": "string atau null",
    "job": "string atau null",
    "citizenship": "string (WNI/WNA) atau null",
    "valid_until": "string atau null",
}

# System prompt dengan instruksi ketat dan few-shot examples
SYSTEM_PROMPT = """Kamu adalah asisten yang mengekstrak data dari hasil OCR KTP Indonesia.

ATURAN KETAT:
1. Output HARUS berupa JSON valid, tanpa teks tambahan apapun
2. Jangan menebak jika data tidak yakin, gunakan null
3. Perbaiki typo yang jelas dari hasil OCR (contoh: huruf O -> angka 0, huruf I -> angka 1)
4. NIK harus 16 digit angka, jika tidak valid gunakan null
5. Tanggal lahir format DD-MM-YYYY
6. Jenis kelamin hanya LAKI-LAKI atau PEREMPUAN
7. Kewarganegaraan hanya WNI atau WNA
8. Jangan sertakan label field (seperti "Nama:", "NIK:") di dalam value

JSON Schema yang HARUS diikuti:
{
    "nik": "string (16 digit) atau null",
    "name": "string atau null",
    "province": "string atau null",
    "city": "string atau null",
    "sub_district": "string atau null",
    "village": "string atau null",
    "address": "string atau null",
    "rt": "string (3 digit) atau null",
    "rw": "string (3 digit) atau null",
    "virgin": "string (LAKI-LAKI/PEREMPUAN) atau null",
    "birthplace": "string atau null",
    "birthdate": "string (DD-MM-YYYY) atau null",
    "religion": "string atau null",
    "status": "string atau null",
    "job": "string atau null",
    "citizenship": "string (WNI/WNA) atau null",
    "valid_until": "string atau null"
}

CONTOH 1:
Input OCR:
PROVINSI DKI JAKARTA
KOTA JAKARTA PUSAT
NIK: 3171O34567890001
Nama: BUDI SANT0SO
Tempat/TglLahir: JAKARTA,O1-01-199O
Jenis Kelamin: LAKI-LAKI
Alamat: JL. SUDIRMAN NO. 1
RT/RW: 001/002
Kel/Desa: PEJOMPONGAN
Kecamatan: BENDUNGAN HILIR
Agama: ISLAM
Status Perkawinan: BELUM KAWIN
Pekerjaan: KARYAWAN SWASTA
Kewarganegaraan: WNI
Berlaku Hingga: SEUMUR HIDUP

Output:
{"nik": "3171034567890001", "name": "BUDI SANTOSO", "province": "DKI JAKARTA", "city": "JAKARTA PUSAT", "sub_district": "BENDUNGAN HILIR", "village": "PEJOMPONGAN", "address": "JL. SUDIRMAN NO. 1", "rt": "001", "rw": "002", "virgin": "LAKI-LAKI", "birthplace": "JAKARTA", "birthdate": "01-01-1990", "religion": "ISLAM", "status": "BELUM KAWIN", "job": "KARYAWAN SWASTA", "citizenship": "WNI", "valid_until": "SEUMUR HIDUP"}

CONTOH 2:
Input OCR:
PROVINSI BANTEN
KABUPATEN TANGERANG
NIK
:36030367II82000l
Nama
ELISABET ANUR
Tempat/TglLahir
:MANGGARAI,27-I1-1982
Jenis Kelamin
:PEREMPUAN

Output:
{"nik": "3603036711820001", "name": "ELISABET ANUR", "province": "BANTEN", "city": "KABUPATEN TANGERANG", "sub_district": null, "village": null, "address": null, "rt": null, "rw": null, "virgin": "PEREMPUAN", "birthplace": "MANGGARAI", "birthdate": "27-11-1982", "religion": null, "status": null, "job": null, "citizenship": null, "valid_until": null}
"""


def _validate_ktp_data(data: Dict) -> tuple[bool, list[str]]:
    """
    Validasi hasil parsing KTP.

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []

    # Validasi NIK: harus 16 digit
    nik = data.get("nik")
    if nik is not None:
        if not isinstance(nik, str) or len(nik) != 16 or not nik.isdigit():
            errors.append(f"NIK tidak valid: '{nik}' (harus 16 digit angka)")

    # Validasi tanggal lahir: format DD-MM-YYYY
    birthdate = data.get("birthdate")
    if birthdate is not None:
        import re
        if not re.match(r"^\d{2}-\d{2}-\d{4}$", birthdate):
            errors.append(f"Tanggal lahir tidak valid: '{birthdate}' (harus DD-MM-YYYY)")
        else:
            # Validasi tanggal logis
            try:
                from datetime import datetime
                datetime.strptime(birthdate, "%d-%m-%Y")
            except ValueError:
                errors.append(f"Tanggal lahir tidak logis: '{birthdate}'")

    # Validasi jenis kelamin
    virgin = data.get("virgin")
    if virgin is not None and virgin not in ["LAKI-LAKI", "PEREMPUAN"]:
        errors.append(f"Jenis kelamin tidak valid: '{virgin}'")

    # Validasi kewarganegaraan
    citizenship = data.get("citizenship")
    if citizenship is not None and citizenship not in ["WNI", "WNA"]:
        errors.append(f"Kewarganegaraan tidak valid: '{citizenship}'")

    # Validasi RT/RW: harus 3 digit
    for field in ["rt", "rw"]:
        val = data.get(field)
        if val is not None:
            if not isinstance(val, str) or not val.isdigit():
                errors.append(f"{field.upper()} tidak valid: '{val}' (harus digit)")

    return len(errors) == 0, errors


def _extract_json_from_response(text: str) -> Optional[Dict]:
    """
    Ekstrak JSON dari response model AI.
    Menangani kasus dimana model menambahkan teks di luar JSON.
    """
    # Coba parse langsung
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Coba cari JSON block dalam markdown code block
    import re
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Coba cari { ... } pattern
    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


async def parse_ktp_with_ai(raw_text: str) -> Dict[str, Optional[str]]:
    """
    Parse raw OCR text menggunakan model AI (Ollama + Qwen3:14b).
    Dengan retry jika validasi gagal.

    Args:
        raw_text: Teks mentah hasil OCR

    Returns:
        Dictionary dengan field-field KTP yang sudah diparsing

    Raises:
        ValueError: Jika model AI gagal menghasilkan output valid setelah retry
    """
    expected_keys = [
        "nik", "name", "province", "city", "sub_district", "village",
        "address", "rt", "rw", "virgin", "birthplace", "birthdate",
        "religion", "status", "job", "citizenship", "valid_until"
    ]

    last_errors = []

    for attempt in range(settings.AI_MAX_RETRIES + 1):
        try:
            # Buat prompt
            user_prompt = f"Ekstrak data KTP dari hasil OCR berikut:\n\n{raw_text}"

            # Tambahkan feedback dari validasi sebelumnya jika retry
            if attempt > 0 and last_errors:
                user_prompt += f"\n\nPERBAIKAN: Respons sebelumnya memiliki error berikut, tolong perbaiki:\n"
                for err in last_errors:
                    user_prompt += f"- {err}\n"

            # Panggil Ollama API
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature untuk konsistensi
                        },
                    },
                )
                response.raise_for_status()

            # Parse response
            result = response.json()
            ai_text = result.get("message", {}).get("content", "")

            logger.info(f"AI response (attempt {attempt + 1}): {ai_text[:200]}...")

            # Ekstrak JSON dari response
            parsed = _extract_json_from_response(ai_text)
            if parsed is None:
                last_errors = ["Response bukan JSON valid"]
                logger.warning(f"AI returned invalid JSON (attempt {attempt + 1})")
                continue

            # Pastikan semua key ada (isi null jika tidak ada)
            for key in expected_keys:
                if key not in parsed:
                    parsed[key] = None

            # Validasi data
            is_valid, errors = _validate_ktp_data(parsed)
            if is_valid:
                # Konversi None ke string kosong untuk kompatibilitas dengan DB
                for key in expected_keys:
                    if parsed[key] is None:
                        parsed[key] = ""

                parsed["raw_text"] = raw_text
                return parsed

            last_errors = errors
            logger.warning(f"Validation failed (attempt {attempt + 1}): {errors}")

        except httpx.TimeoutException:
            last_errors = ["Request timeout ke Ollama"]
            logger.error(f"Ollama timeout (attempt {attempt + 1})")
        except httpx.HTTPStatusError as e:
            last_errors = [f"Ollama HTTP error: {e.response.status_code}"]
            logger.error(f"Ollama HTTP error (attempt {attempt + 1}): {e}")
        except Exception as e:
            last_errors = [f"Unexpected error: {str(e)}"]
            logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")

    # Semua retry gagal, raise error
    raise ValueError(
        f"AI parsing gagal setelah {settings.AI_MAX_RETRIES + 1} percobaan. "
        f"Errors terakhir: {last_errors}"
    )
