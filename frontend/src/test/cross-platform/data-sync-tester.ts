/**
 * Data synchronization testing between platforms
 */

import { Browser, BrowserContext, Page } from 'playwright';
import { SyncTestResult, TestContext } from './types';
import { TEST_TIMEOUTS } from './cross-platform.config';

interface SyncTestData {
  documentId?: string;
  cardId?: string;
  progressData?: any;
  settingsData?: any;
  timestamp: number;
}

export class DataSyncTester {
  private contexts: Map<string, { browser: Browser; context: BrowserContext; page: Page }> = new Map();
  private testResults: SyncTestResult[] = [];

  async initializePlatforms(platforms: { name: string; browser: Browser }[]): Promise<void> {
    console.log('Initializing platforms for sync testing...');
    
    for (const platform of platforms) {
      const context = await platform.browser.newContext();
      const page = await context.newPage();
      
      this.contexts.set(platform.name, {
        browser: platform.browser,
        context,
        page
      });
    }
  }

  async runSyncTests(baseUrl: string = 'http://localhost:3000'): Promise<SyncTestResult[]> {
    console.log('Running data synchronization tests...');
    this.testResults = [];

    const syncTestCases = this.getSyncTestCases();

    for (const testCase of syncTestCases) {
      try {
        const result = await this.executeSyncTest(testCase, baseUrl);
        this.testResults.push(result);
      } catch (error) {
        this.testResults.push({
          testName: testCase.name,
          platforms: Array.from(this.contexts.keys()),
          dataConsistency: false,
          syncLatency: 0,
          conflicts: 0,
          error: error instanceof Error ? error.message : String(error)
        });
      }
    }

    return this.testResults;
  }

  private async executeSyncTest(testCase: any, baseUrl: string): Promise<SyncTestResult> {
    const platforms = Array.from(this.contexts.keys());
    const testContexts: TestContext[] = [];

    // Create test contexts for each platform
    for (const [platformName, platformData] of this.contexts) {
      testContexts.push({
        browser: platformData.browser,
        page: platformData.page,
        platform: platformName,
        baseUrl
      });
    }

    return await testCase.execute(testContexts);
  }

  private getSyncTestCases() {
    return [
      {
        name: 'Document Upload Sync Test',
        description: 'Test document synchronization across platforms',
        execute: async (contexts: TestContext[]): Promise<SyncTestResult> => {
          const startTime = Date.now();
          
          // Upload document on first platform
          const uploadContext = contexts[0];
          await uploadContext.page.goto(`${uploadContext.baseUrl}/documents`);
          
          // Simulate document upload
          const uploadButton = uploadContext.page.locator('[data-testid="upload-button"]');
          await uploadButton.waitFor({ timeout: TEST_TIMEOUTS.elementWait });
          
          // Mock document upload by creating test data
          const testDocumentId = `test-doc-${Date.now()}`;
          await uploadContext.page.evaluate((docId) => {
            // Simulate adding document to local storage or state
            localStorage.setItem('test-document', JSON.stringify({
              id: docId,
              name: 'Test Document',
              uploadTime: Date.now()
            }));
          }, testDocumentId);

          // Wait for sync propagation
          await this.waitForSync();

          // Check if document appears on other platforms
          const syncResults = [];
          for (let i = 1; i < contexts.length; i++) {
            const checkContext = contexts[i];
            await checkContext.page.goto(`${checkContext.baseUrl}/documents`);
            
            // Check if document is synchronized
            const documentExists = await checkContext.page.evaluate((docId) => {
              const doc = localStorage.getItem('test-document');
              if (doc) {
                const parsedDoc = JSON.parse(doc);
                return parsedDoc.id === docId;
              }
              return false;
            }, testDocumentId);
            
            syncResults.push(documentExists);
          }

          const syncLatency = Date.now() - startTime;
          const dataConsistency = syncResults.every(result => result === true);

          return {
            testName: 'Document Upload Sync Test',
            platforms: contexts.map(c => c.platform),
            dataConsistency,
            syncLatency,
            conflicts: 0
          };
        }
      },
      {
        name: 'Card Progress Sync Test',
        description: 'Test card review progress synchronization',
        execute: async (contexts: TestContext[]): Promise<SyncTestResult> => {
          const startTime = Date.now();
          
          // Set up test data on first platform
          const progressContext = contexts[0];
          await progressContext.page.goto(`${progressContext.baseUrl}/study`);
          
          const testCardId = `test-card-${Date.now()}`;
          const testProgress = {
            cardId: testCardId,
            grade: 4,
            reviewCount: 1,
            lastReviewed: Date.now(),
            nextReview: Date.now() + 86400000 // 24 hours
          };

          // Simulate card review
          await progressContext.page.evaluate((progress) => {
            localStorage.setItem('card-progress', JSON.stringify(progress));
          }, testProgress);

          // Wait for sync
          await this.waitForSync();

          // Check progress sync on other platforms
          const syncResults = [];
          for (let i = 1; i < contexts.length; i++) {
            const checkContext = contexts[i];
            await checkContext.page.goto(`${checkContext.baseUrl}/study`);
            
            const progressSynced = await checkContext.page.evaluate((cardId) => {
              const progress = localStorage.getItem('card-progress');
              if (progress) {
                const parsedProgress = JSON.parse(progress);
                return parsedProgress.cardId === cardId && parsedProgress.grade === 4;
              }
              return false;
            }, testCardId);
            
            syncResults.push(progressSynced);
          }

          const syncLatency = Date.now() - startTime;
          const dataConsistency = syncResults.every(result => result === true);

          return {
            testName: 'Card Progress Sync Test',
            platforms: contexts.map(c => c.platform),
            dataConsistency,
            syncLatency,
            conflicts: 0
          };
        }
      },
      {
        name: 'Settings Sync Test',
        description: 'Test user settings synchronization',
        execute: async (contexts: TestContext[]): Promise<SyncTestResult> => {
          const startTime = Date.now();
          
          // Update settings on first platform
          const settingsContext = contexts[0];
          await settingsContext.page.goto(`${settingsContext.baseUrl}/settings`);
          
          const testSettings = {
            theme: 'dark',
            language: 'en',
            cardsPerSession: 20,
            privacyMode: true,
            lastUpdated: Date.now()
          };

          // Simulate settings update
          await settingsContext.page.evaluate((settings) => {
            localStorage.setItem('user-settings', JSON.stringify(settings));
          }, testSettings);

          // Wait for sync
          await this.waitForSync();

          // Check settings sync on other platforms
          const syncResults = [];
          for (let i = 1; i < contexts.length; i++) {
            const checkContext = contexts[i];
            await checkContext.page.goto(`${checkContext.baseUrl}/settings`);
            
            const settingsSynced = await checkContext.page.evaluate(() => {
              const settings = localStorage.getItem('user-settings');
              if (settings) {
                const parsedSettings = JSON.parse(settings);
                return parsedSettings.theme === 'dark' && 
                       parsedSettings.cardsPerSession === 20 &&
                       parsedSettings.privacyMode === true;
              }
              return false;
            });
            
            syncResults.push(settingsSynced);
          }

          const syncLatency = Date.now() - startTime;
          const dataConsistency = syncResults.every(result => result === true);

          return {
            testName: 'Settings Sync Test',
            platforms: contexts.map(c => c.platform),
            dataConsistency,
            syncLatency,
            conflicts: 0
          };
        }
      },
      {
        name: 'Offline Changes Sync Test',
        description: 'Test synchronization of changes made while offline',
        execute: async (contexts: TestContext[]): Promise<SyncTestResult> => {
          const startTime = Date.now();
          
          // Simulate offline mode on first platform
          const offlineContext = contexts[0];
          await offlineContext.page.goto(`${offlineContext.baseUrl}/study`);
          
          // Go offline
          await offlineContext.page.context().setOffline(true);
          
          const offlineChanges = {
            cardId: `offline-card-${Date.now()}`,
            grade: 3,
            reviewedOffline: true,
            offlineTimestamp: Date.now()
          };

          // Make changes while offline
          await offlineContext.page.evaluate((changes) => {
            const existingChanges = localStorage.getItem('offline-changes') || '[]';
            const parsedChanges = JSON.parse(existingChanges);
            parsedChanges.push(changes);
            localStorage.setItem('offline-changes', JSON.stringify(parsedChanges));
          }, offlineChanges);

          // Go back online
          await offlineContext.page.context().setOffline(false);
          
          // Wait for sync
          await this.waitForSync();

          // Check if offline changes are synced to other platforms
          const syncResults = [];
          for (let i = 1; i < contexts.length; i++) {
            const checkContext = contexts[i];
            await checkContext.page.goto(`${checkContext.baseUrl}/study`);
            
            const offlineChangesSynced = await checkContext.page.evaluate((cardId) => {
              const changes = localStorage.getItem('offline-changes');
              if (changes) {
                const parsedChanges = JSON.parse(changes);
                return parsedChanges.some((change: any) => 
                  change.cardId === cardId && change.reviewedOffline === true
                );
              }
              return false;
            }, offlineChanges.cardId);
            
            syncResults.push(offlineChangesSynced);
          }

          const syncLatency = Date.now() - startTime;
          const dataConsistency = syncResults.every(result => result === true);

          return {
            testName: 'Offline Changes Sync Test',
            platforms: contexts.map(c => c.platform),
            dataConsistency,
            syncLatency,
            conflicts: 0
          };
        }
      },
      {
        name: 'Conflict Resolution Test',
        description: 'Test handling of sync conflicts between platforms',
        execute: async (contexts: TestContext[]): Promise<SyncTestResult> => {
          const startTime = Date.now();
          
          if (contexts.length < 2) {
            throw new Error('Need at least 2 platforms for conflict testing');
          }

          const cardId = `conflict-card-${Date.now()}`;
          
          // Create conflicting changes on different platforms
          const platform1 = contexts[0];
          const platform2 = contexts[1];

          await platform1.page.goto(`${platform1.baseUrl}/study`);
          await platform2.page.goto(`${platform2.baseUrl}/study`);

          // Make conflicting changes simultaneously
          const change1 = {
            cardId,
            grade: 4,
            timestamp: Date.now(),
            platform: platform1.platform
          };

          const change2 = {
            cardId,
            grade: 2,
            timestamp: Date.now() + 1, // Slightly later
            platform: platform2.platform
          };

          await Promise.all([
            platform1.page.evaluate((change) => {
              localStorage.setItem('card-conflict-test', JSON.stringify(change));
            }, change1),
            platform2.page.evaluate((change) => {
              localStorage.setItem('card-conflict-test', JSON.stringify(change));
            }, change2)
          ]);

          // Wait for conflict resolution
          await this.waitForSync(5000); // Longer wait for conflict resolution

          // Check conflict resolution
          const resolvedStates = [];
          for (const context of contexts) {
            const resolvedState = await context.page.evaluate(() => {
              return localStorage.getItem('card-conflict-test');
            });
            resolvedStates.push(resolvedState);
          }

          // Check if all platforms have the same resolved state
          const firstState = resolvedStates[0];
          const dataConsistency = resolvedStates.every(state => state === firstState);
          
          // Count conflicts (in this case, we expect 1 conflict that was resolved)
          const conflicts = dataConsistency ? 1 : resolvedStates.length;

          const syncLatency = Date.now() - startTime;

          return {
            testName: 'Conflict Resolution Test',
            platforms: contexts.map(c => c.platform),
            dataConsistency,
            syncLatency,
            conflicts
          };
        }
      }
    ];
  }

  private async waitForSync(timeout: number = 3000): Promise<void> {
    // Simulate sync delay
    await new Promise(resolve => setTimeout(resolve, timeout));
  }

  async cleanup(): Promise<void> {
    console.log('Cleaning up data sync tester...');
    
    for (const [platformName, platformData] of this.contexts) {
      try {
        await platformData.context.close();
        console.log(`Closed context for ${platformName}`);
      } catch (error) {
        console.error(`Error closing context for ${platformName}:`, error);
      }
    }
    
    this.contexts.clear();
  }

  getResults(): SyncTestResult[] {
    return this.testResults;
  }

  generateReport(): string {
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(r => r.dataConsistency).length;
    const failedTests = this.testResults.filter(r => !r.dataConsistency).length;
    
    let report = `\n=== Data Synchronization Test Report ===\n`;
    report += `Total Tests: ${totalTests}\n`;
    report += `Passed: ${passedTests}\n`;
    report += `Failed: ${failedTests}\n`;
    report += `Success Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n\n`;
    
    // Average sync latency
    const avgLatency = this.testResults.reduce((sum, r) => sum + r.syncLatency, 0) / totalTests;
    report += `Average Sync Latency: ${avgLatency.toFixed(0)}ms\n`;
    
    // Total conflicts detected
    const totalConflicts = this.testResults.reduce((sum, r) => sum + r.conflicts, 0);
    report += `Total Conflicts Detected: ${totalConflicts}\n\n`;
    
    // Individual test results
    this.testResults.forEach(result => {
      const status = result.dataConsistency ? 'PASSED' : 'FAILED';
      report += `${result.testName}: ${status}\n`;
      report += `  Platforms: ${result.platforms.join(', ')}\n`;
      report += `  Sync Latency: ${result.syncLatency}ms\n`;
      report += `  Conflicts: ${result.conflicts}\n`;
      
      if (result.error) {
        report += `  Error: ${result.error}\n`;
      }
      report += '\n';
    });
    
    return report;
  }
}