# Пояснення до діаграми `sequence_parse_resume.puml`

## Що показує ця діаграма

Це sequence diagram, яка показує покрокову взаємодію між компонентами під час виконання запиту:

- `POST /resumes/parse`

На відміну від activity-діаграми, тут акцент зроблено не на алгоритмі як такому, а на **порядку викликів між компонентами**.

---

## Учасники діаграми

На діаграмі показані:

- `Client`
- `API Gateway`
- `FastAPI endpoint`
- `ResumeRepository`
- `ResumePipeline`
- `PDF/DOCX Extractor`
- `Cleaner + Layout + Section Detector`
- `Section Parsers`
- `Fallback + Quality`
- `PostgreSQL`

---

## Послідовність взаємодії

### 1. Клієнт надсилає резюме

Клієнт звертається до gateway і передає:

- файл резюме;
- контекст користувача.

### 2. Gateway передає запит у сервіс

Gateway пересилає multipart/form-data і trusted header з `user_id`.

### 3. Endpoint виконує валідацію

`parse_resume()` перевіряє:

- header;
- розширення;
- MIME type.

### 4. Створення запису в БД

Endpoint викликає `ResumeRepository.create_resume()`.

Repository виконує `INSERT` у PostgreSQL і повертає `resume_id`.

### 5. Читання файлу і запуск pipeline

Endpoint зчитує байти файлу й передає їх у `ResumePipeline.parse()`.

### 6. Extraction

Pipeline вибирає правильний extractor:

- PDF
- або DOCX

і отримує текстові блоки.

### 7. Detection and preparation

Потім pipeline передає блоки в модулі:

- cleaner;
- layout detector;
- section detector.

### 8. Parsing секцій

Після цього викликаються section parsers, які формують структурований `ResumeContent`.

### 9. Fallback і quality

Потім виконується:

- fallback logic;
- quality checking.

### 10. Повернення результату в endpoint

Pipeline повертає:

- `ResumeContent`
- `QualityReport`

### 11. Оновлення запису в БД

Endpoint викликає `update_content()`, і repository робить `UPDATE` у PostgreSQL.

### 12. HTTP-відповідь

Після цього endpoint повертає короткий parse summary, який через gateway доходить до клієнта.

---

## Чому ця діаграма корисна

Вона добре показує:

- хто кого викликає;
- у якому порядку це відбувається;
- де проходить межа між API, pipeline і persistence.

---

## Як пояснювати на захисті

Можна казати так:

> Sequence-діаграма показує послідовність викликів під час обробки `POST /resumes/parse`. Endpoint спочатку створює запис у базі, потім передає файл у `ResumePipeline`, який виконує extraction, detection, parsing і quality checking. Після цього результат зберігається у PostgreSQL, а клієнт отримує коротку HTTP-відповідь.
