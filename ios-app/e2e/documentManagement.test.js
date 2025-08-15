describe('Document Management', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should upload a document successfully', async () => {
    // Navigate to Documents tab
    await element(by.id('documents-tab')).tap();
    
    // Tap upload button
    await element(by.id('upload-button')).tap();
    
    // Verify document picker opens
    await expect(element(by.id('document-picker'))).toBeVisible();
    
    // Select a test document (mocked)
    await element(by.id('select-test-document')).tap();
    
    // Verify upload progress
    await waitFor(element(by.id('upload-progress')))
      .toBeVisible()
      .withTimeout(5000);
    
    // Wait for upload completion
    await waitFor(element(by.id('upload-success')))
      .toBeVisible()
      .withTimeout(30000);
  });

  it('should display document list', async () => {
    // Navigate to Documents tab
    await element(by.id('documents-tab')).tap();
    
    // Verify document list is visible
    await expect(element(by.id('document-list'))).toBeVisible();
    
    // Check for at least one document
    await expect(element(by.id('document-item-0'))).toBeVisible();
  });

  it('should show document processing status', async () => {
    // Navigate to Documents tab
    await element(by.id('documents-tab')).tap();
    
    // Tap on a processing document
    await element(by.id('document-item-processing')).tap();
    
    // Verify processing status is shown
    await expect(element(by.id('processing-status'))).toBeVisible();
    await expect(element(by.text('Processing...'))).toBeVisible();
  });

  it('should navigate to document details', async () => {
    // Navigate to Documents tab
    await element(by.id('documents-tab')).tap();
    
    // Tap on a completed document
    await element(by.id('document-item-completed')).tap();
    
    // Verify document details screen
    await expect(element(by.id('document-details'))).toBeVisible();
    await expect(element(by.id('chapter-list'))).toBeVisible();
  });

  it('should handle upload errors gracefully', async () => {
    // Navigate to Documents tab
    await element(by.id('documents-tab')).tap();
    
    // Tap upload button
    await element(by.id('upload-button')).tap();
    
    // Select an invalid file (mocked)
    await element(by.id('select-invalid-document')).tap();
    
    // Verify error message
    await waitFor(element(by.id('upload-error')))
      .toBeVisible()
      .withTimeout(5000);
    
    await expect(element(by.text('Upload failed'))).toBeVisible();
  });

  it('should support file type validation', async () => {
    // Navigate to Documents tab
    await element(by.id('documents-tab')).tap();
    
    // Tap upload button
    await element(by.id('upload-button')).tap();
    
    // Try to select unsupported file type
    await element(by.id('select-unsupported-file')).tap();
    
    // Verify validation error
    await expect(element(by.text('Unsupported file type'))).toBeVisible();
  });
});