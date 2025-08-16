import puppeteer, { Browser, Page } from 'puppeteer';

export interface ColorContrastConfig {
  url: string;
  selectors?: string[];
  wcagLevel: 'AA' | 'AAA';
  includeAllText?: boolean;
  viewport?: { width: number; height: number };
}

export interface ColorContrastResult {
  selector: string;
  text: string;
  foregroundColor: string;
  backgroundColor: string;
  contrastRatio: number;
  wcagAA: {
    normal: boolean;
    large: boolean;
  };
  wcagAAA: {
    normal: boolean;
    large: boolean;
  };
  fontSize: number;
  fontWeight: string;
  passed: boolean;
  level: 'AA' | 'AAA';
}

export interface ColorContrastReport {
  url: string;
  timestamp: Date;
  results: ColorContrastResult[];
  summary: {
    total: number;
    passed: number;
    failed: number;
    passRate: number;
  };
}

export class ColorContrastValidator {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async setup(): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
  }

  async teardown(): Promise<void> {
    if (this.page) {
      await this.page.close();
    }
    if (this.browser) {
      await this.browser.close();
    }
  }

  async validateColorContrast(config: ColorContrastConfig): Promise<ColorContrastReport> {
    if (!this.page) {
      throw new Error('Validator not initialized. Call setup() first.');
    }

    // Set viewport if specified
    if (config.viewport) {
      await this.page.setViewport(config.viewport);
    }

    // Navigate to the page
    await this.page.goto(config.url, { waitUntil: 'networkidle0' });

    // Get text elements to test
    const textElements = await this.getTextElements(config);
    
    // Test each element
    const results: ColorContrastResult[] = [];
    for (const element of textElements) {
      const result = await this.testElement(element, config.wcagLevel);
      if (result) {
        results.push(result);
      }
    }

    // Generate summary
    const passed = results.filter(r => r.passed).length;
    const summary = {
      total: results.length,
      passed,
      failed: results.length - passed,
      passRate: results.length > 0 ? (passed / results.length) * 100 : 0
    };

    return {
      url: config.url,
      timestamp: new Date(),
      results,
      summary
    };
  }

  private async getTextElements(config: ColorContrastConfig): Promise<Array<{selector: string, element: any}>> {
    if (!this.page) return [];

    if (config.selectors && config.selectors.length > 0) {
      // Test specific selectors
      const elements = [];
      for (const selector of config.selectors) {
        const element = await this.page.$(selector);
        if (element) {
          elements.push({ selector, element });
        }
      }
      return elements;
    }

    if (config.includeAllText) {
      // Find all text elements
      return await this.page.evaluate(() => {
        const textElements: Array<{selector: string, element: Element}> = [];
        const walker = document.createTreeWalker(
          document.body,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: (node) => {
              const text = node.textContent?.trim();
              if (!text || text.length < 3) return NodeFilter.FILTER_REJECT;
              
              const parent = node.parentElement;
              if (!parent) return NodeFilter.FILTER_REJECT;
              
              // Skip hidden elements
              const style = window.getComputedStyle(parent);
              if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                return NodeFilter.FILTER_REJECT;
              }
              
              return NodeFilter.FILTER_ACCEPT;
            }
          }
        );

        let node;
        const processedElements = new Set();
        
        while (node = walker.nextNode()) {
          const parent = node.parentElement;
          if (parent && !processedElements.has(parent)) {
            processedElements.add(parent);
            
            // Generate a selector for the element
            let selector = parent.tagName.toLowerCase();
            if (parent.id) {
              selector = `#${parent.id}`;
            } else if (parent.className) {
              selector += `.${parent.className.split(' ').join('.')}`;
            }
            
            // Add position if needed for uniqueness
            const siblings = Array.from(parent.parentElement?.children || []);
            const index = siblings.indexOf(parent);
            if (siblings.filter(s => s.tagName === parent.tagName).length > 1) {
              selector += `:nth-child(${index + 1})`;
            }
            
            textElements.push({ selector, element: parent });
          }
        }

        return textElements.slice(0, 50); // Limit to avoid too many tests
      });
    }

    // Default: test common text elements
    const commonSelectors = [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'span', 'div', 'a', 'button',
      'label', 'input', 'textarea',
      '.text', '.content', '.description'
    ];

    const elements = [];
    for (const selector of commonSelectors) {
      const elementHandles = await this.page.$$(selector);
      for (let i = 0; i < elementHandles.length; i++) {
        elements.push({
          selector: `${selector}:nth-child(${i + 1})`,
          element: elementHandles[i]
        });
      }
    }

    return elements.slice(0, 30); // Limit to avoid too many tests
  }

  private async testElement(elementInfo: {selector: string, element: any}, wcagLevel: 'AA' | 'AAA'): Promise<ColorContrastResult | null> {
    if (!this.page) return null;

    try {
      const elementData = await this.page.evaluate((el) => {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        
        // Skip if element is not visible
        if (rect.width === 0 || rect.height === 0) return null;
        
        return {
          text: el.textContent?.trim() || '',
          color: style.color,
          backgroundColor: style.backgroundColor,
          fontSize: parseFloat(style.fontSize),
          fontWeight: style.fontWeight,
          display: style.display,
          visibility: style.visibility,
          opacity: style.opacity
        };
      }, elementInfo.element);

      if (!elementData || !elementData.text || elementData.text.length < 3) {
        return null;
      }

      // Skip if element is hidden
      if (elementData.display === 'none' || elementData.visibility === 'hidden' || elementData.opacity === '0') {
        return null;
      }

      // Get effective background color (may need to traverse up the DOM)
      const effectiveBackgroundColor = await this.getEffectiveBackgroundColor(elementInfo.element);
      
      // Calculate contrast ratio
      const foregroundRgb = this.parseColor(elementData.color);
      const backgroundRgb = this.parseColor(effectiveBackgroundColor);
      
      if (!foregroundRgb || !backgroundRgb) {
        return null;
      }

      const contrastRatio = this.calculateContrastRatio(foregroundRgb, backgroundRgb);
      
      // Determine if text is large (18pt+ or 14pt+ bold)
      const isLargeText = elementData.fontSize >= 18 || 
                         (elementData.fontSize >= 14 && (elementData.fontWeight === 'bold' || parseInt(elementData.fontWeight) >= 700));

      // WCAG compliance checks
      const wcagAA = {
        normal: contrastRatio >= 4.5,
        large: contrastRatio >= 3.0
      };

      const wcagAAA = {
        normal: contrastRatio >= 7.0,
        large: contrastRatio >= 4.5
      };

      const passed = wcagLevel === 'AA' 
        ? (isLargeText ? wcagAA.large : wcagAA.normal)
        : (isLargeText ? wcagAAA.large : wcagAAA.normal);

      return {
        selector: elementInfo.selector,
        text: elementData.text.substring(0, 100), // Truncate long text
        foregroundColor: elementData.color,
        backgroundColor: effectiveBackgroundColor,
        contrastRatio: Math.round(contrastRatio * 100) / 100,
        wcagAA,
        wcagAAA,
        fontSize: elementData.fontSize,
        fontWeight: elementData.fontWeight,
        passed,
        level: wcagLevel
      };

    } catch (error) {
      console.warn(`Error testing element ${elementInfo.selector}:`, error);
      return null;
    }
  }

  private async getEffectiveBackgroundColor(element: any): Promise<string> {
    if (!this.page) return 'rgb(255, 255, 255)';

    return await this.page.evaluate((el) => {
      let currentElement = el;
      
      while (currentElement && currentElement !== document.body) {
        const style = window.getComputedStyle(currentElement);
        const bgColor = style.backgroundColor;
        
        // If we find a non-transparent background, use it
        if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {
          return bgColor;
        }
        
        currentElement = currentElement.parentElement;
      }
      
      // Default to white background
      return 'rgb(255, 255, 255)';
    }, element);
  }

  private parseColor(colorString: string): {r: number, g: number, b: number} | null {
    // Handle rgb() and rgba() formats
    const rgbMatch = colorString.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (rgbMatch) {
      return {
        r: parseInt(rgbMatch[1]),
        g: parseInt(rgbMatch[2]),
        b: parseInt(rgbMatch[3])
      };
    }

    // Handle hex colors
    const hexMatch = colorString.match(/^#([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
    if (hexMatch) {
      return {
        r: parseInt(hexMatch[1], 16),
        g: parseInt(hexMatch[2], 16),
        b: parseInt(hexMatch[3], 16)
      };
    }

    // Handle named colors (basic set)
    const namedColors: Record<string, {r: number, g: number, b: number}> = {
      'black': {r: 0, g: 0, b: 0},
      'white': {r: 255, g: 255, b: 255},
      'red': {r: 255, g: 0, b: 0},
      'green': {r: 0, g: 128, b: 0},
      'blue': {r: 0, g: 0, b: 255},
      'gray': {r: 128, g: 128, b: 128},
      'grey': {r: 128, g: 128, b: 128}
    };

    return namedColors[colorString.toLowerCase()] || null;
  }

  private calculateContrastRatio(color1: {r: number, g: number, b: number}, color2: {r: number, g: number, b: number}): number {
    const luminance1 = this.getLuminance(color1);
    const luminance2 = this.getLuminance(color2);
    
    const lighter = Math.max(luminance1, luminance2);
    const darker = Math.min(luminance1, luminance2);
    
    return (lighter + 0.05) / (darker + 0.05);
  }

  private getLuminance(color: {r: number, g: number, b: number}): number {
    const rsRGB = color.r / 255;
    const gsRGB = color.g / 255;
    const bsRGB = color.b / 255;

    const r = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
    const g = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
    const b = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  generateReport(report: ColorContrastReport): string {
    let output = '# Color Contrast Validation Report\n\n';
    output += `**URL**: ${report.url}\n`;
    output += `**Generated**: ${report.timestamp.toISOString()}\n\n`;

    output += '## Summary\n\n';
    output += `- **Total Elements Tested**: ${report.summary.total}\n`;
    output += `- **Passed**: ${report.summary.passed}\n`;
    output += `- **Failed**: ${report.summary.failed}\n`;
    output += `- **Pass Rate**: ${report.summary.passRate.toFixed(1)}%\n\n`;

    if (report.results.length === 0) {
      output += '## No Results\n\nNo text elements were found to test.\n';
      return output;
    }

    // Group results by pass/fail
    const passed = report.results.filter(r => r.passed);
    const failed = report.results.filter(r => !r.passed);

    if (failed.length > 0) {
      output += '## ❌ Failed Elements\n\n';
      output += '| Element | Text | Contrast Ratio | Required | Status |\n';
      output += '|---------|------|----------------|----------|--------|\n';
      
      for (const result of failed) {
        const required = result.level === 'AA' 
          ? (result.fontSize >= 18 || (result.fontSize >= 14 && result.fontWeight === 'bold') ? '3.0' : '4.5')
          : (result.fontSize >= 18 || (result.fontSize >= 14 && result.fontWeight === 'bold') ? '4.5' : '7.0');
        
        const truncatedText = result.text.length > 30 ? result.text.substring(0, 30) + '...' : result.text;
        output += `| \`${result.selector}\` | ${truncatedText} | ${result.contrastRatio} | ${required} | ❌ |\n`;
      }
      output += '\n';
    }

    if (passed.length > 0) {
      output += '## ✅ Passed Elements\n\n';
      output += `${passed.length} elements passed the color contrast requirements.\n\n`;
    }

    // Detailed results
    output += '## Detailed Results\n\n';
    
    for (const result of report.results) {
      const status = result.passed ? '✅' : '❌';
      output += `### ${status} ${result.selector}\n\n`;
      
      output += `**Text**: "${result.text}"\n\n`;
      output += `**Colors**:\n`;
      output += `- Foreground: ${result.foregroundColor}\n`;
      output += `- Background: ${result.backgroundColor}\n\n`;
      
      output += `**Typography**:\n`;
      output += `- Font Size: ${result.fontSize}px\n`;
      output += `- Font Weight: ${result.fontWeight}\n\n`;
      
      output += `**Contrast Ratio**: ${result.contrastRatio}:1\n\n`;
      
      output += `**WCAG Compliance**:\n`;
      output += `- AA Normal Text (4.5:1): ${result.wcagAA.normal ? '✅' : '❌'}\n`;
      output += `- AA Large Text (3.0:1): ${result.wcagAA.large ? '✅' : '❌'}\n`;
      output += `- AAA Normal Text (7.0:1): ${result.wcagAAA.normal ? '✅' : '❌'}\n`;
      output += `- AAA Large Text (4.5:1): ${result.wcagAAA.large ? '✅' : '❌'}\n\n`;
      
      output += '---\n\n';
    }

    return output;
  }
}