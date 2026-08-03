# AdWall CLI

Самодостаточный CLI для GraphQL API, которые использует веб-приложение
[AdWall](https://app.adwall.io/). Он ориентирован на AI-агентов: JSON по
умолчанию, typed-команды для поиска и кабинета, cursor pagination, собственная
token-сессия и явное подтверждение мутаций.

[English documentation](docs/README.en.md) ·
[Русское руководство](docs/README.ru.md) ·
[Skill для агентов](skills/adwall-api/SKILL.md) ·
[Карта API](specs/internal-api.json)

> Это не официальный Public API. Схема и операции восстановлены по живому
> интерфейсу, first-party JavaScript и GraphQL introspection AdWall 3 августа
> 2026 года. Используйте CLI только со своим аккаунтом и соблюдайте тариф,
> лимиты и условия сервиса.

## Быстрый старт

Требуется Python 3.10+.

```powershell
git clone https://github.com/dvygolov/adwall-cli.git
cd adwall-cli
Copy-Item .env.example .env
# Заполните ADWALL_EMAIL и ADWALL_PASSWORD

python -m venv .venv
.\.venv\Scripts\python -m pip install .
.\.venv\Scripts\adwall auth login
.\.venv\Scripts\adwall creatives search --query casino --country CZ --limit 10
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/adwall auth login
```

Успешный вход создаёт `ADWALL_SESSION_FILE` с парой access/refresh token.
Пароль остаётся в `.env`, не попадает в аргументы процесса и не сохраняется в
файле сессии. При `UNAUTHENTICATED` CLI обновляет токены и повторяет запрос один
раз.

## Покрытие

```text
adwall auth login|status|logout
adwall creatives search [ФИЛЬТРЫ] | get ID
adwall dictionaries categories|countries|languages
adwall favorites list|add|remove|toggle
adwall blacklist rules|direct|affected|add-rule|remove-rule|clear-ad
adwall apps search
adwall archives list|create|retry
adwall raw ENDPOINT QUERY_FILE [--variables JSON]
```

Основной API: `https://adwall.io/api/graphql`. Страница приложений использует
`stats-api/graphql`, а архиватор лендингов — `proxies-api/graphql`.

## Поиск

```powershell
adwall creatives search `
  --query casino `
  --country CZ --country GB `
  --format Video `
  --placement Facebook `
  --delivery-from 2026-07-01 `
  --delivery-to 2026-08-01 `
  --cloaked yes `
  --limit 10
```

Фильтры покрывают текст объявления, имя Facebook Page, OCR по изображению,
текст ссылки, полный URL, geo, число стран, язык, формат, даты показа и
создания, host/IP/TLD, приложение, placements, Meta Page ID, lead form, CTA,
категории и cloaking. Повторяйте list-флаги или передавайте значения через
запятую.

Для больших выдач используйте ограниченную пагинацию:

```powershell
adwall --jsonl creatives search --query Plinko --all-pages --max-pages 3 --limit 10
```

Каждый новый креатив может учитываться в `nUniqueAdsRetrieved`, поэтому CLI не
делает неограниченную пагинацию.

## Мутации и безопасность

Все изменения избранного, blacklist и архиватора требуют `--yes`:

```powershell
adwall favorites add AD_ID --yes
adwall blacklist add-rule AD_ID Hostname --yes
adwall archives create https://example.com --country CZ --yes
```

`raw` принимает GraphQL-документ из файла. Для документа с `mutation` он также
требует `--yes`.

## Skill

`skills/adwall-api/` самодостаточен: внутри `cli/` лежит копия CLI.

```powershell
python .\skills\adwall-api\scripts\adwall.py auth status
python .\skills\adwall-api\scripts\adwall.py creatives search --query Plinko --limit 10
```

## Проверка

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
python scripts/sync_skill_cli.py --check
python D:\YandexDisk\Settings\!skills\skills\skill-creator\scripts\quick_validate.py skills\adwall-api
```
