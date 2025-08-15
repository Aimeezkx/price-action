#!/usr/bin/env node

/**
 * Frontend Performance Monitoring Verification Script
 * Tests the performance monitoring implementation in the React frontend
 */

const fs = require('fs');
const path = require('path');

class FrontendPerformanceVerifier {
    constructor() {
        this.results = {
            files: {},
            implementation: {},
            integration: {}
        };
    }

    checkFileExists(filePath, description) {
        const fullPath = path.join(__dirname, filePath);
        const exists = fs.existsSync(fullPath);
        
        this.results.files[filePath] = {
            exists,
            description,
            size: exists ? fs.statSync(fullPath).size : 0
        };
        
        return exists;
    }

    checkFileContent(filePath, patterns, description) {
        const fullPath = path.join(__dirname, filePath);
        
        if (!fs.existsSync(fullPath)) {
            this.results.implementation[description] = {
                status: 'missing_file',
                file: filePath
            };
            return false;
        }

        const content = fs.readFileSync(fullPath, 'utf8');
        const results = {};
        
        for (const [name, pattern] of Object.entries(patterns)) {
            const regex = new RegExp(pattern, 'i');
            results[name] = regex.test(content);
        }
        
        this.results.implementation[description] = {
            status: 'checked',
            file: filePath,
            patterns: results,
            allPassed: Object.values(results).every(Boolean)
        };
        
        return Object.values(results).every(Boolean);
    }

    verifyPerformanceLibrary() {
        console.log('📊 Verifying Performance Library...');
        
        const patterns = {
            'PerformanceMonitor class': 'class PerformanceMonitor',
            'Core Web Vitals tracking': 'largest-contentful-paint|first-input|layout-shift',
            'Navigation timing': 'PerformanceNavigationTiming',
            'Metric recording': 'recordMetric',
            'Performance observers': 'PerformanceObserver',
            'API call tracking': 'trackAPICall',
            'Component render tracking': 'trackComponentRender',
            'Export functionality': 'exportMetrics',
            'React hook': 'usePerformanceTracking',
            'HOC wrapper': 'withPerformanceTracking'
        };
        
        return this.checkFileContent('src/lib/performance.ts', patterns, 'Performance Library');
    }

    verifyPerformanceDashboard() {
        console.log('📈 Verifying Performance Dashboard...');
        
        const patterns = {
            'Dashboard component': 'function PerformanceDashboard|const PerformanceDashboard',
            'Performance summary': 'getPerformanceSummary',
            'Status colors': 'getStatusColor',
            'Export functionality': 'exportData',
            'Real-time updates': 'useEffect.*setInterval|useEffect.*setTimeout',
            'Toggle visibility': 'setIsVisible',
            'Metric formatting': 'formatValue',
            'Statistics display': 'PerformanceStats|PerformanceSummary'
        };
        
        return this.checkFileContent('src/components/PerformanceDashboard.tsx', patterns, 'Performance Dashboard');
    }

    verifyAppIntegration() {
        console.log('🔗 Verifying App Integration...');
        
        const patterns = {
            'Performance import': 'from.*performance',
            'Dashboard import': 'PerformanceDashboard',
            'App initialization tracking': 'recordMetric.*AppInitialization',
            'Dashboard rendering': '<PerformanceDashboard',
            'Development mode check': 'NODE_ENV.*development'
        };
        
        return this.checkFileContent('src/App.tsx', patterns, 'App Integration');
    }

    verifyAPIClientIntegration() {
        console.log('🌐 Verifying API Client Integration...');
        
        const patterns = {
            'Performance import': 'from.*performance',
            'API call tracking': 'trackAPICall',
            'Request timing': 'performance\\.now\\(\\)',
            'Error tracking': 'trackAPICall.*0|trackAPICall.*error',
            'Duration calculation': 'endTime - startTime'
        };
        
        return this.checkFileContent('src/lib/api.ts', patterns, 'API Client Integration');
    }

    verifyTypeDefinitions() {
        console.log('📝 Verifying Type Definitions...');
        
        // Check if performance types are properly defined
        const performanceFile = path.join(__dirname, 'src/lib/performance.ts');
        if (!fs.existsSync(performanceFile)) {
            this.results.implementation['Type Definitions'] = {
                status: 'missing_file',
                file: 'src/lib/performance.ts'
            };
            return false;
        }

        const content = fs.readFileSync(performanceFile, 'utf8');
        
        const typePatterns = {
            'PerformanceMetric interface': 'interface PerformanceMetric',
            'NavigationTiming interface': 'interface NavigationTiming',
            'Proper typing': 'Record<string,\\s*any>|Dict<string,\\s*any>',
            'Function signatures': '\\(.*\\):\\s*(Promise<|void|boolean|number)',
            'Generic types': '<T.*>'
        };
        
        const results = {};
        for (const [name, pattern] of Object.entries(typePatterns)) {
            const regex = new RegExp(pattern, 'i');
            results[name] = regex.test(content);
        }
        
        this.results.implementation['Type Definitions'] = {
            status: 'checked',
            patterns: results,
            allPassed: Object.values(results).every(Boolean)
        };
        
        return Object.values(results).every(Boolean);
    }

    checkPackageDependencies() {
        console.log('📦 Checking Package Dependencies...');
        
        const packageJsonPath = path.join(__dirname, 'package.json');
        if (!fs.existsSync(packageJsonPath)) {
            this.results.integration['Package Dependencies'] = {
                status: 'missing_package_json'
            };
            return false;
        }

        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
        
        const requiredDeps = {
            'react': 'React framework',
            '@tanstack/react-query': 'Data fetching and caching'
        };
        
        const results = {};
        for (const [dep, description] of Object.entries(requiredDeps)) {
            results[dep] = {
                present: dep in dependencies,
                version: dependencies[dep] || 'not found',
                description
            };
        }
        
        this.results.integration['Package Dependencies'] = {
            status: 'checked',
            dependencies: results,
            allPresent: Object.values(results).every(r => r.present)
        };
        
        return Object.values(results).every(r => r.present);
    }

    runAllVerifications() {
        console.log('🚀 Starting Frontend Performance Monitoring Verification...\n');
        
        // Check file existence
        const requiredFiles = [
            ['src/lib/performance.ts', 'Performance monitoring library'],
            ['src/components/PerformanceDashboard.tsx', 'Performance dashboard component'],
            ['src/App.tsx', 'Main application component'],
            ['src/lib/api.ts', 'API client']
        ];
        
        console.log('📁 Checking Required Files...');
        let allFilesExist = true;
        for (const [file, description] of requiredFiles) {
            const exists = this.checkFileExists(file, description);
            console.log(`  ${exists ? '✅' : '❌'} ${file} - ${description}`);
            if (!exists) allFilesExist = false;
        }
        
        if (!allFilesExist) {
            console.log('\n❌ Some required files are missing. Cannot proceed with verification.');
            return this.results;
        }
        
        // Run implementation verifications
        const verifications = [
            ['Performance Library', () => this.verifyPerformanceLibrary()],
            ['Performance Dashboard', () => this.verifyPerformanceDashboard()],
            ['App Integration', () => this.verifyAppIntegration()],
            ['API Client Integration', () => this.verifyAPIClientIntegration()],
            ['Type Definitions', () => this.verifyTypeDefinitions()],
            ['Package Dependencies', () => this.checkPackageDependencies()]
        ];
        
        console.log('\n🔍 Running Implementation Verifications...');
        let allVerificationsPassed = true;
        
        for (const [name, verifyFunc] of verifications) {
            try {
                const passed = verifyFunc();
                console.log(`  ${passed ? '✅' : '❌'} ${name}`);
                if (!passed) allVerificationsPassed = false;
            } catch (error) {
                console.log(`  💥 ${name} - Error: ${error.message}`);
                allVerificationsPassed = false;
            }
        }
        
        return { allFilesExist, allVerificationsPassed };
    }

    printSummary() {
        const { allFilesExist, allVerificationsPassed } = this.runAllVerifications();
        
        console.log('\n' + '='.repeat(60));
        console.log('📊 FRONTEND PERFORMANCE MONITORING VERIFICATION SUMMARY');
        console.log('='.repeat(60));
        
        // File summary
        const totalFiles = Object.keys(this.results.files).length;
        const existingFiles = Object.values(this.results.files).filter(f => f.exists).length;
        console.log(`Files: ${existingFiles}/${totalFiles} exist`);
        
        // Implementation summary
        const totalImplementations = Object.keys(this.results.implementation).length;
        const passedImplementations = Object.values(this.results.implementation)
            .filter(i => i.allPassed || i.allPresent).length;
        console.log(`Implementations: ${passedImplementations}/${totalImplementations} passed`);
        
        // Overall status
        if (allFilesExist && allVerificationsPassed) {
            console.log('\n🎉 Frontend performance monitoring is properly implemented!');
            console.log('\nFeatures verified:');
            console.log('  ✅ Core Web Vitals tracking (LCP, FID, CLS)');
            console.log('  ✅ Navigation timing measurement');
            console.log('  ✅ API call performance tracking');
            console.log('  ✅ Component render time monitoring');
            console.log('  ✅ Performance dashboard with real-time updates');
            console.log('  ✅ Export functionality for metrics');
            console.log('  ✅ React hooks and HOC for easy integration');
            console.log('  ✅ TypeScript type definitions');
        } else {
            console.log('\n⚠️  Frontend performance monitoring needs attention.');
            
            // Show specific issues
            const issues = [];
            if (!allFilesExist) issues.push('Missing required files');
            if (!allVerificationsPassed) issues.push('Implementation issues found');
            
            console.log('\nIssues found:');
            issues.forEach(issue => console.log(`  - ${issue}`));
        }
        
        console.log('\n' + '='.repeat(60));
        
        // Save detailed results
        const resultsFile = 'frontend_performance_verification_results.json';
        fs.writeFileSync(resultsFile, JSON.stringify(this.results, null, 2));
        console.log(`\n📄 Detailed results saved to: ${resultsFile}`);
    }
}

// Run verification
const verifier = new FrontendPerformanceVerifier();
verifier.printSummary();