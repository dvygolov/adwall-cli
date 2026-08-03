# AdWall CLI — полное руководство

## Конфигурация

```dotenv
ADWALL_API_URL=https://adwall.io/api/graphql
ADWALL_STATS_API_URL=https://adwall.io/stats-api/graphql
ADWALL_PROXIES_API_URL=https://adwall.io/proxies-api/graphql
ADWALL_ADMIN_API_URL=https://adwall.io/admin-api/graphql
ADWALL_EMAIL=you@example.com
ADWALL_PASSWORD=your-password
ADWALL_SESSION_FILE=.adwall-session.json
ADWALL_TIMEOUT=60
```

CLI загружает access/refresh token из своего файла сессии. Если API возвращает
GraphQL-код `UNAUTHENTICATED`, CLI вызывает `RenewTokens` с refresh token,
сохраняет новую пару и один раз повторяет исходную операцию. Browser cookies и
browser storage не используются.

## Фильтры креативов

| CLI | `AdsFilterInput` | Значение |
|---|---|---|
| `--query`, `--text-body` | `textSearch.creativeBody` | Текст объявления |
| `--page-name` | `textSearch.metaPageName` | Имя Facebook Page |
| `--image-text` | `textSearch.textOnImages` | OCR-текст изображения |
| `--link-text` | `textSearch.creativeLinkText` | Текст ссылки |
| `--url` | `textSearch.targetLinkUrl` | Полный URL или фрагмент |
| `--country` | `shownInCountries` | Повторяемый ISO-код |
| `--countries-count` | `shownInTotalCountries` | Число стран |
| `--language` | `languages` | Повторяемый код языка |
| `--format` | `mediaDisplayFormats` | `Carousel`, `Image`, `None`, `Video` |
| `--placement` | `publisherPlatforms` | Meta placement |
| `--created-from/to` | `creationPeriod` | Обе даты `YYYY-MM-DD` |
| `--delivery-from/to` | `deliveryPeriod` | Обе даты `YYYY-MM-DD` |
| `--hostname` | `targetLink.hostname` | Host |
| `--ip-address` | `targetLink.ipAddress` | IP |
| `--tld` | `targetLink.topLevelDomainsList` | Доменная зона |
| `--app-id` | `targetApp.id` | ID приложения |
| `--app-platform` | `targetApp.platform` | `Android`, `IOs` |
| `--app-hosting` | `targetApp.hosting` | `AppStore`, `GooglePlay` |
| `--meta-page-id` | `metaPage.id` | Facebook Page ID |
| `--lead-form` | `includesLeadTypeForm` | `yes`, `no` |
| `--cta` | `callToActionTypes` | GraphQL `CallToActionKey` |
| `--category-id` | `attachedCategoryIds` | ID категории AdWall |
| `--cloaked` | `targetLink.contentInspection.isProbablyCloaked` | `yes`, `no` |
| `--additional-assets` | `hasAdditionalAssets` | `yes`, `no` |
| `--special-category` | `specialCategories` | Meta special category |

Placements: `AudienceNetwork`, `Facebook`, `Instagram`, `Messenger`, `Oculus`,
`Threads`, `WhatsApp`.

Special categories: `CreditAds`, `EmploymentAds`, `HousingAds`,
`PoliticalAndIssueAds`.

`creatives search` отправляет `dataset: Unique`, как first-party интерфейс.
По умолчанию возвращается до 10 объектов. `--all-pages` ограничен
`--max-pages 5`, пока пользователь явно не задаст другое значение.

## Ответ креатива

`creatives get ID` и search edges содержат `id`, признаки favorites/blacklist,
языки, placements, geo, CTA, media, тексты, даты, EU reach, Meta Page,
приложение, целевую ссылку, host/IP/TLD, cloaking и категории.

## Справочники

```text
dictionaries categories
dictionaries countries [--all-pages --max-pages N]
dictionaries languages [--all-pages --max-pages N]
```

Получите category ID через `dictionaries categories`, прежде чем использовать
`--category-id`.

## Избранное и blacklist

```text
favorites list [поисковые фильтры]
favorites add|remove|toggle AD_ID --yes

blacklist rules [--attribute ATTRIBUTE] [--value TEXT]
blacklist direct [cursor options]
blacklist affected ATTRIBUTE VALUE [--include-direct]
blacklist add-rule AD_ID ATTRIBUTE --yes
blacklist remove-rule ATTRIBUTE VALUE --yes
blacklist clear-ad AD_ID --yes
```

Blacklist attributes: `AppId`, `FbPageId`, `Hostname`, `IpAddress`.
Перед удалением правила сначала вызовите `blacklist rules` и проверьте точное
значение.

## Приложения

```text
apps search [--name TEXT] [--platform Android|IOs]
            [--status alive|banned] [--from DATE --to DATE]
            [--page N] [--page-size N] [--sort FIELD --direction asc|desc]
```

Команда использует `stats-api/graphql`, как страница `/apps`.

## Архивы

```text
archives list [--page N] [--page-size N]
archives create URL [--country ISO] --yes
archives retry ARCHIVE_ID --yes
```

Создание архива запускает внешний proxy/archive job и может потреблять ресурсы
тарифа. Не скачивайте и не открывайте архивы без проверки источника.

## Raw GraphQL

```text
raw api|stats|proxies|admin QUERY.graphql
    [--variables '{"key":"value"}' | --variables-file vars.json]
    [--operation-name NAME] [--yes]
```

Используйте только наблюдённые first-party операции. Не запускайте schema
mutation, admin operation или массовый запрос без отдельного разрешения.
