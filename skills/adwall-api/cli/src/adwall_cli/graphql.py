AD_FRAGMENT = """
fragment AdFragment on Ad {
  blacklistedByAttributes
  id
  isDirectlyBlacklisted
  isInMyFavorites
  languages
  publisherPlatforms
  shownInCountries
  specialCategories
  callToAction { text type }
  creativeMedia {
    carouselCards {
      ... on CreativeCarouselImageCard {
        image { absoluteFilePath filename relativeFilePath dimensions { heightPx widthPx } }
      }
      ... on CreativeCarouselVideoCard {
        video { absoluteFilePath filename relativeFilePath videoDurationInSeconds }
        videoThumb { absoluteFilePath filename relativeFilePath dimensions { heightPx widthPx } }
      }
    }
    displayFormat
    image { absoluteFilePath filename relativeFilePath dimensions { heightPx widthPx } }
    video { absoluteFilePath filename relativeFilePath videoDurationInSeconds }
    videoThumb { absoluteFilePath filename relativeFilePath dimensions { heightPx widthPx } }
  }
  creativeText { bodies link { captions descriptions titles } }
  dateTimes { lastRefreshTime deliveryStopTime deliveryStartTime creationTime }
  euRelated {
    audienceReach { breakdown { ageRange female male } country }
    beneficiaryPayers { beneficiary current payer }
    euTotalReach
    targetAges { lowerBound upperBound }
    targetGender
    targetLocations { excluded name numObfuscated type }
  }
  metaPage { id name profilePicture { absoluteFilePath filename relativeFilePath } url }
  targetApp { id platform url }
  targetLink {
    contentInspection { isProbablyCloaked }
    hostname
    ipAddress
    topLevelDomain
    isAvailableForScraping
    url
  }
  attached { keywords categories { id isRoot title } }
}
"""

SIGN_IN = """
mutation SignIn($email: String!, $password: String!) {
  signIn(email: $email, password: $password) {
    accessToken
    refreshToken
    user {
      id email roles
      referralProgram { totalReferrals myReferrerIdToShare }
      platformUsageMetrics { nUniqueAdsRetrieved }
      activeSubscription {
        daysLeft hoursLeft startedAt finishesAt
        plan { featureList { nAdsLimit } internalName amount currencyCode recurringPeriodDays }
      }
    }
  }
}
"""

RENEW_TOKENS = """
mutation RenewTokens { renewTokens { accessToken refreshToken } }
"""

CURRENT_USER = """
query GetCurrentUser {
  getCurrentUser {
    id email roles
    referralProgram { totalReferrals myReferrerIdToShare }
    platformUsageMetrics { nUniqueAdsRetrieved }
    activeSubscription {
      daysLeft hoursLeft startedAt finishesAt
      plan { featureList { nAdsLimit } internalName amount currencyCode recurringPeriodDays }
    }
  }
}
"""

GET_ADS = AD_FRAGMENT + """
query GetAds($after: Cursor, $filter: AdsFilterInput, $first: Int!, $dataset: AdsDataset) {
  getAds(after: $after, filter: $filter, first: $first, dataset: $dataset) {
    pageInfo { hasNextPage endCursor currentPageSize totalDocumentsMatched }
    edges { cursor node { ...AdFragment } }
  }
}
"""

GET_AD = AD_FRAGMENT + """
query GetAd($id: String!) { getAd(id: $id) { ...AdFragment } }
"""

GET_FAVORITES = AD_FRAGMENT + """
query GetFavorites($first: Int!, $after: Cursor, $filter: AdsFilterInput) {
  getFavorites(first: $first, after: $after, filter: $filter) {
    pageInfo { currentPageSize endCursor hasNextPage totalDocumentsMatched }
    edges { cursor node { ...AdFragment } }
  }
}
"""

ADD_FAVORITE = """
mutation AddAdToFavorites($adId: ObjectId!) { addAdToFavorites(adId: $adId) }
"""

REMOVE_FAVORITE = """
mutation RemoveAdFromFavorites($adId: ObjectId!) { removeAdFromFavorites(adId: $adId) }
"""

TOGGLE_FAVORITE = """
mutation ToggleAdInFavorites($adId: ObjectId!) {
  toggleAdInFavorites(adId: $adId) { isAdded isRemoved }
}
"""

GET_CATEGORIES = """
query GetAdsCategories { getAdsCategories { id isRoot title parentCategoryId } }
"""

GET_COUNTRIES = """
query GetCountriesDictionaries($after: Cursor, $first: Int!) {
  getDictionaries {
    countries(after: $after, first: $first) {
      edges { cursor node { isoCode name } }
      pageInfo { currentPageSize endCursor hasNextPage totalDocumentsMatched }
    }
  }
}
"""

GET_LANGUAGES = """
query GetCountriesLanguages($after: Cursor, $first: Int!) {
  getDictionaries {
    languages(first: $first, after: $after) {
      edges { cursor node { name isoCode } }
      pageInfo { currentPageSize endCursor hasNextPage totalDocumentsMatched }
    }
  }
}
"""

GET_BLACKLIST_RULES = """
query GetBlacklistRules($pagination: PageBasedPaginationInput, $filter: BlacklistRulesFilterInput) {
  getBlacklistRules(pagination: $pagination, filter: $filter) {
    pageInfo {
      currentPageNumber currentPageSize hasNextPage hasPrevPage
      totalDocumentOnThisPage totalDocumentsMatched totalPages
    }
    data { blacklistAttribute attributeValue }
  }
}
"""

GET_DIRECT_BLACKLIST = AD_FRAGMENT + """
query GetDirectlyBlacklistedAds($after: Cursor, $first: Int!) {
  getDirectlyBlacklistedAds(after: $after, first: $first) {
    pageInfo { hasNextPage endCursor currentPageSize totalDocumentsMatched }
    edges { cursor node { ...AdFragment } }
  }
}
"""

GET_AFFECTED_BLACKLIST = AD_FRAGMENT + """
query GetBlacklistedAds($filter: BlacklistedAdsFilterInput!, $first: Int!, $after: Cursor) {
  getBlacklistedAds(filter: $filter, first: $first, after: $after) {
    pageInfo { currentPageSize endCursor hasNextPage totalDocumentsMatched }
    edges { cursor node { ...AdFragment } }
  }
}
"""

CREATE_BLACKLIST_RULE = """
mutation CreateBlacklistRuleBasedOnAttribute(
  $adId: ObjectId!, $blacklistAttribute: BlacklistAttribute!
) {
  createBlacklistRuleBasedOnAttribute(adId: $adId, blacklistAttribute: $blacklistAttribute)
}
"""

REMOVE_BLACKLIST_RULE = """
mutation RemoveBlacklistRule(
  $blacklistAttribute: BlacklistAttribute!, $attributeValue: String!
) {
  removeBlacklistRule(blacklistAttribute: $blacklistAttribute, attributeValue: $attributeValue)
}
"""

REMOVE_ALL_AD_RULES = """
mutation RemoveAllBlacklistRulesThatAffectAd($adId: ObjectId!) {
  removeAllBlacklistRulesThatAffectAd(adId: $adId)
}
"""

FIND_APPS = """
query FindAppCoverageReports(
  $filter: AppCoverageReportsFilterInput,
  $pagination: PageBasedPaginationInput,
  $sorting: AppCoverageReportsSortingInput
) {
  findAppCoverageReports(filter: $filter, pagination: $pagination, sorting: $sorting) {
    data {
      metrics { firstAdAppearedAt lastAdAppearedAt totalAdsPerPeriod totalRelatedMetaPages }
      app {
        icon { absoluteFilePath }
        id name platform
        availability { is404 is404Since lastCheckedAt }
      }
    }
    pageInfo {
      currentPageNumber currentPageSize hasNextPage hasPrevPage
      totalDocumentOnThisPage totalDocumentsMatched totalPages
    }
  }
}
"""

FIND_ARCHIVES = """
query FindMyWebpageArchivals(
  $filter: WebpageArchivalsFilterInput,
  $pagination: PageBasedPaginationInput,
  $sorting: WebpageArchivalsSortingInput
) {
  findWebpageArchivals: findMyWebpageArchivals(
    filter: $filter, pagination: $pagination, sorting: $sorting
  ) {
    data {
      timeTakenMs status id downloadParams { url countryCode } createdAt
      archive {
        id sizeBytes url
        screenshots {
          lg { heightPx url widthPx }
          sm { heightPx url widthPx }
        }
      }
    }
    pageInfo {
      currentPageNumber currentPageSize hasNextPage hasPrevPage
      totalDocumentOnThisPage totalDocumentsMatched totalPages
    }
  }
}
"""

INITIALIZE_ARCHIVE = """
mutation InitializeWebpageArchival($countryCode: String, $url: String!) {
  initializeWebpageArchival(countryCode: $countryCode, url: $url) { id }
}
"""

RETRY_ARCHIVE = """
mutation RetryFailedWebpageArchival($webpageArchivalId: ObjectId!) {
  retryFailedWebpageArchival(webpageArchivalId: $webpageArchivalId) {
    id status problemsList { caughtError }
  }
}
"""
