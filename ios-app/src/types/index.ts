// Shared types between web and iOS app
export interface Document {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chapter_count: number;
  figure_count: number;
  knowledge_count: number;
  created_at: string;
}

export interface Chapter {
  id: string;
  title: string;
  level: number;
  figures: Figure[];
  knowledge_count: number;
}

export interface Figure {
  id: string;
  image_path: string;
  caption: string;
  page_number: number;
  bbox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface Card {
  id: string;
  card_type: 'qa' | 'cloze' | 'image_hotspot';
  front: string;
  back: string;
  difficulty: number;
  due_date: string;
  metadata: Record<string, any>;
}

export interface Knowledge {
  id: string;
  kind: 'definition' | 'fact' | 'theorem' | 'process' | 'example';
  text: string;
  entities: string[];
  anchors: {
    page?: number;
    chapter?: string;
    position?: number;
  };
  confidence_score?: number;
  created_at: string;
}

export interface TableOfContents {
  document_id: string;
  document_title: string;
  total_chapters: number;
  chapters: ChapterTOC[];
}

export interface ChapterTOC {
  id: string;
  title: string;
  level: number;
  order_index: number;
  page_start?: number;
  page_end?: number;
  has_content: boolean;
}

export interface SearchResult {
  id: string;
  type: 'knowledge' | 'card';
  title: string;
  content: string;
  chapter_title?: string;
  highlights?: string[];
}

export interface CardFilters {
  chapter?: string;
  difficulty?: string;
  cardType?: string;
}

export interface Hotspot {
  id: string;
  x: number; // percentage
  y: number; // percentage
  width: number; // percentage
  height: number; // percentage
  label: string;
  description?: string;
  correct: boolean;
}