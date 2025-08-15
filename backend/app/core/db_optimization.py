"""
Database optimization utilities
Includes query optimization, indexing strategies, and performance analysis
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from .database import get_db_session

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database optimization and analysis utilities"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        
    async def analyze_query_performance(self, session: Session) -> Dict[str, Any]:
        """Analyze database query performance"""
        try:
            # Get slow queries from PostgreSQL stats
            slow_queries_query = text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_time > 100  -- Queries slower than 100ms
                ORDER BY mean_time DESC 
                LIMIT 10
            """)
            
            result = session.execute(slow_queries_query)
            slow_queries = [dict(row._mapping) for row in result]
            
            # Get table statistics
            table_stats_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """)
            
            result = session.execute(table_stats_query)
            table_stats = [dict(row._mapping) for row in result]
            
            # Get index usage statistics
            index_usage_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan > 0
                ORDER BY idx_scan DESC
            """)
            
            result = session.execute(index_usage_query)
            index_usage = [dict(row._mapping) for row in result]
            
            return {
                "slow_queries": slow_queries,
                "table_statistics": table_stats,
                "index_usage": index_usage
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {"error": str(e)}
    
    async def get_missing_indexes(self, session: Session) -> List[Dict[str, Any]]:
        """Identify potentially missing indexes"""
        try:
            # Query to find tables with sequential scans
            missing_indexes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    CASE 
                        WHEN seq_scan > 0 AND idx_scan = 0 THEN 'No index usage'
                        WHEN seq_tup_read > idx_tup_fetch * 10 THEN 'High sequential scan ratio'
                        ELSE 'OK'
                    END as recommendation
                FROM pg_stat_user_tables
                WHERE seq_scan > 100  -- Tables with many sequential scans
                ORDER BY seq_tup_read DESC
            """)
            
            result = session.execute(missing_indexes_query)
            return [dict(row._mapping) for row in result]
            
        except Exception as e:
            logger.error(f"Error identifying missing indexes: {e}")
            return []
    
    async def optimize_tables(self, session: Session) -> Dict[str, Any]:
        """Run table optimization commands"""
        try:
            results = {}
            
            # Get list of tables that need optimization
            tables_query = text("""
                SELECT tablename 
                FROM pg_stat_user_tables 
                WHERE n_dead_tup > n_live_tup * 0.1  -- More than 10% dead tuples
            """)
            
            result = session.execute(tables_query)
            tables_to_optimize = [row[0] for row in result]
            
            for table in tables_to_optimize:
                try:
                    # Run VACUUM ANALYZE
                    session.execute(text(f"VACUUM ANALYZE {table}"))
                    results[table] = "optimized"
                    logger.info(f"Optimized table: {table}")
                except Exception as e:
                    results[table] = f"error: {str(e)}"
                    logger.error(f"Error optimizing table {table}: {e}")
            
            session.commit()
            return {"optimized_tables": results}
            
        except Exception as e:
            logger.error(f"Error optimizing tables: {e}")
            return {"error": str(e)}
    
    async def create_performance_indexes(self, session: Session) -> Dict[str, Any]:
        """Create performance-oriented indexes"""
        indexes_to_create = [
            # Document processing performance
            {
                "name": "idx_documents_status_created",
                "table": "documents",
                "columns": ["status", "created_at"],
                "description": "Optimize document status queries with date filtering"
            },
            {
                "name": "idx_chapters_document_order",
                "table": "chapters", 
                "columns": ["document_id", "order_index"],
                "description": "Optimize chapter ordering queries"
            },
            {
                "name": "idx_knowledge_chapter_kind",
                "table": "knowledge",
                "columns": ["chapter_id", "kind"],
                "description": "Optimize knowledge filtering by type"
            },
            {
                "name": "idx_cards_knowledge_type",
                "table": "cards",
                "columns": ["knowledge_id", "card_type"],
                "description": "Optimize card queries by type"
            },
            {
                "name": "idx_srs_due_date_user",
                "table": "srs",
                "columns": ["due_date", "user_id"],
                "description": "Optimize SRS review queries"
            },
            {
                "name": "idx_knowledge_embedding_cosine",
                "table": "knowledge",
                "columns": ["embedding"],
                "type": "ivfflat",
                "options": "vector_cosine_ops WITH (lists = 100)",
                "description": "Optimize vector similarity search"
            }
        ]
        
        results = {}
        
        for index_info in indexes_to_create:
            try:
                # Check if index already exists
                check_query = text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE indexname = :index_name
                """)
                
                result = session.execute(check_query, {"index_name": index_info["name"]})
                if result.fetchone():
                    results[index_info["name"]] = "already exists"
                    continue
                
                # Create the index
                if index_info.get("type") == "ivfflat":
                    # Vector index
                    create_query = text(f"""
                        CREATE INDEX {index_info["name"]} 
                        ON {index_info["table"]} 
                        USING ivfflat ({index_info["columns"][0]}) 
                        {index_info.get("options", "")}
                    """)
                else:
                    # Regular B-tree index
                    columns = ", ".join(index_info["columns"])
                    create_query = text(f"""
                        CREATE INDEX {index_info["name"]} 
                        ON {index_info["table"]} ({columns})
                    """)
                
                session.execute(create_query)
                results[index_info["name"]] = "created"
                logger.info(f"Created index: {index_info['name']} - {index_info['description']}")
                
            except Exception as e:
                results[index_info["name"]] = f"error: {str(e)}"
                logger.error(f"Error creating index {index_info['name']}: {e}")
        
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error committing index creation: {e}")
            
        return {"created_indexes": results}
    
    async def get_database_size_info(self, session: Session) -> Dict[str, Any]:
        """Get database size and space usage information"""
        try:
            # Database size
            db_size_query = text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as database_size
            """)
            result = session.execute(db_size_query)
            db_size = result.fetchone()[0]
            
            # Table sizes
            table_sizes_query = text("""
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            result = session.execute(table_sizes_query)
            table_sizes = [dict(row._mapping) for row in result]
            
            # Index sizes
            index_sizes_query = text("""
                SELECT 
                    indexname,
                    tablename,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
                LIMIT 10
            """)
            
            result = session.execute(index_sizes_query)
            index_sizes = [dict(row._mapping) for row in result]
            
            return {
                "database_size": db_size,
                "table_sizes": table_sizes,
                "largest_indexes": index_sizes
            }
            
        except Exception as e:
            logger.error(f"Error getting database size info: {e}")
            return {"error": str(e)}

async def run_database_optimization():
    """Run comprehensive database optimization"""
    async with get_db_session() as session:
        optimizer = DatabaseOptimizer(session.bind)
        
        logger.info("Starting database optimization...")
        
        # Create performance indexes
        index_results = await optimizer.create_performance_indexes(session)
        logger.info(f"Index creation results: {index_results}")
        
        # Optimize tables
        optimization_results = await optimizer.optimize_tables(session)
        logger.info(f"Table optimization results: {optimization_results}")
        
        # Analyze performance
        performance_analysis = await optimizer.analyze_query_performance(session)
        logger.info("Database optimization completed")
        
        return {
            "indexes": index_results,
            "optimization": optimization_results,
            "analysis": performance_analysis
        }