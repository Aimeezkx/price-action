"""
Vector indexing service for optimizing semantic search performance
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from ..core.database import engine

logger = logging.getLogger(__name__)


class VectorIndexService:
    """Service for managing vector indexes and optimization"""
    
    def __init__(self):
        self.index_configs = {
            'knowledge_embedding_cosine': {
                'table': 'knowledge',
                'column': 'embedding',
                'method': 'ivfflat',
                'ops': 'vector_cosine_ops',
                'lists': 100  # Number of clusters for IVFFlat
            },
            'knowledge_embedding_l2': {
                'table': 'knowledge',
                'column': 'embedding',
                'method': 'ivfflat',
                'ops': 'vector_l2_ops',
                'lists': 100
            }
        }
    
    def create_vector_indexes(self, db: Session) -> Dict[str, bool]:
        """
        Create vector indexes for better search performance
        
        Returns:
            Dictionary mapping index names to creation success status
        """
        results = {}
        
        for index_name, config in self.index_configs.items():
            try:
                # Check if index already exists
                if self._index_exists(db, index_name):
                    logger.info(f"Index {index_name} already exists")
                    results[index_name] = True
                    continue
                
                # Create the index
                self._create_index(db, index_name, config)
                results[index_name] = True
                logger.info(f"Successfully created index: {index_name}")
                
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {e}")
                results[index_name] = False
        
        return results
    
    def _index_exists(self, db: Session, index_name: str) -> bool:
        """Check if an index exists"""
        try:
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = :index_name
                )
            """), {"index_name": index_name})
            
            return result.scalar()
        except Exception as e:
            logger.error(f"Failed to check if index exists: {e}")
            return False
    
    def _create_index(self, db: Session, index_name: str, config: Dict[str, Any]) -> None:
        """Create a vector index with the given configuration"""
        table = config['table']
        column = config['column']
        method = config['method']
        ops = config['ops']
        lists = config.get('lists', 100)
        
        # For IVFFlat indexes, we need to set the lists parameter
        if method == 'ivfflat':
            # Set the lists parameter for IVFFlat
            db.execute(text(f"SET ivfflat.probes = {min(lists // 4, 10)}"))
            
            # Create the index
            index_sql = f"""
                CREATE INDEX {index_name} ON {table} 
                USING {method} ({column} {ops}) 
                WITH (lists = {lists})
            """
        else:
            # For other index types
            index_sql = f"""
                CREATE INDEX {index_name} ON {table} 
                USING {method} ({column} {ops})
            """
        
        db.execute(text(index_sql))
        db.commit()
    
    def drop_vector_indexes(self, db: Session) -> Dict[str, bool]:
        """
        Drop all vector indexes
        
        Returns:
            Dictionary mapping index names to drop success status
        """
        results = {}
        
        for index_name in self.index_configs.keys():
            try:
                if self._index_exists(db, index_name):
                    db.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                    db.commit()
                    logger.info(f"Successfully dropped index: {index_name}")
                
                results[index_name] = True
                
            except Exception as e:
                logger.error(f"Failed to drop index {index_name}: {e}")
                results[index_name] = False
        
        return results
    
    def analyze_vector_performance(self, db: Session) -> Dict[str, Any]:
        """
        Analyze vector search performance and provide recommendations
        
        Returns:
            Dictionary with performance metrics and recommendations
        """
        try:
            # Get table statistics
            stats = {}
            
            # Count total knowledge points with embeddings
            result = db.execute(text("""
                SELECT COUNT(*) as total_count,
                       COUNT(embedding) as embedded_count
                FROM knowledge
            """))
            
            row = result.fetchone()
            stats['total_knowledge'] = row.total_count
            stats['embedded_knowledge'] = row.embedded_count
            stats['embedding_coverage'] = (
                row.embedded_count / row.total_count * 100 
                if row.total_count > 0 else 0
            )
            
            # Check index usage
            index_stats = {}
            for index_name in self.index_configs.keys():
                if self._index_exists(db, index_name):
                    # Get index size
                    result = db.execute(text("""
                        SELECT pg_size_pretty(pg_relation_size(:index_name)) as size
                    """), {"index_name": index_name})
                    
                    size_row = result.fetchone()
                    index_stats[index_name] = {
                        'exists': True,
                        'size': size_row.size if size_row else 'Unknown'
                    }
                else:
                    index_stats[index_name] = {'exists': False}
            
            stats['indexes'] = index_stats
            
            # Performance recommendations
            recommendations = []
            
            if stats['embedding_coverage'] < 90:
                recommendations.append(
                    "Consider updating embeddings for all knowledge points to improve search coverage"
                )
            
            if stats['embedded_knowledge'] > 1000:
                missing_indexes = [
                    name for name, info in index_stats.items() 
                    if not info['exists']
                ]
                if missing_indexes:
                    recommendations.append(
                        f"Create vector indexes for better performance: {', '.join(missing_indexes)}"
                    )
            
            if stats['embedded_knowledge'] > 10000:
                recommendations.append(
                    "Consider using HNSW indexes for very large datasets (requires pgvector 0.5.0+)"
                )
            
            stats['recommendations'] = recommendations
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to analyze vector performance: {e}")
            return {'error': str(e)}
    
    def optimize_vector_search_settings(self, db: Session) -> Dict[str, Any]:
        """
        Optimize PostgreSQL settings for vector search
        
        Returns:
            Dictionary with optimization results
        """
        try:
            optimizations = {}
            
            # Set optimal work_mem for vector operations
            db.execute(text("SET work_mem = '256MB'"))
            optimizations['work_mem'] = '256MB'
            
            # Set optimal maintenance_work_mem for index creation
            db.execute(text("SET maintenance_work_mem = '1GB'"))
            optimizations['maintenance_work_mem'] = '1GB'
            
            # Optimize IVFFlat settings based on data size
            result = db.execute(text("SELECT COUNT(*) FROM knowledge WHERE embedding IS NOT NULL"))
            embedded_count = result.scalar()
            
            if embedded_count > 0:
                # Set probes based on data size (rule of thumb: sqrt(lists))
                lists = self.index_configs['knowledge_embedding_cosine']['lists']
                probes = max(1, min(lists // 4, int(lists ** 0.5)))
                
                db.execute(text(f"SET ivfflat.probes = {probes}"))
                optimizations['ivfflat_probes'] = probes
                
                # Recommend optimal lists value
                optimal_lists = max(embedded_count // 1000, 10)
                optimal_lists = min(optimal_lists, 1000)  # Cap at 1000
                
                optimizations['recommended_lists'] = optimal_lists
                
                if optimal_lists != lists:
                    optimizations['recommendation'] = (
                        f"Consider recreating indexes with lists={optimal_lists} "
                        f"for optimal performance with {embedded_count} embeddings"
                    )
            
            db.commit()
            
            logger.info("Vector search settings optimized")
            return optimizations
            
        except Exception as e:
            logger.error(f"Failed to optimize vector search settings: {e}")
            return {'error': str(e)}
    
    def vacuum_analyze_vector_tables(self, db: Session) -> Dict[str, bool]:
        """
        Run VACUUM ANALYZE on tables with vector columns for optimal performance
        
        Returns:
            Dictionary mapping table names to success status
        """
        results = {}
        tables = ['knowledge']  # Tables with vector columns
        
        for table in tables:
            try:
                # VACUUM ANALYZE to update statistics and reclaim space
                db.execute(text(f"VACUUM ANALYZE {table}"))
                results[table] = True
                logger.info(f"Successfully vacuumed and analyzed table: {table}")
                
            except Exception as e:
                logger.error(f"Failed to vacuum analyze table {table}: {e}")
                results[table] = False
        
        return results


# Global vector index service instance
vector_index_service = VectorIndexService()