# Пояснення до діаграми `activity_parse_pipeline.puml`

## Що показує ця діаграма

Ця activity-діаграма показує **загальний алгоритм парсингу резюме**.  
Це одна з найважливіших діаграм у всій документації, бо вона описує послідовність дій сервісу від отримання HTTP-запиту до збереження результату в базу даних.

---

## Як читати діаграму

Activity diagram читається зверху вниз:

1. початок процесу;
2. послідовні кроки;
3. перевірки через умовні переходи;
4. завершення процесу.

Точки розгалуження показують, що в алгоритмі є умови, наприклад:

- чи є потрібний header;
- чи підтримується тип файлу;
- чи файл не порожній;
- чи виникла помилка під час парсингу.

Для зручності орієнтації варто читати українське пояснення разом із короткими англійськими назвами блоків, які стоять на самій діаграмі, наприклад:

- отримання запиту (`Receive POST /resumes/parse`);
- перевірка заголовка (`Read trusted user_id header`);
- валідація файлу (`Validate file extension and MIME type`);
- створення запису (`Create resume row in DB`);
- читання вмісту (`Read uploaded file bytes`);
- вибір extractor-а (`Choose extractor by extension`);
- попередня обробка (`Preprocess blocks`);
- визначення layout (`Detect layout and reorder blocks`);
- пошук секцій (`Detect section headers`);
- побудова меж секцій (`Build section boundaries`);
- парсинг секцій (`Parse ... section`);
- fallback (`Apply fallback manager`);
- перевірка якості (`Run quality checker`);
- фіналізація (`Save final content to DB`, `Return ...`).

---

## Послідовне пояснення алгоритму

### 1. Отримання запиту

Сервіс приймає `POST /resumes/parse` (`Receive POST /resumes/parse`).

Разом із файлом він очікує trusted header з `user_id` (`Read trusted user_id header`), який передає gateway.

### 2. Перевірка заголовка

Якщо header відсутній (`Header present? -> no`), сервіс одразу повертає помилку `400`.

Це потрібно, бо сервіс довіряє gateway і не виконує власну автентифікацію.

### 3. Валідація файлу

Перевіряється (`Validate file extension and MIME type`):

- розширення файлу;
- MIME type.

Допустимі лише `PDF` та `DOCX`.

### 4. Створення початкового запису

Якщо файл коректний, сервіс створює запис у БД (`Create resume row in DB`) зі статусом:

- `parse_status = processing`

Це дозволяє зафіксувати сам факт початку обробки.

### 5. Читання байтів файлу

Сервіс зчитує вміст файла в пам’ять (`Read uploaded file bytes`).

Якщо файл порожній (`File empty? -> yes`):

- статус стає `failed`;
- записується `parse_error`;
- зберігається warning;
- повертається помилка `400`.

### 6. Вибір extractor-а

Алгоритм переходить до extraction (`Choose extractor by extension`).

Якщо файл PDF (`PDF? -> yes`):

- використовується `PDFExtractor`

Якщо DOCX (`PDF? -> no`, тобто DOCX-гілка):

- використовується `DOCXExtractor`

### 7. Попередня обробка

Після extraction виконується preprocess (`Preprocess blocks`):

- очищення блоків;
- нормалізація bullet-ів;
- відновлення логічної структури тексту.

### 8. Layout analysis

Сервіс визначає layout документа (`Detect layout and reorder blocks`), наприклад:

- `single_column`
- `two_column`

і за потреби перебудовує порядок читання блоків.

### 9. Detection секцій

Потім сервіс (`Detect section headers`, `Build section boundaries`):

- знаходить заголовки секцій;
- будує межі секцій;
- прив’язує блоки до відповідних частин резюме.

### 10. Парсинг секцій

Кожна логічна секція парситься окремо (`Parse contact section`, `Parse summary section`, `Parse experience section` і так далі):

- contact
- summary
- experience
- education
- skills
- certifications
- languages
- projects

### 11. Fallback

Після основного парсингу запускається fallback-логіка (`Apply fallback manager`), якщо результат виявився слабким або неповним.

### 12. Quality checking

Сервіс оцінює, чи парсинг вийшов достатньо якісним (`Run quality checker`):

- чи є контактні дані;
- чи знайдені основні секції;
- чи не забагато `unassigned_blocks`.

### 13. Фіналізація

Якщо критичної помилки не виникло (`Parsing exception? -> no`):

- `parse_status = completed`
- результат записується у БД (`Save final content to DB`)
- API повертає короткий summary (`Return resume_id, partial_parse, warnings, major_sections_found`)

Якщо виникла помилка (`Parsing exception? -> yes`):

- `parse_status = failed`
- фіксується `parse_error`
- повертається failed-result (`Return failed content`)

---

## Що ця діаграма показує з точки зору алгоритмів

Ця діаграма демонструє, що в сервісі реалізовано **багатокроковий алгоритм обробки документа**, а не просто збереження файлу чи простий CRUD.

Вона показує:

- послідовність етапів;
- наявність умов;
- можливість помилки;
- повернення до резервної логіки через fallback.

---

## Як пояснювати цю діаграму на захисті

Можна казати так:

> Ця activity-діаграма показує повний алгоритм роботи сервісу. Спочатку перевіряється коректність запиту, потім створюється запис у базі, виконується extraction тексту, його попередня обробка, визначення секцій, спеціалізований парсинг, fallback-обробка та оцінка якості. Після цього фінальний JSON зберігається у PostgreSQL.
