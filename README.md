# AdWall CLI

CLI для официального read-only [AdWall Agent API](https://adwall.io/) v1.1.0.
Он ориентирован на AI-агентов: выдаёт JSON, поддерживает все официальные
фильтры поиска, cursor pagination и безопасно передаёт detail grant.

[English documentation](docs/README.en.md) ·
[Русское руководство](docs/README.ru.md) ·
[Skill для агентов](skills/adwall-api/SKILL.md) ·
[OpenAPI](specs/openapi.json)

API работает по REST, использует Bearer-аутентификацию и не изменяет данные
AdWall. Настраиваемый базовый URL: `https://adwall.io/api`.

## Быстрый старт

Требуется Python 3.10+ и Agent API key из кабинета AdWall.

```powershell
git clone https://github.com/dvygolov/adwall-cli.git
cd adwall-cli
Copy-Item .env.example .env
# Запишите ключ в ADWALL_API_KEY. Не публикуйте файл .env.

python -m venv .venv
.\.venv\Scripts\python -m pip install .
.\.venv\Scripts\adwall auth status
.\.venv\Scripts\adwall creatives search --q casino --geo CZ --limit 10
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/adwall auth status
.venv/bin/adwall creatives search --q casino --geo CZ --limit 10
```

Ключ также можно передать через переменную окружения `ADWALL_API_KEY`.

CLI добавляет к базовому URL официальный OpenAPI path `/api/v1/...`, поэтому
полный URL поиска — `https://adwall.io/api/api/v1/creatives`. Двойной `/api`
здесь корректен; не сокращайте базовый URL до одного host.

## Команды

```text
adwall auth status
adwall creatives search [ФИЛЬТРЫ]
adwall creatives get LIBRARY_ID [--detail-grant GRANT]
adwall creatives instances LIBRARY_ID --detail-grant GRANT [ПАГИНАЦИЯ]
adwall categories list
adwall api capabilities|usage|openapi
```

Глобальные параметры: `--env-file`, `--compact`, `--jsonl`,
`--response-meta`, `--version`.

## Поиск

```powershell
adwall creatives search `
  --q casino `
  --advertiser Example `
  --geo CZ `
  --format video `
  --platform facebook `
  --running-from 2026-07-01 `
  --running-to 2026-08-01 `
  --limit 10
```

Поддерживаются официальные параметры: `q`, `advertiser`, `target_url`,
`link_text`, `image_text`, `geo`, `language`, `platform`, `format`, `cta`,
`category_id`, `published_from`, `published_to`, `running_from`, `running_to`,
`domain`, `tld`, `app`, `app_platform`, `special_category`, `countries_count`,
`sort`, `order`, `limit`, `cursor`. В CLI подчёркивания заменяются дефисами,
например `--target-url` и `--category-id`.

Максимальный `limit` — 50. По умолчанию результаты сортируются от новых к
старым. Сортировка по reach применима только к креативам из ЕС.

Для продолжения передайте `nextCursor` из ответа:

```powershell
adwall creatives search --q Plinko --limit 25 --cursor NEXT_CURSOR
```

Или используйте ограниченный автоматический обход:

```powershell
adwall --jsonl creatives search --q Plinko --limit 25 --all-pages --max-pages 3
```

## Detail grant

Каждый объект поисковой выдачи содержит `detailGrant`. Передавайте его при
запросе detail или same-fingerprint instances для этого же `libraryId`:

```powershell
adwall creatives get LIBRARY_ID --detail-grant DETAIL_GRANT
adwall creatives instances LIBRARY_ID --detail-grant DETAIL_GRANT --limit 20
```

CLI отправляет значение в заголовке `X-AdWall-Detail-Grant`. Это подтверждает,
что креатив уже был получен поиском, и предотвращает повторное списание за
detail/instances. Для `instances` grant обязателен.

## Справочные endpoints

```powershell
adwall categories list
adwall api capabilities
adwall api usage
adwall api openapi
```

`capabilities` полезно проверять перед построением запроса, `usage` показывает
текущее потребление, а `openapi` возвращает актуальную схему сервера.

Наблюдаемый rate limit — 60 запросов в минуту. При `429` дождитесь указанного
сервером интервала; не запускайте параллельный обход лимита.
Добавьте `--response-meta`, чтобы получить доступные rate-limit headers вместе
с данными ответа.

## Skill

`skills/adwall-api/` самодостаточен: внутри `cli/` лежит копия CLI.

```powershell
python .\skills\adwall-api\scripts\adwall.py auth status
python .\skills\adwall-api\scripts\adwall.py creatives search --q Plinko --limit 10
```

## Проверка

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
python scripts/sync_skill_cli.py --check
python C:\Users\ratta\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\adwall-api
```
