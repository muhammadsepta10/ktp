import re
from typing import Dict

def parse_ktp_text(raw_text: str) -> Dict[str, str]:
    """
    Parse raw OCR text menjadi field-field KTP.
    Return dictionary dengan semua field KTP.
    """
    # Helper function
    def find(pattern, text, default=""):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else default

    # Patterns (sederhana, bisa diimprove)
    nik = find(r"NIK\s*:?\s*([0-9]{16})", raw_text)
    name = find(r"Nama\s*:?\s*([A-Z\s']+)", raw_text)
    city = find(r"KOTA\s*:?\s*([A-Z\s']+)", raw_text)
    province = find(r"PROVINSI\s*:?\s*([A-Z\s']+)", raw_text)
    sub_district = find(r"KEC(?:AMATAN)?\s*:?\s*([A-Z\s']+)", raw_text)
    village = find(r"KEL(?:URAHAN)?(?:/DESA)?\s*:?\s*([A-Z\s']+)", raw_text)
    rt = find(r"RT\s*:?\s*([0-9]{1,3})", raw_text)
    rw = find(r"RW\s*:?\s*([0-9]{1,3})", raw_text)
    address = find(r"Alamat\s*:?\s*(.+)", raw_text)
    virgin = find(r"Jenis Kelamin\s*:?\s*([A-Z\s]+)", raw_text)
    birthplace = find(r"Tempat/Tgl Lahir\s*:?\s*([A-Z\s']+)", raw_text)
    birthdate = find(r"Tempat/Tgl Lahir.*?(\d{2}-\d{2}-\d{4})", raw_text)
    religion = find(r"Agama\s*:?\s*([A-Z\s]+)", raw_text)
    status = find(r"Status Perkawinan\s*:?\s*([A-Z\s]+)", raw_text)
    job = find(r"Pekerjaan\s*:?\s*([A-Z\s']+)", raw_text)
    citizenship = find(r"Kewarganegaraan\s*:?\s*([A-Z]+)", raw_text)
    valid_until = find(r"Berlaku Hingga\s*:?\s*([A-Z\s0-9-]+)", raw_text)

    return {
        "raw_text": raw_text,
        "nik": nik,
        "name": name,
        "city": city,
        "province": province,
        "sub_district": sub_district,
        "village": village,
        "rt": rt,
        "rw": rw,
        "address": address,
        "virgin": virgin,
        "birthplace": birthplace,
        "birthdate": birthdate,
        "religion": religion,
        "status": status,
        "job": job,
        "citizenship": citizenship,
        "valid_until": valid_until,
    }
