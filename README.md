---

### 1. Problem

The eBay crawler faces two key challenges related to item conditions and currency:

 - Condition Mismatch:
    -   When the --set-cond flag (accepting "New" or "Used") is not provided, the script scrapes all search results without filtering by condition. This results in non-standard conditions like "Good - Refurbished", "Pre-Owned", or "Parts Only" appearing in the output.
    -   Individual product pages consistently list conditions as "New" or "Used," creating a mismatch with search result data.
    -   Decision required: Should the crawler include non-standard conditions like "Good - Refurbished", "Pre-Owned", or "Parts Only"  or use the standardized filter conditions (New/Used)?
        
- Condition Extraction:
    -   To obtain standardized "New" or "Used" conditions, the crawler could scrape each product page, but this significantly slows execution and increases requests.
    -   Alternatively, it could rely on filter-based conditions applied during the search, even when `--set-cond` is unset.
        
- Currency Standardization:
    -   Prices must be consistently reported in USD, regardless of the listing’s original currency.


### 2. Options Considered

To address the mismatch and ensure standardized condition data, two approaches were evaluated:

- Option 1: Scrape Product Pages:
    
    -   Open each product page to retrieve the standardized condition ("New" or "Used").
    -   Significantly slows down the script due to additional HTTP requests for each product page.
    -   Increases the risk of rate-limiting or bans from eBay due to higher request volumes.    
    -   Adds complexity to error handling for failed product page requests.
            
- Option 2: Rely on Filter Conditions:
    
    -   Use eBay's condition filter ("New" or "Used") to standardize scraping, even when `--set-cond` is not set. If `--set-cond` is unspecified, the script iterates through all available conditions (using `_get_condition`) in a predefined order.
    -   Faster execution, as it avoids scraping individual product pages.
    -   Reduces the number of HTTP requests, lowering the risk of rate-limiting.
    -   Simplifies the codebase by leveraging existing filter logic.        
    -   Ensures standardized output by aligning with eBay's filter categories.
            

### 3. Chosen Approach

Option 2: Rely on Filter Conditions was selected for the following reasons:
-   Performance: Avoiding product page requests reduces runtime and server load, making the crawler more efficient and scalable.
-   Reliability: Fewer requests decrease the likelihood of triggering eBay's anti-scraping mechanisms, ensuring consistent operation.
-   Standardization: Using filter conditions ("New" or "Used") aligns with the expected output format and simplifies downstream data processing.
-   Maintainability: Leveraging the existing _get_condition method to fetch available conditions minimizes code changes and ensures robustness.
    

To handle the absence of `--set-cond`, the script will:

1.  Use `_get_condition` to retrieve all available condition filters from the search page.
2.  If `--set-cond` is not provided, iterate through all conditions in a standardized order (e.g., "New" then "Used").
3.  For each condition, apply the filter, scrape the results, and store the data with the corresponding condition label.
    

### 4. Implementation Details
-   Condition Handling:
    -   The _get_condition method parses the search page to extract available condition filters (e.g., "New," "Used").
    -   When `--set-cond` is set, the script applies the specified condition directly.
    -   When `--set-cond` is not set, the script iterates through all conditions retrieved by _get_condition, ensuring comprehensive coverage.
        
-   Currency Conversion:
    -   The `_to_usd` method converts prices from various currencies to USD, ensuring uniformity in the output data.
