# Пояснення до діаграми `activity_experience_parsing.puml`

## Що показує ця діаграма

Ця activity-діаграма описує алгоритм парсингу секції `experience`.

Це одна з найцікавіших ділянок сервісу, бо секція досвіду роботи зазвичай:

- найоб’ємніша;
- найменш стандартизована;
- найбільш схильна до помилок парсингу.

---

## Чому цей алгоритм важливий

Для кожної позиції роботи сервіс намагається витягнути:

- `company`
- `title`
- `start_date`
- `end_date`
- `date_range_raw`
- `location`
- `bullets`
- `description_raw`
- `raw_text`

Складність у тому, що ці дані в різних CV можуть бути оформлені дуже по-різному.

На самій діаграмі основні блоки названі так:

- `Receive blocks of experience section`
- `Merge blocks into section text`
- `Split section into candidate job entries`
- `Take next candidate entry`
- `Extract raw_text for current entry`
- `Split entry into lines`
- `Find header lines`
- `Search for date range using regex`
- `Date range found?`
- `Heuristically classify header text`
- `Separate bullet lines from plain text lines`
- `Bullet lines found?`
- `Non-bullet descriptive text remains?`
- `Create ExperienceEntry`
- `Append entry to experience[]`
- `Return parsed list of ExperienceEntry`

Нижче ті самі кроки пояснені українською, але з коротким англійським дублем у дужках.

---

## Послідовне пояснення алгоритму

### 1. Отримання секції `experience`

На вхід алгоритм отримує блоки, які вже були віднесені до секції досвіду роботи (`Receive blocks of experience section`).

### 2. Об’єднання в текст секції

Блоки секції зводяться до цілісного тексту (`Merge blocks into section text`), який далі зручно аналізувати.

### 3. Розбиття на кандидатні записи роботи

Вся секція ділиться на `candidate job entries` (`Split section into candidate job entries`), тобто на припущення, де починається нова позиція роботи.

Це один із найважливіших кроків, бо якщо межі позицій визначені погано, далі поля теж будуть неправильними.

### 4. Обробка кожного запису окремо

Далі алгоритм циклічно проходить по кожному candidate entry (`Take next candidate entry`).

Для кожного запису формується `raw_text` (`Extract raw_text for current entry`), щоб зберегти повний сирий текст цієї позиції.

### 5. Розбиття запису на рядки

Запис ділиться на окремі рядки (`Split entry into lines`).

Це потрібно для того, щоб відокремити:

- header-зону;
- bullets;
- описовий текст.

### 6. Пошук header lines

Алгоритм намагається знайти верхню частину запису (`Find header lines`), де, як правило, містяться:

- назва компанії;
- посада;
- дати;
- локація.

### 7. Пошук дат

Потім за допомогою регулярних виразів шукається діапазон дат (`Search for date range using regex`).

Якщо діапазон знайдено (`Date range found? -> yes`):

- витягуються `start_date`;
- `end_date`;
- `date_range_raw`.

Якщо дати не знайдено (`Date range found? -> no`):

- ці поля залишаються `null`.

### 8. Евристична класифікація header-частини

Після цього сервіс намагається розкласти header (`Heuristically classify header text`) на:

- `company`
- `title`
- `location`

Це виконується не за жорстким шаблоном, а за набором правил та евристик.

### 9. Відокремлення bullets

Далі сервіс визначає, які рядки є bullet-пунктами (`Separate bullet lines from plain text lines`).

Якщо bullets знайдено (`Bullet lines found? -> yes`):

- вони зберігаються в `bullets[]`

Інакше (`Bullet lines found? -> no`):

- `bullets[]` залишається порожнім.

### 10. Визначення `description_raw`

Якщо після виділення bullets лишився текст, який не є bullet-ами, але є змістовним описом (`Non-bullet descriptive text remains? -> yes`), він зберігається в `description_raw`.

Це корисно для випадків, коли досвід оформлений не як список, а як абзац.

### 11. Створення `ExperienceEntry`

Після збору полів формується один структурований запис `ExperienceEntry` (`Create ExperienceEntry`).

### 12. Додавання до результату

Цей запис додається до масиву `experience[]` (`Append entry to experience[]`).

### 13. Випадок слабкого розбору

Якщо надійно побудувати записи не вдалося (`No reliable entries built? -> yes`):

- алгоритм не вигадує поля;
- зберігає raw text;
- або залишає можливість для fallback-логіки.

### 14. Повернення результату

У фіналі алгоритм повертає список `ExperienceEntry` (`Return parsed list of ExperienceEntry`).

---

## Який метод тут використовується

Тут використовується **евристичний rule-based parsing**.

Це означає, що сервіс не використовує модель машинного навчання, а працює через:

- правила;
- регулярні вирази;
- структуру рядків;
- типові ознаки записів досвіду.

---

## Чому це хороший приклад алгоритму для документації

Цей алгоритм добре показує, що сервіс:

- виконує реальний аналіз тексту;
- приймає рішення на основі ознак;
- працює з невизначеними структурами;
- уміє зберігати сирий текст, якщо структура неповна.

---

## Як пояснювати цю діаграму на захисті

Можна казати так:

> Секція `experience` розбирається евристично. Спочатку вона ділиться на окремі позиції роботи, потім для кожної позиції визначаються дати, header-частина, company, title, location, bullets і descriptive text. Якщо повний розбір неможливий, сервіс не вигадує дані, а зберігає сирий текст для подальшого використання.
