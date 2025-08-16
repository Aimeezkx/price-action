import { UsabilityTestFramework } from '../usability-test-framework';

describe('Usability Tests', () => {
  const baseUrl = process.env.TEST_BASE_URL || 'http://localhost:3000';
  let usabilityFramework: UsabilityTestFramework;

  beforeAll(async () => {
    usabilityFramework = new UsabilityTestFramework();
    await usabilityFramework.setup();
  });

  afterAll(async () => {
    await usabilityFramework.teardown();
  });

  describe('User Workflow Tests', () => {
    test('Home page should load quickly and be navigable', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: baseUrl,
        scenarios: [
          {
            name: 'Homepage Load',
            description: 'Load homepage and verify main elements',
            userGoal: 'Access the application homepage',
            steps: [
              {
                action: 'wait',
                target: 'main',
                description: 'Wait for main content to load'
              },
              {
                action: 'verify',
                target: 'nav',
                description: 'Verify navigation is present'
              }
            ],
            successCriteria: {
              requiredElements: ['main', 'nav'],
              performanceThresholds: {
                maxLoadTime: 3000
              }
            },
            difficulty: 'easy'
          }
        ]
      });

      expect(results.length).toBe(1);
      expect(results[0].success).toBe(true);
      expect(results[0].userExperienceScore).toBeGreaterThanOrEqual(80);
      expect(results[0].performanceMetrics.pageLoadTime).toBeLessThanOrEqual(3000);
    });

    test('Document upload workflow should be intuitive', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: `${baseUrl}/documents`,
        scenarios: [
          {
            name: 'Document Upload Flow',
            description: 'Navigate to upload and open modal',
            userGoal: 'Upload a new document',
            steps: [
              {
                action: 'wait',
                target: '[data-testid="upload-button"]',
                description: 'Wait for upload button to be available'
              },
              {
                action: 'click',
                target: '[data-testid="upload-button"]',
                description: 'Click upload button'
              },
              {
                action: 'wait',
                target: '[data-testid="upload-modal"]',
                description: 'Wait for upload modal to appear'
              }
            ],
            successCriteria: {
              requiredElements: [
                '[data-testid="upload-modal"]',
                '[data-testid="file-input"]'
              ],
              performanceThresholds: {
                maxInteractionTime: 1000
              }
            },
            difficulty: 'medium'
          }
        ]
      });

      expect(results.length).toBe(1);
      expect(results[0].completed).toBe(true);
      expect(results[0].userExperienceScore).toBeGreaterThanOrEqual(70);
      
      // Check that interaction time is reasonable
      const totalInteractionTime = results[0].stepResults.reduce(
        (sum, step) => sum + step.timeToComplete, 0
      );
      expect(totalInteractionTime).toBeLessThanOrEqual(2000);
    });

    test('Study session should be smooth and responsive', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: `${baseUrl}/study`,
        scenarios: [
          {
            name: 'Flashcard Interaction',
            description: 'Interact with flashcards in study session',
            userGoal: 'Review flashcards effectively',
            steps: [
              {
                action: 'wait',
                target: '[data-testid="flashcard"]',
                description: 'Wait for flashcard to load'
              },
              {
                action: 'click',
                target: '[data-testid="flashcard"]',
                description: 'Click to flip card'
              },
              {
                action: 'wait',
                target: '[data-testid="grading-interface"]',
                timeout: 2000,
                description: 'Wait for grading interface'
              },
              {
                action: 'click',
                target: '[data-testid="grade-4"]',
                description: 'Grade the card'
              }
            ],
            successCriteria: {
              customValidation: async (page) => {
                // Check if next card appeared or session completed
                const nextCard = await page.$('[data-testid="flashcard"]');
                const sessionComplete = await page.$('[data-testid="session-complete"]');
                return nextCard || sessionComplete;
              },
              performanceThresholds: {
                maxInteractionTime: 3000
              }
            },
            difficulty: 'medium'
          }
        ]
      });

      expect(results.length).toBe(1);
      expect(results[0].completed).toBe(true);
      
      // Each step should complete reasonably quickly
      for (const stepResult of results[0].stepResults) {
        expect(stepResult.timeToComplete).toBeLessThanOrEqual(2000);
      }
    });

    test('Search functionality should be responsive and helpful', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: `${baseUrl}/search`,
        scenarios: [
          {
            name: 'Search and Filter',
            description: 'Perform search with filters',
            userGoal: 'Find specific content using search',
            steps: [
              {
                action: 'wait',
                target: '[data-testid="search-input"]',
                description: 'Wait for search input'
              },
              {
                action: 'type',
                target: '[data-testid="search-input"]',
                value: 'machine learning',
                description: 'Enter search query'
              },
              {
                action: 'key',
                key: 'Enter',
                description: 'Submit search'
              },
              {
                action: 'wait',
                target: '[data-testid="search-results"]',
                timeout: 3000,
                description: 'Wait for search results'
              }
            ],
            successCriteria: {
              requiredElements: ['[data-testid="search-results"]'],
              expectedText: ['machine learning'],
              performanceThresholds: {
                maxInteractionTime: 4000
              }
            },
            difficulty: 'medium'
          }
        ]
      });

      expect(results.length).toBe(1);
      expect(results[0].completed).toBe(true);
      expect(results[0].userExperienceScore).toBeGreaterThanOrEqual(70);
    });
  });

  describe('Performance and Responsiveness', () => {
    test('All pages should load within acceptable time limits', async () => {
      const pages = [
        { path: '/', name: 'Home' },
        { path: '/documents', name: 'Documents' },
        { path: '/study', name: 'Study' },
        { path: '/search', name: 'Search' }
      ];

      for (const page of pages) {
        const results = await usabilityFramework.runUsabilityTest({
          url: `${baseUrl}${page.path}`,
          scenarios: [
            {
              name: `${page.name} Page Load Performance`,
              description: `Test ${page.name} page loading performance`,
              userGoal: `Access ${page.name} page quickly`,
              steps: [
                {
                  action: 'wait',
                  target: 'main',
                  timeout: 5000,
                  description: 'Wait for main content'
                }
              ],
              successCriteria: {
                requiredElements: ['main'],
                performanceThresholds: {
                  maxLoadTime: 3000
                }
              },
              difficulty: 'easy'
            }
          ]
        });

        expect(results[0].success).toBe(true);
        expect(results[0].performanceMetrics.pageLoadTime).toBeLessThanOrEqual(3000);
      }
    });

    test('Interactive elements should respond quickly', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: `${baseUrl}/documents`,
        scenarios: [
          {
            name: 'Button Response Time',
            description: 'Test button interaction responsiveness',
            userGoal: 'Interact with buttons smoothly',
            steps: [
              {
                action: 'click',
                target: '[data-testid="upload-button"]',
                description: 'Click upload button'
              },
              {
                action: 'wait',
                target: '[data-testid="upload-modal"]',
                timeout: 1000,
                description: 'Wait for modal to appear'
              }
            ],
            successCriteria: {
              requiredElements: ['[data-testid="upload-modal"]'],
              performanceThresholds: {
                maxInteractionTime: 500
              }
            },
            difficulty: 'easy'
          }
        ]
      });

      expect(results[0].success).toBe(true);
      
      // Button click should be very responsive
      const clickStep = results[0].stepResults.find(s => s.description.includes('Click'));
      if (clickStep) {
        expect(clickStep.timeToComplete).toBeLessThanOrEqual(500);
      }
    });
  });

  describe('Error Handling and Edge Cases', () => {
    test('Should handle missing elements gracefully', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: `${baseUrl}/`,
        scenarios: [
          {
            name: 'Missing Element Test',
            description: 'Test behavior with missing elements',
            userGoal: 'Handle missing elements gracefully',
            steps: [
              {
                action: 'click',
                target: '[data-testid="non-existent-element"]',
                description: 'Try to click non-existent element',
                optional: true
              },
              {
                action: 'wait',
                target: 'main',
                description: 'Verify page still works'
              }
            ],
            successCriteria: {
              requiredElements: ['main']
            },
            difficulty: 'easy'
          }
        ]
      });

      expect(results[0].completed).toBe(true);
      
      // Should have warnings but not fail completely
      const optionalStepFailed = results[0].stepResults.some(s => 
        !s.success && s.description.includes('non-existent')
      );
      expect(optionalStepFailed).toBe(true);
      
      // But overall scenario should still succeed
      expect(results[0].success).toBe(true);
    });

    test('Should handle slow loading gracefully', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: `${baseUrl}/study`,
        scenarios: [
          {
            name: 'Slow Loading Test',
            description: 'Test behavior with slow loading elements',
            userGoal: 'Handle slow loading gracefully',
            steps: [
              {
                action: 'wait',
                target: '[data-testid="flashcard"]',
                timeout: 10000,
                description: 'Wait for flashcard with extended timeout'
              }
            ],
            successCriteria: {
              requiredElements: ['[data-testid="flashcard"]'],
              performanceThresholds: {
                maxLoadTime: 10000
              }
            },
            difficulty: 'easy'
          }
        ]
      });

      expect(results[0].completed).toBe(true);
      
      // Should succeed even if it takes longer
      expect(results[0].success).toBe(true);
    });
  });

  describe('User Experience Metrics', () => {
    test('Overall user experience should meet quality standards', async () => {
      const results = await usabilityFramework.runUsabilityTest({
        url: baseUrl,
        scenarios: [
          {
            name: 'Complete User Journey',
            description: 'Test complete user journey through the app',
            userGoal: 'Navigate through main app features',
            steps: [
              {
                action: 'wait',
                target: 'main',
                description: 'Load homepage'
              },
              {
                action: 'click',
                target: '[data-testid="documents-link"]',
                description: 'Navigate to documents'
              },
              {
                action: 'wait',
                target: '[data-testid="documents-page"]',
                description: 'Wait for documents page'
              },
              {
                action: 'click',
                target: '[data-testid="study-link"]',
                description: 'Navigate to study'
              },
              {
                action: 'wait',
                target: '[data-testid="study-page"]',
                description: 'Wait for study page'
              }
            ],
            successCriteria: {
              customValidation: async (page) => {
                // Check if we successfully navigated through the app
                const currentUrl = page.url();
                return currentUrl.includes('/study');
              },
              performanceThresholds: {
                maxInteractionTime: 5000
              }
            },
            difficulty: 'medium'
          }
        ]
      });

      expect(results[0].completed).toBe(true);
      expect(results[0].success).toBe(true);
      expect(results[0].userExperienceScore).toBeGreaterThanOrEqual(75);
      
      // Total journey should be reasonably fast
      expect(results[0].timeToComplete).toBeLessThanOrEqual(10000);
    });
  });
});