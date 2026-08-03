# Search filters

Use:

```text
python scripts/adwall.py creatives search [options]
```

| CLI | GraphQL input | Values |
|---|---|---|
| `--query`, `--text-body` | `textSearch.creativeBody` | ad body text |
| `--page-name` | `textSearch.metaPageName` | Facebook Page name |
| `--image-text` | `textSearch.textOnImages` | OCR text |
| `--link-text` | `textSearch.creativeLinkText` | creative link text |
| `--url` | `textSearch.targetLinkUrl` | full URL or substring |
| `--country` | `shownInCountries` | repeat ISO code |
| `--countries-count` | `shownInTotalCountries` | integer |
| `--language` | `languages` | repeat ISO language |
| `--format` | `mediaDisplayFormats` | Carousel, Image, None, Video |
| `--placement` | `publisherPlatforms` | Meta placement |
| `--created-from/to` | `creationPeriod` | both YYYY-MM-DD |
| `--delivery-from/to` | `deliveryPeriod` | both YYYY-MM-DD |
| `--hostname` | `targetLink.hostname` | hostname |
| `--ip-address` | `targetLink.ipAddress` | IP address |
| `--tld` | `targetLink.topLevelDomainsList` | domain zone |
| `--app-id` | `targetApp.id` | application ID |
| `--app-platform` | `targetApp.platform` | Android, IOs |
| `--app-hosting` | `targetApp.hosting` | AppStore, GooglePlay |
| `--meta-page-id` | `metaPage.id` | Facebook Page ID |
| `--lead-form` | `includesLeadTypeForm` | yes, no |
| `--cta` | `callToActionTypes` | CallToActionKey |
| `--category-id` | `attachedCategoryIds` | AdWall category ID |
| `--cloaked` | `contentInspection.isProbablyCloaked` | yes, no |
| `--additional-assets` | `hasAdditionalAssets` | yes, no |
| `--special-category` | `specialCategories` | Meta special category |

Placements: `AudienceNetwork Facebook Instagram Messenger Oculus Threads
WhatsApp`.

Get category IDs with `dictionaries categories`. The response is cursor-based:
use `--after`, or bounded `--all-pages --max-pages N`. The default dataset is
`Unique`, matching the first-party UI.
