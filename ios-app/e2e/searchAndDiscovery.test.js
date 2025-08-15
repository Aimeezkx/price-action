describe('Search and Discovery', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should perform text search', async () => {
    // Navigate to Search tab
    await element(by.id('search-tab')).tap();
    
    // Type in search query
    await element(by.id('search-input')).typeText('machine learning');
    
    // Tap search button
    await element(by.id('search-button')).tap();
    
    // Wait for results
    await waitFor(element(by.id('search-results')))
      .toBeVisible()
      .withTimeout(10000);
    
    // Verify results are displayed
    await expect(element(by.id('search-result-0'))).toBeVisible();
  });

  it('should perform semantic search', async () => {
    // Navigate to Search tab
    await element(by.id('search-tab')).tap();
    
    // Enable semantic search
    await element(by.id('semantic-search-toggle')).tap();
    
    // Type in search query
    await element(by.id('search-input')).typeText('artificial intelligence');
    
    // Tap search button
    await element(by.id('search-button')).tap();
    
    // Wait for results
    await waitFor(element(by.id('search-results')))
      .toBeVisible()
      .withTimeout(15000);
    
    // Verify semantic results
    await expect(element(by.id('search-result-0'))).toBeVisible();
  });

  it('should apply search filters', async () => {
    // Navigate to Search tab
    await element(by.id('search-tab')).tap();
    
    // Open filters
    await element(by.id('filter-button')).tap();
    
    // Select chapter filter
    await element(by.id('chapter-filter')).tap();
    await element(by.text('Chapter 1')).tap();
    
    // Select difficulty filter
    await element(by.id('difficulty-filter')).tap();
    await element(by.text('Medium')).tap();
    
    // Apply filters
    await element(by.id('apply-filters')).tap();
    
    // Perform search
    await element(by.id('search-input')).typeText('neural networks');
    await element(by.id('search-button')).tap();
    
    // Verify filtered results
    await waitFor(element(by.id('search-results')))
      .toBeVisible()
      .withTimeout(10000);
  });

  it('should show search history', async () => {
    // Navigate to Search tab
    await element(by.id('search-tab')).tap();
    
    // Perform a search first
    await element(by.id('search-input')).typeText('deep learning');
    await element(by.id('search-button')).tap();
    
    // Wait for results
    await waitFor(element(by.id('search-results')))
      .toBeVisible()
      .withTimeout(10000);
    
    // Clear search and check history
    await element(by.id('search-input')).clearText();
    await element(by.id('search-input')).tap();
    
    // Verify search history appears
    await expect(element(by.id('search-history'))).toBeVisible();
    await expect(element(by.text('deep learning'))).toBeVisible();
  });

  it('should handle empty search results', async () => {
    // Navigate to Search tab
    await element(by.id('search-tab')).tap();
    
    // Search for something that doesn't exist
    await element(by.id('search-input')).typeText('nonexistent topic xyz');
    await element(by.id('search-button')).tap();
    
    // Wait for empty state
    await waitFor(element(by.id('empty-search-results')))
      .toBeVisible()
      .withTimeout(10000);
    
    await expect(element(by.text('No results found'))).toBeVisible();
  });

  it('should support search suggestions', async () => {
    // Navigate to Search tab
    await element(by.id('search-tab')).tap();
    
    // Start typing
    await element(by.id('search-input')).typeText('mach');
    
    // Wait for suggestions
    await waitFor(element(by.id('search-suggestions')))
      .toBeVisible()
      .withTimeout(3000);
    
    // Tap on a suggestion
    await element(by.text('machine learning')).tap();
    
    // Verify suggestion was applied
    await expect(element(by.id('search-input'))).toHaveText('machine learning');
  });

  it('should navigate to card from search results', async () => {
    // Navigate to Search tab
    await element(by.id('search-tab')).tap();
    
    // Perform search
    await element(by.id('search-input')).typeText('algorithms');
    await element(by.id('search-button')).tap();
    
    // Wait for results
    await waitFor(element(by.id('search-results')))
      .toBeVisible()
      .withTimeout(10000);
    
    // Tap on a search result
    await element(by.id('search-result-0')).tap();
    
    // Verify navigation to card detail or study mode
    await expect(element(by.id('card-detail')).or(by.id('flashcard-container'))).toBeVisible();
  });
});