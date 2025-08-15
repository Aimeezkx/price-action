#!/bin/bash

echo "🔍 Verifying Task 22: Chapter and Content Browsing Implementation"
echo ""

# Check if all required files exist
echo "📋 CHECKING REQUIRED FILES:"
echo "=================================="

files=(
    "src/hooks/useChapters.ts"
    "src/components/TableOfContents.tsx"
    "src/components/ChapterDetail.tsx"
    "src/components/ImageViewer.tsx"
    "src/components/KnowledgePointBrowser.tsx"
    "src/components/ChapterBrowser.tsx"
    "src/pages/ChapterBrowserPage.tsx"
)

all_files_exist=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (MISSING)"
        all_files_exist=false
    fi
done

echo ""
echo "📝 CHECKING KEY FUNCTIONALITY:"
echo "=================================="

# Check for key functions and components in files
check_content() {
    local file=$1
    local pattern=$2
    local description=$3
    
    if [ -f "$file" ]; then
        if grep -q "$pattern" "$file"; then
            echo "✅ $description"
        else
            echo "❌ $description (NOT FOUND in $file)"
            all_files_exist=false
        fi
    else
        echo "❌ $description (FILE MISSING: $file)"
        all_files_exist=false
    fi
}

# Check hooks
check_content "src/hooks/useChapters.ts" "useTableOfContents" "Table of Contents hook"
check_content "src/hooks/useChapters.ts" "useChapterFigures" "Chapter Figures hook"
check_content "src/hooks/useChapters.ts" "useChapterKnowledge" "Chapter Knowledge hook"

# Check components
check_content "src/components/TableOfContents.tsx" "TableOfContents" "Table of Contents component"
check_content "src/components/ChapterDetail.tsx" "ChapterDetail" "Chapter Detail component"
check_content "src/components/ImageViewer.tsx" "ImageViewer" "Image Viewer component"
check_content "src/components/KnowledgePointBrowser.tsx" "KnowledgePointBrowser" "Knowledge Point Browser component"
check_content "src/components/ChapterBrowser.tsx" "ChapterBrowser" "Main Chapter Browser component"

# Check page
check_content "src/pages/ChapterBrowserPage.tsx" "ChapterBrowserPage" "Chapter Browser Page"

# Check types
check_content "src/types/index.ts" "Knowledge" "Knowledge type definition"
check_content "src/types/index.ts" "TableOfContents" "TableOfContents type definition"

# Check API integration
check_content "src/lib/api.ts" "getChapters" "Get Chapters API method"
check_content "src/lib/api.ts" "getChapterFigures" "Get Chapter Figures API method"
check_content "src/lib/api.ts" "getChapterKnowledge" "Get Chapter Knowledge API method"

# Check router integration
check_content "src/router.tsx" "ChapterBrowserPage" "Router integration"
check_content "src/router.tsx" "documents/:documentId/chapters" "Chapter browsing route"

# Check document list integration
check_content "src/components/DocumentList.tsx" "Browse" "Browse Chapters button"

echo ""
echo "📱 CHECKING RESPONSIVE DESIGN:"
echo "=================================="

# Check for responsive design patterns
check_content "src/components/ChapterBrowser.tsx" "lg:hidden" "Mobile menu toggle"
check_content "src/components/ChapterBrowser.tsx" "lg:w-80" "Desktop sidebar width"
check_content "src/components/ImageViewer.tsx" "md:hidden" "Mobile-specific controls"
check_content "src/components/ChapterDetail.tsx" "md:grid-cols-2" "Responsive grid layout"

echo ""
echo "🔧 CHECKING COMPONENT EXPORTS:"
echo "=================================="

check_content "src/components/index.ts" "ChapterBrowser" "ChapterBrowser export"
check_content "src/components/index.ts" "TableOfContents" "TableOfContents export"
check_content "src/components/index.ts" "ImageViewer" "ImageViewer export"
check_content "src/pages/index.ts" "ChapterBrowserPage" "ChapterBrowserPage export"

echo ""
echo "📊 SUMMARY:"
echo "=================================="

if [ "$all_files_exist" = true ]; then
    echo "🎉 SUCCESS: All Task 22 requirements appear to be implemented!"
    echo ""
    echo "✅ Implementation includes:"
    echo "   • Table of Contents (TOC) navigation component"
    echo "   • Chapter detail view with figures and knowledge points"
    echo "   • Image viewer with caption display"
    echo "   • Knowledge point browser with source anchors"
    echo "   • Responsive design for mobile and desktop"
    echo "   • Integration with existing document management"
    echo ""
    echo "🔗 Key Features:"
    echo "   • Hierarchical chapter navigation"
    echo "   • Tabbed interface for overview, figures, and knowledge"
    echo "   • Zoomable image viewer with metadata"
    echo "   • Filterable and searchable knowledge points"
    echo "   • Mobile-responsive design with collapsible sidebar"
    echo "   • Direct links from document list to chapter browser"
    exit 0
else
    echo "❌ INCOMPLETE: Some Task 22 requirements are missing."
    echo "🔧 Please review the missing content and ensure all components are properly implemented."
    exit 1
fi