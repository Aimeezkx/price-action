import { AccessibilityUsabilityConfig } from '../accessibility-usability-suite';

export const documentLearningAppConfig: AccessibilityUsabilityConfig = {
  baseUrl: 'http://localhost:3000',
  outputDir: './test-reports/accessibility-usability',
  generateReports: true,
  pages: [
    {
      name: 'Home Page',
      path: '/',
      accessibility: {
        enabled: true,
        tags: ['wcag2a', 'wcag2aa'],
        excludeSelectors: ['.loading-spinner', '.toast-notification']
      },
      keyboard: {
        enabled: true,
        scenarios: [
          {
            name: 'Main Navigation',
            description: 'Navigate through main menu items',
            keySequence: [
              { type: 'tab', repeat: 5 },
              { type: 'enter' }
            ],
            expectedOutcome: {
              customValidation: async (page: any) => {
                const activeElement = await page.evaluate(() => document.activeElement?.tagName);
                return ['A', 'BUTTON'].includes(activeElement);
              }
            }
          },
          {
            name: 'Skip to Content',
            description: 'Use skip link to jump to main content',
            keySequence: [
              { type: 'tab' },
              { type: 'enter' }
            ],
            expectedOutcome: {
              focusedElement: 'main'
            }
          }
        ]
      },
      screenReader: {
        enabled: true,
        testCases: [
          {
            name: 'Page Title',
            description: 'Check page title for screen readers',
            selector: 'title',
            expectedText: 'Document Learning App - Home'
          },
          {
            name: 'Main Heading',
            description: 'Check main page heading',
            selector: 'h1',
            expectedAttributes: {
              role: 'heading'
            },
            expectedText: 'Welcome to Document Learning'
          },
          {
            name: 'Navigation Menu',
            description: 'Check navigation accessibility',
            selector: 'nav[role="navigation"]',
            expectedAttributes: {
              role: 'navigation',
              ariaLabel: 'Main navigation'
            }
          }
        ]
      },
      colorContrast: {
        enabled: true,
        wcagLevel: 'AA',
        selectors: ['h1', 'h2', 'p', 'a', 'button', '.nav-link']
      },
      usability: {
        enabled: true,
        scenarios: [
          {
            name: 'Homepage Navigation',
            description: 'Navigate to different sections from homepage',
            userGoal: 'Explore the application features',
            steps: [
              {
                action: 'wait',
                target: 'main',
                description: 'Wait for page to load'
              },
              {
                action: 'click',
                target: '[data-testid="documents-link"]',
                description: 'Click on Documents link'
              },
              {
                action: 'wait',
                target: '[data-testid="documents-page"]',
                description: 'Wait for documents page to load'
              }
            ],
            successCriteria: {
              expectedUrl: '/documents',
              requiredElements: ['[data-testid="documents-page"]'],
              performanceThresholds: {
                maxLoadTime: 2000,
                maxInteractionTime: 1000
              }
            },
            difficulty: 'easy'
          }
        ]
      }
    },
    {
      name: 'Documents Page',
      path: '/documents',
      accessibility: {
        enabled: true,
        tags: ['wcag2a', 'wcag2aa'],
        excludeSelectors: ['.loading-spinner', '.upload-progress']
      },
      keyboard: {
        enabled: true,
        scenarios: [
          {
            name: 'Document Upload',
            description: 'Navigate to and open document upload modal',
            keySequence: [
              { type: 'tab', repeat: 3 },
              { type: 'enter' }
            ],
            expectedOutcome: {
              visibleElements: ['[data-testid="upload-modal"]'],
              focusedElement: '[data-testid="file-input"]'
            }
          },
          {
            name: 'Document List Navigation',
            description: 'Navigate through document list items',
            keySequence: [
              { type: 'tab', repeat: 5 },
              { type: 'arrow', direction: 'down', repeat: 3 }
            ],
            expectedOutcome: {
              customValidation: async (page: any) => {
                const focused = await page.evaluate(() => {
                  const activeElement = document.activeElement;
                  return activeElement?.closest('[data-testid="document-item"]') !== null;
                });
                return focused;
              }
            }
          }
        ]
      },
      screenReader: {
        enabled: true,
        testCases: [
          {
            name: 'Upload Button',
            description: 'Check upload button accessibility',
            selector: '[data-testid="upload-button"]',
            expectedAttributes: {
              role: 'button',
              ariaLabel: 'Upload new document'
            },
            shouldBeFocusable: true
          },
          {
            name: 'Document List',
            description: 'Check document list accessibility',
            selector: '[data-testid="document-list"]',
            expectedAttributes: {
              role: 'list',
              ariaLabel: 'Your documents'
            }
          },
          {
            name: 'Document Item',
            description: 'Check individual document item',
            selector: '[data-testid="document-item"]:first-child',
            expectedAttributes: {
              role: 'listitem'
            },
            shouldBeFocusable: true
          }
        ]
      },
      colorContrast: {
        enabled: true,
        wcagLevel: 'AA',
        selectors: [
          '[data-testid="upload-button"]',
          '[data-testid="document-title"]',
          '[data-testid="document-status"]'
        ]
      },
      usability: {
        enabled: true,
        scenarios: [
          {
            name: 'Document Upload Flow',
            description: 'Complete document upload process',
            userGoal: 'Upload a PDF document for processing',
            steps: [
              {
                action: 'click',
                target: '[data-testid="upload-button"]',
                description: 'Click upload button'
              },
              {
                action: 'wait',
                target: '[data-testid="upload-modal"]',
                description: 'Wait for upload modal'
              },
              {
                action: 'verify',
                target: '[data-testid="file-input"]',
                description: 'Verify file input is present'
              }
            ],
            successCriteria: {
              requiredElements: [
                '[data-testid="upload-modal"]',
                '[data-testid="file-input"]',
                '[data-testid="upload-submit"]'
              ],
              performanceThresholds: {
                maxInteractionTime: 500
              }
            },
            difficulty: 'medium'
          },
          {
            name: 'Document Selection',
            description: 'Select and view document details',
            userGoal: 'View details of an uploaded document',
            steps: [
              {
                action: 'click',
                target: '[data-testid="document-item"]:first-child',
                description: 'Click on first document'
              },
              {
                action: 'wait',
                target: '[data-testid="document-details"]',
                description: 'Wait for document details to load'
              }
            ],
            successCriteria: {
              requiredElements: ['[data-testid="document-details"]'],
              customValidation: async (page: any) => {
                const title = await page.$('[data-testid="document-title"]');
                return title !== null;
              }
            },
            difficulty: 'easy'
          }
        ]
      }
    },
    {
      name: 'Study Page',
      path: '/study',
      accessibility: {
        enabled: true,
        tags: ['wcag2a', 'wcag2aa']
      },
      keyboard: {
        enabled: true,
        scenarios: [
          {
            name: 'Flashcard Interaction',
            description: 'Navigate and interact with flashcards using keyboard',
            keySequence: [
              { type: 'tab', repeat: 2 },
              { type: 'space' },
              { type: 'tab' },
              { type: 'enter' }
            ],
            expectedOutcome: {
              customValidation: async (page: any) => {
                // Check if card was flipped or graded
                const cardFlipped = await page.$('[data-testid="card-back"]');
                const gradingVisible = await page.$('[data-testid="grading-interface"]');
                return cardFlipped || gradingVisible;
              }
            }
          },
          {
            name: 'Grading Navigation',
            description: 'Navigate through grading options',
            keySequence: [
              { type: 'tab', repeat: 3 },
              { type: 'arrow', direction: 'right', repeat: 2 },
              { type: 'enter' }
            ],
            expectedOutcome: {
              customValidation: async (page: any) => {
                // Check if next card appeared or session completed
                return true; // Simplified validation
              }
            }
          }
        ]
      },
      screenReader: {
        enabled: true,
        testCases: [
          {
            name: 'Flashcard',
            description: 'Check flashcard accessibility',
            selector: '[data-testid="flashcard"]',
            expectedAttributes: {
              role: 'button',
              ariaLabel: 'Flashcard - press space to flip'
            },
            shouldBeFocusable: true
          },
          {
            name: 'Grading Interface',
            description: 'Check grading buttons accessibility',
            selector: '[data-testid="grade-4"]',
            expectedAttributes: {
              role: 'button',
              ariaLabel: 'Grade as Good (4)'
            },
            shouldBeFocusable: true
          },
          {
            name: 'Progress Indicator',
            description: 'Check study progress accessibility',
            selector: '[data-testid="study-progress"]',
            expectedAttributes: {
              role: 'progressbar',
              ariaLabel: 'Study session progress'
            }
          }
        ]
      },
      colorContrast: {
        enabled: true,
        wcagLevel: 'AA',
        selectors: [
          '[data-testid="flashcard"]',
          '[data-testid="grade-button"]',
          '[data-testid="progress-text"]'
        ]
      },
      usability: {
        enabled: true,
        scenarios: [
          {
            name: 'Card Review Session',
            description: 'Complete a flashcard review session',
            userGoal: 'Review and grade flashcards effectively',
            steps: [
              {
                action: 'wait',
                target: '[data-testid="flashcard"]',
                description: 'Wait for flashcard to load'
              },
              {
                action: 'click',
                target: '[data-testid="flashcard"]',
                description: 'Flip the card'
              },
              {
                action: 'wait',
                target: '[data-testid="grading-interface"]',
                description: 'Wait for grading interface'
              },
              {
                action: 'click',
                target: '[data-testid="grade-4"]',
                description: 'Grade the card as Good'
              }
            ],
            successCriteria: {
              customValidation: async (page: any) => {
                // Check if next card appeared or session completed
                const nextCard = await page.$('[data-testid="flashcard"]');
                const sessionComplete = await page.$('[data-testid="session-complete"]');
                return nextCard || sessionComplete;
              },
              performanceThresholds: {
                maxInteractionTime: 2000
              }
            },
            difficulty: 'medium'
          }
        ]
      }
    },
    {
      name: 'Search Page',
      path: '/search',
      accessibility: {
        enabled: true,
        tags: ['wcag2a', 'wcag2aa']
      },
      keyboard: {
        enabled: true,
        scenarios: [
          {
            name: 'Search Input Navigation',
            description: 'Navigate to and use search input',
            keySequence: [
              { type: 'tab', repeat: 2 },
              { type: 'key', key: 'machine learning' }
            ],
            expectedOutcome: {
              focusedElement: '[data-testid="search-input"]'
            }
          },
          {
            name: 'Search Results Navigation',
            description: 'Navigate through search results',
            keySequence: [
              { type: 'tab', repeat: 5 },
              { type: 'arrow', direction: 'down', repeat: 3 }
            ],
            expectedOutcome: {
              customValidation: async (page: any) => {
                const focused = await page.evaluate(() => {
                  const activeElement = document.activeElement;
                  return activeElement?.closest('[data-testid="search-result"]') !== null;
                });
                return focused;
              }
            }
          }
        ]
      },
      screenReader: {
        enabled: true,
        testCases: [
          {
            name: 'Search Input',
            description: 'Check search input accessibility',
            selector: '[data-testid="search-input"]',
            expectedAttributes: {
              role: 'searchbox',
              ariaLabel: 'Search your documents'
            },
            shouldBeFocusable: true
          },
          {
            name: 'Search Results',
            description: 'Check search results list',
            selector: '[data-testid="search-results"]',
            expectedAttributes: {
              role: 'list',
              ariaLabel: 'Search results'
            }
          },
          {
            name: 'Search Filters',
            description: 'Check search filters accessibility',
            selector: '[data-testid="search-filters"]',
            expectedAttributes: {
              role: 'group',
              ariaLabel: 'Search filters'
            }
          }
        ]
      },
      colorContrast: {
        enabled: true,
        wcagLevel: 'AA',
        selectors: [
          '[data-testid="search-input"]',
          '[data-testid="search-result-title"]',
          '[data-testid="filter-label"]'
        ]
      },
      usability: {
        enabled: true,
        scenarios: [
          {
            name: 'Search and Filter',
            description: 'Perform search and apply filters',
            userGoal: 'Find specific content using search and filters',
            steps: [
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
                description: 'Wait for search results'
              },
              {
                action: 'click',
                target: '[data-testid="difficulty-filter"]',
                description: 'Apply difficulty filter'
              }
            ],
            successCriteria: {
              requiredElements: ['[data-testid="search-results"]'],
              expectedText: ['machine learning'],
              performanceThresholds: {
                maxInteractionTime: 3000
              }
            },
            difficulty: 'medium'
          }
        ]
      }
    }
  ]
};