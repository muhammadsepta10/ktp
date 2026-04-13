# Issue #5: Bug Fix - API OCR Response dan PaddleOCR show_log Error

## Deskripsi Masalah

Ketika memanggil API `POST /api/v1/ocr`, terdapat 2 bug:

### Bug 1: Response Code Tidak Sesuai
- **Masalah**: Ketika terjadi error pada proses OCR, API masih mengembalikan status code `201 (Created)` padahal seharusnya error.
- **Ekspektasi**: 
  - `4xx` untuk error yang disebabkan kesalahan user (invalid file, format tidak didukung)
  - `5xx` untuk error dari server (gagal proses image, internal error)
- **Lokasi**: `api/app/routers/ocr.py`

### Bug 2: PaddleOCR show_log Error
- **Masalah**: Error `Failed to process image: Unknown argument: show_log`
- **Penyebab**: Parameter `show_log` tidak lagi didukung di versi PaddleOCR terbaru
- **Lokasi**: `api/app/services/ocr_service.py`

---

## Tahapan Implementasi

### Tahap 1: Perbaiki Error show_log di OcrService

**File yang diubah:** `api/app/services/ocr_service.py`

**Langkah-langkah:**
1. Buka file `api/app/services/ocr_service.py`
2. Cari bagian inisialisasi PaddleOCR di method `ocr` (property):
   ```python
   @property
   def ocr(self) -> PaddleOCR:
       if self._ocr is None:
           self._ocr = PaddleOCR(
               use_angle_cls=True,
               lang=self.lang,
               show_log=False,  # <-- HAPUS BARIS INI
           )
       return self._ocr
   ```
3. Hapus parameter `show_log=False` karena tidak didukung di versi PaddleOCR terbaru
4. Untuk menonaktifkan logging, gunakan environment variable atau paddlepaddle logging config:
   ```python
   import logging
   logging.getLogger("ppocr").setLevel(logging.WARNING)
   ```

**Kode Akhir:**
```python
import logging
from paddleocr import PaddleOCR
from PIL import Image
import io
from typing import Optional
from app.config import settings

# Disable PaddleOCR verbose logging
logging.getLogger("ppocr").setLevel(logging.WARNING)


class OcrService:
    def __init__(self, lang: str = None):
        self.lang = lang or settings.OCR_LANGUAGE
        self._ocr = None

    @property
    def ocr(self) -> PaddleOCR:
        if self._ocr is None:
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
            )
        return self._ocr
    # ... sisa kode tetap sama
```

---

### Tahap 2: Perbaiki Response Code di Router

**File yang diubah:** `api/app/routers/ocr.py`

**Langkah-langkah:**
1. Buka file `api/app/routers/ocr.py`
2. Cari endpoint `POST /api/v1/ocr` (function `create_ocr`)
3. Ubah logika penanganan error OCR dari:
   ```python
   # Run OCR
   try:
       extracted_text = ocr_service.extract_text_from_bytes(content)
       ocr_result.extracted_text = extracted_text
       ocr_result.status = "completed"
   except ValueError as e:
       ocr_result.status = "failed"
       ocr_result.extracted_text = str(e)

   await db.commit()
   await db.refresh(ocr_result)

   return ocr_result
   ```

4. Menjadi:
   ```python
   # Run OCR
   try:
       extracted_text = ocr_service.extract_text_from_bytes(content)
       ocr_result.extracted_text = extracted_text
       ocr_result.status = "completed"
   except ValueError as e:
       ocr_result.status = "failed"
       ocr_result.extracted_text = str(e)
       await db.commit()
       await db.refresh(ocr_result)
       raise HTTPException(
           status_code=500,
           detail=f"Failed to process image: {str(e)}"
       )

   await db.commit()
   await db.refresh(ocr_result)

   return ocr_result
   ```

**Penjelasan:**
- Ketika OCR gagal memproses image, tetap simpan record ke database dengan status "failed"
- Kemudian raise HTTPException dengan status 500 (Internal Server Error)
- Status 500 karena ini adalah error dari server side (PaddleOCR gagal memproses)

---

### Tahap 3: Testing

**Langkah-langkah:**
1. Jalankan server:
   ```bash
   cd /Users/redbox/Documents/project/self-project/PaddleOCR/api
   uvicorn main:app --reload
   ```

2. Test dengan foto KTP dari folder `/ktp`:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ocr" \
     -H "accept: application/json" \
     -F "file=@../ktp/1740113924-5CB1MPSO56.jpg"
   ```

3. **Ekspektasi hasil sukses:**
   - Status code: `201`
   - Response body: JSON dengan `status: "completed"` dan `extracted_text` berisi teks terekstrak

4. **Test dengan file invalid (opsional):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ocr" \
     -H "accept: application/json" \
     -F "file=@invalid.txt"
   ```
   - Ekspektasi: Status code `400` dengan pesan "Invalid file type"

---

## Checklist Implementasi

- [ ] Hapus parameter `show_log=False` di `ocr_service.py`
- [ ] Tambahkan logging config untuk disable verbose log PaddleOCR
- [ ] Ubah penanganan error di `ocr.py` agar raise HTTPException 500
- [ ] Test endpoint dengan foto KTP
- [ ] Verifikasi response code berubah dari 201 ke 500 saat error
- [ ] Verifikasi tidak ada lagi error "Unknown argument: show_log"

---

## Files yang Perlu Diubah

| File | Perubahan |
|------|-----------|
| `api/app/services/ocr_service.py` | Hapus `show_log=False`, tambah logging config |
| `api/app/routers/ocr.py` | Ubah error handling untuk raise HTTPException 500 |

---

## Referensi

- Folder foto KTP untuk testing: `/Users/redbox/Documents/project/self-project/PaddleOCR/ktp/`
- Contoh file KTP: `1740113924-5CB1MPSO56.jpg`
